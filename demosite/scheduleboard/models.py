from django.db import models


# Create your models here.

"""
A simple enumeration of stations that the user can switch between.
"""
STATION_CHOICES = (
    ('place-sstat', 'South Station'),
    ('place-north', 'North Station')
)


def get_station_display_name(station_key):
    for station in STATION_CHOICES:
        if station[0] == station_key:
            return station[1]
    else:
        return None


class Schedule:
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
        if self.departure_time:
            return self.departure_time
        else:
            return self.arrival_time

    def get_status(self):
        if self.prediction:
            return self.prediction.get_status()
        else:
            return ""

    def get_destination(self):
        return self.route.get_destination(self.direction_id)


class Route:
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
        return self.dir_destinations[dir_id]

    def get_name(self):
        if self.short_name:
            return self.short_name
        else:
            return self.long_name


class Prediction:
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
        if self.arrival_time:
            return self.arrival_time
        else:
            return self.departure_time

    def get_status(self):
        if self.status and self.status != "None":
            return self.status
        else:
            return ""
