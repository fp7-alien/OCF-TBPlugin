
from alien_plugin.models.AlienAggregateReservation import AlienAggregateReservation as AlienAggregateReservationModel
import decimal, random
from alien_plugin.log.log import *

class AggregateReservation():
    """
    Manages creation/edition of AlienResources from the input of a given form.
    """
    
    @staticmethod
    def create(aggregate_id, startDate,endDate,sliceUrn):
        try:

            sr = AlienAggregateReservationModel()
            sr.aggregate_id = aggregate_id
            sr.start_date=startDate
            sr.end_date=endDate
            sr.slice_urn=sliceUrn
            sr.save()
        except Exception as e:
            writeToLog("Exception %s" %str(e))
            pass

