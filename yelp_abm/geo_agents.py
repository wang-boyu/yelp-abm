import random
from enum import Enum

import mesa
import mesa_geo as mg
import pyproj
from shapely.geometry import Point


class RestaurantAgent(mg.GeoAgent):
    unique_id: int
    model: mesa.Model
    geometry: Point
    crs: pyproj.CRS

    name: str
    rvw_cnt: int
    avg_str: float
    avg_fod: float
    avg_mbn: float
    avg_prc: float
    avg_srv: float

    capacity: int
    num_customers: int = 0
    visiting_history: list[int]

    def __init__(self, unique_id, model, geometry, crs) -> None:
        super().__init__(unique_id, model, geometry, crs)
        self.visiting_history = []

    @property
    def is_full(self):
        return self.num_customers >= self.capacity

    def add_customer(self):
        self.num_customers += 1

    def step(self):
        self.num_customers = 0


CensusTractAgent = mg.GeoAgent


class ConsumerType(Enum):
    STUDENT = "STUDENT"
    MID_AGE = "MID_AGE"
    SENIOR = "SENIOR"


CONSUMER_PREFERENCES = {
    ConsumerType.STUDENT: lambda x: (x.avg_prc, x.avg_fod, x.avg_mbn, x.avg_srv),
    ConsumerType.MID_AGE: lambda x: (x.avg_fod, x.avg_prc, x.avg_mbn, x.avg_srv),
    ConsumerType.SENIOR: lambda x: (x.avg_mbn, x.avg_srv, x.avg_fod, x.avg_prc),
}


class ConsumerAgent(mg.GeoAgent):
    unique_id: int
    model: mesa.Model
    geometry: Point
    crs: pyproj.CRS

    type: ConsumerType
    restaurant_candidates: list[RestaurantAgent]
    choice_strategy: str

    def __init__(
        self,
        unique_id,
        model,
        geometry,
        crs,
        consumer_type: ConsumerType,
        choice_strategy: str,
    ) -> None:
        super().__init__(unique_id, model, geometry, crs)
        self.type = consumer_type
        self.choice_strategy = choice_strategy

    def step(self):
        available_restaurants = [r for r in self.restaurant_candidates if not r.is_full]
        if available_restaurants:
            if self.choice_strategy == "random":
                restaurant = random.choice(available_restaurants)
            elif self.choice_strategy == "best":
                restaurant = max(
                    available_restaurants,
                    key=CONSUMER_PREFERENCES[self.type],
                )
            else:
                raise ValueError(
                    f"Invalid choice strategy: {self.choice_strategy}. Choose from 'random' or 'best'."
                )
            restaurant.add_customer()
