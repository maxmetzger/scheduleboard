from django.utils import timezone
from datetime import datetime, timedelta
import logging
import requests
import operator
from .models import Schedule, Prediction, Route

logger = logging.getLogger(__name__)

mbta_datetime_format = "%Y-%m-%dT%H:%M:%S%z"

def create_schedule(json, routes, predictions):

    schedules = []

    for element in json:
        assert (element["type"] == "schedule")
        arrival_time = element["attributes"]["arrival_time"]
        if arrival_time:
            arrival_time = datetime.strptime(arrival_time, mbta_datetime_format)
        departure_time = element["attributes"]["departure_time"]
        if departure_time:
            departure_time = datetime.strptime(departure_time, mbta_datetime_format)
        direction = element["attributes"]["direction_id"]
        route_id = element["relationships"]["route"]["data"]["id"]
        trip_id = element["relationships"]["trip"]["data"]["id"]
        stop_id = element["relationships"]["stop"]["data"]["id"]

        route = routes[route_id]
        prediction = None
        if element["relationships"]["prediction"]["data"]:
            prediction_id = element["relationships"]["prediction"]["data"]["id"]
            prediction = predictions[prediction_id]
        sid = element["id"]
        schedule = Schedule(sid, arrival_time, departure_time, direction, route, trip_id, stop_id, prediction)
        schedules.append(schedule)

    schedules.sort(key=lambda x: x.get_scheduled_time())
    return schedules


def create_route(json):
    assert (json["type"] == "route")
    rid = json["id"]
    c = json["attributes"]["color"]
    tc = json["attributes"]["text_color"]
    sn = json["attributes"]["short_name"]
    ln = json["attributes"]["long_name"]
    dd = json["attributes"]["direction_destinations"]
    dn = json["attributes"]["direction_names"]
    rt = json["attributes"]["type"]
    return Route(rid, c, tc, sn, ln, dd, dn, rt)


def create_prediction(json):
    """
    Creates a single Prediction object from a json dictionary
    :param json: a single json dictionary element where type="prediction"
    :return:
    """
    assert(json["type"] == "prediction")
    pid = json["id"]
    at = json["attributes"]["arrival_time"]
    if at:
        at = datetime.strptime(at, mbta_datetime_format)
    dt = json["attributes"]["departure_time"]
    if dt:
        dt = datetime.strptime(dt, mbta_datetime_format)
    di = json["attributes"]["direction_id"]
    s = json["attributes"]["status"]
    return Prediction(pid, at, dt, di, s)


def parse_included(included):
    """
    creates a tuple of routes and predictions from a json list
    :param included: a list of json dictionaries
    :return: a tuple of routes (a dictionary of route_id->Route), predictions (a dictionary of prediction_id->Prediction)
    """
    routes = {}
    predictions = {}
    for element in included:
        if element["type"] == "route":
            route = create_route(element)
            routes[route.id] = route
        elif element["type"] == "prediction":
            prediction = create_prediction(element)
            predictions[prediction.id] = prediction
    return routes, predictions


def get_schedules_routes_and_predictions(min_time, station_name):
    """
    Gets the schedules and included predictions (if any) for the next six hours
    :param min_time: the min_time filter to use (refer to mbta api documentation)
    :return: a tuple of Schedules (list), Routes (dictionary by ID), and Predictions (dictionary by ID)
    """
# https://api-v3.mbta.com/schedules?include=prediction&filter[min_time]=14%3A00&filter[max_time]=14%3A30&filter[stop]=place-sstat
    hours_to_get = 6
    current_time = min_time.strftime("%H:%M")
    current_date = min_time.strftime("%Y-%m-%d")

    max_time = str(min_time.hour + hours_to_get).zfill(2)+min_time.strftime(":%M")
    logger.debug(f"Using filter[date]: {current_date}, filter[min_time]: {current_time}, filter[max_time]: {max_time}")
    logger.debug(f"Current time: {current_time}")
    logger.debug(f"Current date: {current_date}")
    payload = {
        'filter[stop]': station_name,
        'filter[min_time]': current_time,
        'filter[max_time]': max_time,
        'filter[date]': current_date,
        'sort': 'arrival_time',
        'include': 'prediction,trip,route'}
    response = requests.get('https://api-v3.mbta.com/schedules', params=payload)
    logger.debug(f"Response was {response}")

    included = response.json()['included']
    logger.debug(f"There were {len(included)} included")
    routes, predictions = parse_included(included)
    logger.debug(f"Now there are {len(routes)} routes and {len(predictions)} predictions")

    data = response.json()['data']
    logger.debug(f"There were {len(data)} data ")
    schedule = create_schedule(data, routes, predictions)
    logger.debug(f"Now there are {len(schedule)} schedules")

    return schedule, routes, predictions
