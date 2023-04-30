import random
from uuid import uuid4

import pandas as pd
import geopandas as gpd
import mesa
import mesa_geo as mg
from tqdm import tqdm

from .geo_agents import RestaurantAgent, ConsumerAgent, ConsumerType, CensusTractAgent
from .utils import random_points_in_polygon


class YelpOpinionDynamicsModel(mesa.Model):
    def __init__(
        self,
        restaurant_file: str,
        consumer_file: str,
        model_crs: str = "ESRI:102696",
        restaurant_search_radius_feet: int = 70000,
        export_data: bool = False,
        max_steps: int = 100,
    ):
        super().__init__()
        self.export_data = export_data
        self.max_steps = max_steps
        self.restaurant_file = restaurant_file
        self.consumer_file = consumer_file
        self.restaurant_search_radius_feet = restaurant_search_radius_feet
        self.restaurant_schedule = mesa.time.RandomActivation(self)
        self.agent_schedule = mesa.time.RandomActivation(self)
        self.space = mg.GeoSpace(crs=model_crs)
        self._create_restaurants()
        self._create_consumers()

    def _create_restaurants(self):
        restaurants_df = gpd.read_file(self.restaurant_file).to_crs(self.space.crs)
        restaurants_creator = mg.AgentCreator(RestaurantAgent, model=self)
        restaurant_agents = restaurants_creator.from_GeoDataFrame(
            restaurants_df, unique_id="bsnss_d"
        )
        self.space.add_agents(restaurant_agents)

        for restaurant in restaurant_agents:
            # TODO: set capacity based on restaurant checkin data
            restaurant.capacity = random.randint(1, 10)
            self.restaurant_schedule.add(restaurant)

    def _create_consumers(self):
        census_tracts_df = gpd.read_file(self.consumer_file).to_crs(self.space.crs)
        # filter to keep only census tracts in St. Louis, MO
        census_tracts_df = census_tracts_df.loc[
            census_tracts_df["cnss_tr"].str.startswith("29")
        ]
        # filter to keep only census tracts with at least 1 restaurant
        # census_tracts_df = census_tracts_df.sjoin(restaurants_df, how="inner", op="contains")

        census_tracts_creator = mg.AgentCreator(CensusTractAgent, model=self)
        census_tract_agents = census_tracts_creator.from_GeoDataFrame(
            census_tracts_df, unique_id="cnss_tr"
        )
        self.space.add_agents(census_tract_agents)

        # 1 student, 1 mid-age, 1 senior per census tract
        for census_tract in tqdm(
            census_tract_agents, desc="Creating consumers in census tracts"
        ):
            student = ConsumerAgent(
                uuid4().int, self, None, self.space.crs, ConsumerType.STUDENT
            )
            mid_age = ConsumerAgent(
                uuid4().int, self, None, self.space.crs, ConsumerType.MID_AGE
            )
            senior = ConsumerAgent(
                uuid4().int, self, None, self.space.crs, ConsumerType.SENIOR
            )

            points = random_points_in_polygon(census_tract.geometry, 3)
            student.geometry = points[0]
            mid_age.geometry = points[1]
            senior.geometry = points[2]

            for consumer in student, mid_age, senior:
                neighbors = self.space.get_neighbors_within_distance(
                    consumer, self.restaurant_search_radius_feet
                )
                consumer.restaurant_candidates = [
                    r for r in neighbors if isinstance(r, RestaurantAgent)
                ]
                self.space.add_agents(consumer)
                self.agent_schedule.add(consumer)

    def _remove_consumers(self):
        consumers = [a for a in self.space.agents if isinstance(a, ConsumerAgent)]
        for consumer in consumers:
            self.space.remove_agent(consumer)
            self.agent_schedule.remove(consumer)

    def export_visiting_history_to_parquet(self, filename: str) -> None:
        gdf = self.space.get_agents_as_GeoDataFrame(agent_cls=RestaurantAgent)
        df = pd.DataFrame(gdf.drop(columns=["geometry"]))
        df.to_parquet(filename)
        print(f"Exported visiting history to {filename}.")

    def step(self):
        self._remove_consumers()
        self._create_consumers()
        self.restaurant_schedule.step()
        self.reset_randomizer(seed=random.randint(0, 1000000))
        self.agent_schedule.step()
        for restaurant in self.restaurant_schedule.agents:
            restaurant.visiting_history.append(restaurant.num_customers)
        self.running = self.restaurant_schedule.steps < self.max_steps
        if not self.running and self.export_data:
            self.export_visiting_history_to_parquet(
                "data/processed/abm_visiting_history.parquet"
            )
