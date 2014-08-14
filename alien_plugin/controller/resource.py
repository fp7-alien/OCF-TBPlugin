

from alien_plugin.models.AlienResource import AlienResource as AlienResourceModel
import decimal, random
from alien_plugin.log.log import *

class AlienResource():
    """
    Manages creation/edition of AlienResources from the input of a given form.
    """
    
    @staticmethod
    def create(instance, aggregate_id, slice=None):
        try:
            sr = AlienResourceModel()

            sr.aggregate_id = aggregate_id

            sr.set_dpid(instance.__dict__['name'])

            sr.set_name(instance.__dict__['name'])

            sr.set_project_id(0)
            sr.set_slice_id(0)
            #if slice:
            #    sr.set_project_id(slice.project.id)
            #    sr.set_project_name(slice.project.name)
            #    sr.set_slice_id(slice.id)
            #    sr.set_slice_name(slice.name)
            sr.save()

        except Exception as e:
            writeToLog("Exception %s" %str(e))
            if "Duplicate entry" in str(e):
                raise Exception("AlienResource with name '%s' already exists." % str(instance.name))
            else:
                raise e

    @staticmethod
    def fill(instance, slice, aggregate_id, resource_id = None):
        # resource_id = False => create. Check that no other resource exists with this name
        if not resource_id:
            if AlienResourceModel.objects.filter(name = instance.name):
                # Every exception will be risen to the upper level
                raise Exception("AlienResource with name '%s' already exists." % str(instance.name))

            instance.aggregate_id = aggregate_id
            #instance.project_id = slice.project.id
            #instance.project_name = slice.project.name
            #instance.slice_id = slice.id
            #instance.slice_name = slice.name
        # resource_id = True => edit. Change name/label
        instance.dpid = instance.name
        return instance

    @staticmethod
    def delete(resource_id):
        try:
            AlienResourceModel.objects.get(id = resource_id).delete()
        except:
            pass

