import json
import random

from shapely.geometry import Polygon, Point


def sectra_polygon_to_shapely(data_polygon):
    return Polygon([(pt["x"], pt["y"]) for pt in data_polygon["points"]])


def random_point_in_polygon(poly):
    minx, miny, maxx, maxy = poly.bounds
    while True:
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if poly.contains(p):
            return p
