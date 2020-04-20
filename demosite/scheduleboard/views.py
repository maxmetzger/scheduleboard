from django.shortcuts import render
from django.utils import timezone
import logging
from . import services, forms, models

logger = logging.getLogger(__name__)
"""
This class contains a single view - the view used to display the schedule board.
"""


# Create your views here.
def index(request):
    """
    To display the schedule board, we perform a few simple steps.

    1. Did the user select a station from the drop-down menu? If so, use that station.
    Otherwise, default to South Station.

    2. Get the schedules, routes, and predictions for the station, starting at time now.

    3. Create the station form, with the initial selection corresponding to the station selected during step 1.

    4. Render the template.

    :param request:
    :return:
    """

    station_key = models.STATION_CHOICES[0][0]
    logger.debug(f"POST contents were {request.POST}")
    if request.POST.get('station_selection'):
        station_key = request.POST.get('station_selection')
        logger.debug(f"User selected {station_key}")

    min_time = timezone.localtime()
    schedule, routes, predictions = services.get_schedules_routes_and_predictions(min_time, station_key)

    logger.debug(f"Calling template with {len(schedule)} schedules, {len(routes)} routes and {len(predictions)} predictions")

    template_name = 'scheduleboard/index.html'

    station_form = forms.StationForm(initial={'station_selection': station_key})
    logger.debug(f"station form is: {type(station_form)}")
    station_display_name = models.get_station_display_name(station_key)

    return render(request, template_name, {
        'schedule': schedule,
        'routes': routes,
        'predictions': predictions,
        'current_datetime': timezone.localtime(),
        'station_form': station_form,
        'station_display_name': station_display_name
    })
