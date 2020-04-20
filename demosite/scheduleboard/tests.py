from django.test import TestCase
from django.utils import timezone
from . import services
# Create your tests here.

class ServicesTests(TestCase):
    """
    Some simple Django tests to ensure that our services work at various times.
    """
    def test_at_time_now(self):
        """
        A general test to see if the service works at time now
        :return:
        """
        min_time = timezone.localtime()
        schedules, routes, predictions = services.get_schedules_routes_and_predictions(min_time)
        #the last schedule in the list should occur after the first schedule
        self.assertGreaterEqual(schedules[-1].get_scheduled_time(), schedules[0].get_scheduled_time())

    def test_at_midnight(self):
        """
        If called at midnight, we should get results that include tomorrow in the early AM.
        :return:
        """
        min_time = timezone.localtime()
        min_time = min_time.replace(hour=0, minute=0, second=0)
        schedules, routes, predictions = services.get_schedules_routes_and_predictions(min_time)
        # the last schedule in the list should occur after the first schedule
        self.assertGreaterEqual(schedules[-1].get_scheduled_time(), schedules[0].get_scheduled_time())

    def test_close_to_midnight(self):
        """
        If called close to midnight, results should spill over into the next calendar day, as "today's"
        last trains actually run tomorrow morning, around 1AM to 2AM.
        :return:
        """
        min_time = timezone.localtime()
        min_time = min_time.replace(hour=22, minute=0, second=0)
        schedules, routes, predictions = services.get_schedules_routes_and_predictions(min_time)
        # the last schedule in the list should occur after the first schedule
        self.assertGreaterEqual(schedules[-1].get_scheduled_time(), schedules[0].get_scheduled_time())