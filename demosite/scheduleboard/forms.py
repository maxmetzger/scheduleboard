from django import forms
import logging
from . import models

logger = logging.getLogger(__name__)


class StationForm(forms.Form):

    station_selection = forms.ChoiceField(choices=models.STATION_CHOICES,
                                          widget=forms.Select(attrs={"onChange": 'submit()'}))
