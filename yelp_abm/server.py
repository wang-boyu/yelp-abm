"""
Configure visualization elements and instantiate a server
"""

import os

import mesa
import mesa_geo as mg
import xyzservices.providers as xyz
from dotenv import load_dotenv

from .geo_agents import RestaurantAgent, ConsumerAgent, ConsumerType, CensusTractAgent
from .model import YelpOpinionDynamicsModel
from .visualization.HistogramModule import HistogramModule
from .visualization.NewMapVisualization import MapModule


def agent_portrayal(agent):
    portrayal = {}
    if isinstance(agent, RestaurantAgent):
        portrayal = {
            "stroke": False,
            "radius": 3,
            "fillColor": "blue",
            "fillOpacity": 1,
            "description": {
                "Name: ": agent.name,
                "Reviews: ": agent.rvw_cnt,
                "Stars: ": f"{agent.avg_str:.2f}",
                "Food: ": f"{agent.avg_fod:.2f}",
                "Ambience: ": f"{agent.avg_mbn:.2f}",
                "Price: ": f"{agent.avg_prc:.2f}",
                "Service: ": f"{agent.avg_srv:.2f}",
            },
        }
    elif isinstance(agent, ConsumerAgent):
        portrayal = {
            "stroke": False,
            "radius": 2,
            "fillOpacity": 0.7,
            "description": {
                "ID: ": str(agent.unique_id),
                "Type: ": agent.type.value,
            },
        }
        if agent.type == ConsumerType.STUDENT:
            portrayal["fillColor"] = "green"
        elif agent.type == ConsumerType.MID_AGE:
            portrayal["fillColor"] = "red"
        elif agent.type == ConsumerType.SENIOR:
            portrayal["fillColor"] = "orange"
    elif isinstance(agent, CensusTractAgent):
        portrayal = {
            "color": "black",
            "weight": 0.2,
            "fill": False,
        }
    return portrayal


load_dotenv()
map_tile = mg.RasterWebTile.from_xyzservices(
    xyz.MapBox(
        id="mapbox/streets-v12",
        accessToken=os.getenv("MAPBOX_ACCESS_TOKEN"),
    )
)
map_tile.options[
    "attribution"
] = '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

map_element = MapModule(
    agent_portrayal,
    map_height=600,
    map_width=600,
    tiles=map_tile,
)

model_kwargs = {
    "restaurant_file": "data/processed/ch_2_restaurants_st_louis_avg_sentiments.shp",
    "consumer_file": "data/processed/ch_4_population_age_group.shp",
    "num_consumers_per_census_tract": mesa.visualization.Slider(
        "Consumers per census tract", 3, 1, 10, 1
    ),
    "max_steps": mesa.visualization.Slider("Max steps", 100, 1, 100, 1),
    "export_data": mesa.visualization.Checkbox(
        "Export visiting history after simulation", True
    ),
}

histogram = HistogramModule(10, 200, 500)
server = mesa.visualization.ModularServer(
    YelpOpinionDynamicsModel,
    [map_element, histogram],
    "Yelp Opinion Dynamics",
    model_kwargs,
)
