from django.utils import timezone
from datetime import datetime, timedelta
import logging
import requests
import operator
from .models import Schedule, Prediction, Route

"""
This file contains methods to access the MBTA API and create our own representations of the resulting JSON response.
"""

logger = logging.getLogger(__name__)

# This is how the MBTA API currently returns all datetime values.
mbta_datetime_format = "%Y-%m-%dT%H:%M:%S%z"

def fix_UTC_offset(date_string):
    """
    Python 3.6 and lower does not like when a date string has a colon in the UTC offset, such as
    2020-04-20T23:59:59-04:00
    Intead, Pyton 3.6 and lower needs the colon removed:
     2020-04-20T23:59:59-0400

    We can fix this easily by simply removing the colon if it exists.
    (Python 3.7 and later does not have this issue.)

    See https://stackoverflow.com/questions/30999230/how-to-parse-timezone-with-colon for an example.

    :param date_string: a date string of the format "%Y-%m-%dT%H:%M:%S%z"
    :return: No return, the date string is fixed inline
    """
    if ":" == date_string[-3:-2]:
        date_string = date_string[:-3] + date_string[-2:]

def create_schedule(json, routes, predictions):
    """
    This method creates a list of models.Schedule objects, each representing a single schedule entry.
    :param json: the schedule JSON from the MBTA API response. should be a list of JSON dictionaries.
    :param routes: a list of models.Route objects
    :param predictions: a list of models.Prediction objects
    :return: a list of models.Schedule objects, in chronological order (earliest schedule first)
    """
    schedules = []

    for element in json:
        assert (element["type"] == "schedule")  # here we check to ensure we're not parsing the wrong JSON
        arrival_time = element["attributes"]["arrival_time"]
        if arrival_time:
            fix_UTC_offset(arrival_time)
            arrival_time = datetime.strptime(arrival_time, mbta_datetime_format)
        departure_time = element["attributes"]["departure_time"]
        if departure_time:
            fix_UTC_offset(departure_time)
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

    schedules.sort(key=lambda x: x.get_scheduled_time()) # sort the schedules by their scheduled time
    return schedules


def create_route(json):
    """
    creates a single models.Route object from a JSON dictionary
    :param json: a dictionary of JSON key/value pairs.
    :return: a models.Route object
    """
    assert (json["type"] == "route")  # check to ensure this is valid JSON
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
    Creates a single models.Prediction object from a json dictionary
    :param json: a single json dictionary element where type="prediction"
    :return: a models.Prediction object
    """
    assert(json["type"] == "prediction")  # check to ensure this is valid JSON
    pid = json["id"]
    at = json["attributes"]["arrival_time"]
    if at:
        fix_UTC_offset(at)
        at = datetime.strptime(at, mbta_datetime_format)
    dt = json["attributes"]["departure_time"]
    if dt:
        fix_UTC_offset(dt)
        dt = datetime.strptime(dt, mbta_datetime_format)
    di = json["attributes"]["direction_id"]
    s = json["attributes"]["status"]
    return Prediction(pid, at, dt, di, s)


def parse_included(included):
    """
    creates a tuple of routes and predictions from a json list
    :param included: a list of json dictionaries
    :return: a tuple consisting of routes, predictions
    routes is a dictionary of route_id -> models.Route objects;
    predictions is a dictionary of prediction_id->models.Prediction objects
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
    This method calls out the the MBTA API to get schedules, routes, and predictions (when available)
    for a six hour window starting at min_time. Results are always for the current day, although they may span into
    the next day if this is called with a min_time is close to midnight.

    See https://api-v3.mbta.com/docs/swagger/index.html#/Schedule for a description of how filter[min_time] and
    filter[max_time] work, as the behavior may not be intuitive when crossing over midnight into tomorrow morning.

    :param min_time: the min_time filter to use (refer to mbta api documentation).
    min_time should be a HH:MM formatted string in 24 hour time, e.g., "01:00", "00:35", "24:00"
    :param station_name: the station ID as used by the MBTA API.
    See https://api-v3.mbta.com/docs/swagger/index.html#/Stop/ for potential names. Parent names (e.g., "place-north")
    are also supported.
    :return: a tuple of Schedules (list of Model.Schedules),
    Routes (dictionary by ID, models.Route), and Predictions (dictionary by ID, models.Prediction)
    """
# example URL https://api-v3.mbta.com/schedules?include=prediction&filter[min_time]=14%3A00&filter[max_time]=14%3A30&filter[stop]=place-sstat
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
