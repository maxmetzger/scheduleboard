from django.shortcuts import render
from django.utils import timezone
import logging
from . import services, forms, models

logger = logging.getLogger(__name__)


# Create your views here.
def index(request):

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
