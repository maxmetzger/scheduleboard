from django import forms
import logging
from . import models

logger = logging.getLogger(__name__)


class StationForm(forms.Form):
    """
    A simple Django form that creates a drop-down menu of stations, so users can select which station's schedule they want to see.
    """

    station_selection = forms.ChoiceField(choices=models.STATION_CHOICES,
                                          widget=forms.Select(attrs={"onChange": 'submit()'}))
