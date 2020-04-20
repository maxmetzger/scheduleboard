from django.db import models


# Create your models here.
"""
The models included in this file are not managed by Django; for a simple demo app we don't need to cache anything in
our own database. For a larger site with many users, we would want to cache our Schedule, Route, and Prediction objects
to keep from hitting the MBTA API too frequently. 
"""

#A simple enumeration of stations that the user can switch between. This can easily be extended if you know the station IDs you want to add, just add more (station_id, station_name) pairs.

STATION_CHOICES = (
    ('place-sstat', 'South Station'),
    ('place-north', 'North Station')
)


def get_station_display_name(station_key):
    """
    Given a station_key, find the corresponding station_name from STATION_CHOICES
    :param station_key: a key, taken from STATION_CHOICES
    :return: the corresponding station name, or None if station_key is not in STATION_CHOICES
    """
    for station in STATION_CHOICES:
        if station[0] == station_key:
            return station[1]
    else:
        return None


class Schedule:
    """
    A class that wraps the MBTA Schedule returned from https://api-v3.mbta.com/schedules.
    Only fields relevant to the schedule board are stored in this class.
    See https://api-v3.mbta.com/docs/swagger/index.html#/Schedule for more information.
    """
    managed = False #technically not needed as this class does not extend models.Model, included for clarity
    id = 0
    arrival_time = None
    departure_time = None
    direction_id = None
    route = None
    trip_id = None
    stop_id = None
    prediction = None

    def __init__(self, sid, at, dt, dir, rt, tp, sp, pr):
        """
        Creates a new Schedule object
        :param sid: the schedule ID
        :param at: arrival time
        :param dt: departure time
        :param dir: direction ID
        :param rt: route id
        :param tp: trip id
        :param sp: stop id
        :param pr: prediction id
        """
        self.id = sid
        if at:
            self.arrival_time = at
        if dt:
            self.departure_time = dt
        self.direction_id = dir
        self.route = rt
        self.stop_id = sp
        if pr:
            self.prediction = pr

    def __str__(self):
        return f"Schedule({self.id}|{self.arrival_time}|{self.departure_time})"

    def get_scheduled_time(self):
        """
        Gets the time to display. https://api-v3.mbta.com/ often returns only one time.
        :return: departure_time if available, otherwise arrival_time.
        """
        if self.departure_time:
            return self.departure_time
        else:
            return self.arrival_time

    def get_status(self):
        """
        Convenience method to get the status from a prediction, if a prediction exists for this object.
        :return: The prediction's status if available, otherwise an empty string.
        """
        if self.prediction:
            return self.prediction.get_status()
        else:
            return ""

    def get_destination(self):
        """
        Convenience method to get the destination from a route.
        :return: the route's final destination.
        """
        return self.route.get_destination(self.direction_id)


class Route:
    """
    A class that wraps the MBTA route, see https://api-v3.mbta.com/docs/swagger/index.html#/Route for more information.
    Only fields relevant to the schedule board are stored within this class.
    """
    managed = False
    id = None
    color = None
    text_color = None
    short_name = None
    long_name = None
    dir_destinations = None
    dir_names = None
    route_type = None

    def __init__(self, rid, c, tc, sn, ln, dd, dn, rt):
        """
        Creates a new route object
        :param rid: the route id
        :param c: the color for the route
        :param tc: the color for text on the route
        :param sn: the short name of the route
        :param ln: the long name of the route
        :param dd: a map of direction IDs to destination strings (e.g., Braintree)
        :param dn: a map of direction IDs to direction names (e.g., North)
        :param rt: route type (see https://github.com/google/transit/blob/master/gtfs/spec/en/reference.md#routestxt)
        """
        self.id = rid
        self.color = c
        self.text_color = tc
        self.short_name = sn
        self.long_name = ln
        self.dir_destinations = dd
        self.dir_names = dn
        self.route_type = rt

    def get_destination(self, dir_id):
        """
        Gets the corresponding destination name for a given direction id.
        :param dir_id: The direction id, typically found within a Schedule.
        :return: the corresponding destination string for the given direction id
        """
        return self.dir_destinations[dir_id]

    def get_name(self):
        """
        Returns a display name for this route. Not all routes have short and long names (such as the Red Line.)
        :return: defaults to the short_name if present, otherwise the long_name is returned.
        """
        if self.short_name:
            return self.short_name
        else:
            return self.long_name


class Prediction:
    """
    A class that wraps a prediction from the MBTA APi.
    See https://api-v3.mbta.com/docs/swagger/index.html#/Prediction for more information.
    """
    managed = False
    id = None
    arrival_time = None
    departure_time = None
    direction_id = None
    status = None

    def __init__(self, pid, at, dt, di, s):
        self.id = pid
        if at:
            self.arrival_time = at
        if dt:
            self.departure_time = dt
        self.direction_id = di
        if s:
            self.status = s

    def get_display_time(self):
        """
        Gets the appropriate time to display. See https://www.mbta.com/developers/v3-api/best-practices for more information.
        :return: arrival_time if present, otherwise departure_time
        """
        if self.arrival_time:
            return self.arrival_time
        else:
            return self.departure_time

    def get_status(self):
        if self.status and self.status != "None":
            return self.status
        else:
            return ""
