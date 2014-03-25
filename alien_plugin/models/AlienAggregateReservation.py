

from django.db import models
from django.core.exceptions import MultipleObjectsReturned
from expedient.clearinghouse.aggregate.models import Aggregate
from expedient.common.permissions.shortcuts import must_have_permission
from alien_plugin.models.AlienResource import AlienResource
from alien_plugin.log.log import *
from expedient.common.messaging.models import DatedMessage
from alien_plugin.models.AlienResourceAggregate import AlienResourceAggregate

# AlienResource Aggregate class
class AlienAggregateReservation(models.Model):
    class Meta:
        """Meta class for AlienResource model."""
        app_label = 'alien_plugin'
    #aggregate = models.ManyToOneField('AlienResourceAggregate', editable = False, blank = False, null = False)
    aggregate = models.ForeignKey(AlienResourceAggregate)
    #aggregate_id=models.IntegerField()
    start_date= models.DateTimeField(
        help_text="start date of reservation")
    end_date= models.DateTimeField(
        help_text="end date of reservation")
    slice_urn= models.CharField(max_length = 1024, default = "")