
from django.views.generic import simple
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from expedient.clearinghouse.aggregate.models import Aggregate
from expedient.clearinghouse.slice.models import Slice
from expedient.common.messaging.models import DatedMessage
from expedient.common.utils.plugins.plugincommunicator import *
from expedient.common.utils.plugins.resources.link import Link
from expedient.common.utils.plugins.resources.node import Node
from expedient.common.utils.views import generic_crud
from alien_plugin.controller.resource import AlienResource as AlienResourceController
from alien_plugin.forms.AlienResource import AlienResource as AlienResourceModelForm
from alien_plugin.models import AlienResource as AlienResourceModel,\
    AlienResourceAggregate as AlienResourceAggregateModel
from alien_plugin.log.log import *
from alien_plugin.models import AlienSliceInfo
from alien_plugin.models.AlienSliceInfo import *
from alien_plugin.calender.reserveCalender import *
from alien_plugin.calender.reserveCalender import ResourceCalendar
from alien_plugin.controller.AggregateReservation import AggregateReservation as AggregateReservationController
from alien_plugin.controller.aggregate import *

import copy
import logging
import xmlrpclib
from datetime import date, datetime, timedelta
import calendar
from calendar import monthrange
import os.path


def create_resource(request, slice_id, agg_id):
    """Show a page that allows user to add a AlienResource to the aggregate."""

    if request.method == "POST":
        # Shows error message when aggregate unreachable, disable AlienResource creation and get back to slice detail page
        agg = Aggregate.objects.get(id = agg_id)
        if agg.check_status() == False:
            DatedMessage.objects.post_message_to_user(
                "AlienResource Aggregate '%s' is not available" % agg.name,
                request.user, msg_type=DatedMessage.TYPE_ERROR,)
            return HttpResponseRedirect(reverse("slice_detail", args=[slice_id]))

        if 'create_resource' in request.POST:
            return HttpResponseRedirect(reverse("alien_plugin_resource_crud", args=[slice_id, agg_id]))
        else:
            return HttpResponseRedirect(reverse("slice_detail", args=[slice_id]))

def resource_crud(request, slice_id, agg_id, resource_id = None):
    """
    Show a page that allows user to create/edit AlienResource's to the Aggregate.
    """
    slice = get_object_or_404(Slice, id = slice_id)
    aggregate = Aggregate.objects.get(id = agg_id)
    error_crud = ""

    def pre_save(instance, created):
        """
        Fills AlienResource instance prior to its saving.
        Used within the scope of the generic_crud method.
        """
        instance = AlienResourceController.fill(instance, slice, agg_id, resource_id)

    try:
        return generic_crud(request, obj_id=resource_id, model=AlienResourceModel,
                 form_class=AlienResourceModelForm,
                 template="alien_plugin_resource_crud.html",
                 redirect=lambda inst: reverse("slice_detail", args=[slice_id]),
                 extra_context={"agg": aggregate, "slice": slice, "exception": error_crud, "breadcrumbs": (
                 ("Home", reverse("home")),
                 ("Project %s" % slice.project.name, reverse("project_detail", args=[slice.project.id])),
                 ("Slice %s" % slice.name, reverse("slice_detail", args=[slice_id])),
                 ("%s AlienResource" % "Update" if resource_id else "Create", reverse("alien_plugin_resource_crud", args=[slice_id, agg_id])),)
                 }, extra_form_params={}, template_object_name="object", pre_save=pre_save,
                 post_save=None, success_msg=None)
    except ValidationError as e:
        # Django exception message handling is different to Python's...
        error_crud = ";".join(e.messages)
    except Exception as e:
        print "[WARNING] Could not create resource in plugin 'alien_plugin'. Details: %s" % str(e)
        DatedMessage.objects.post_message_to_user(
            "AlienResource might have been created, but some problem ocurred: %s" % str(e),
            request.user, msg_type=DatedMessage.TYPE_ERROR)
        return HttpResponseRedirect(reverse("slice_detail", args=[slice_id]))

def manage_resource(request, resource_id, action_type):
    """
    Manages the actions executed over AlienResource's.
    """
    if action_type == "delete":
        AlienResourceController.delete(resource_id)
    # Go to manage resources again
    return HttpResponse("")

###
# Topology to show in the Expedient
#

def get_sr_list(slice):
    #return AlienResourceModel.objects.filter(slice_id = slice.uuid)
    return AlienResourceModel.objects.all()

def get_sr_aggregates(slice):
    sr_aggs = []
    try:
        sr_aggs = slice.aggregates.filter(leaf_name=AlienResourceAggregateModel.__name__.lower())
    except:
        pass
    return sr_aggs

def get_node_description(node):
    description = "<strong>Alien Resource: " + node.name + "</strong><br/><br/>"

    connections = ""
    node_connections = node.get_connections()
    for i, connection in enumerate(node_connections):
        connections += connection.name
        if i < len(node_connections)-1:
            connections += ", "
    description += "<br/>&#149; Connected to: %s" % str(connections)
    return description

def get_nodes_links(slice, chosen_group=None):
    nodes = []
    links = []
    sr_aggs = get_sr_aggregates(slice)

    # Getting image for the nodes
    # FIXME: avoid to ask the user for the complete name of the method here! he should NOT know it
    try:
        image_url = reverse('img_media_alien_plugin', args=("alien_img.png",))
    except:
        image_url = 'alien_img.png'

    # For every AlienResource AM
    for i, sr_agg in enumerate(sr_aggs):


        devices=AlienResourceModel.objects.filter(
            aggregate=sr_agg,
            )


        for sr in devices:
            nodes.append(Node(
                # Users shall not be left the choice to choose group/island; otherwise collision may arise
                name = sr.name, value = sr.id, aggregate = sr.aggregate, type = "Alien resource",
                description = get_node_description(sr), image = image_url)
            )
            for connection in sr.get_connections():
                # Two-ways link
                links.append(
                    Link(
                        target = str(sr.id), source = str(connection.id),
                        value = "rsc_id_%s-rsc_id_%s" % (connection.id, sr.id)
                        ),
                )
                links.append(
                    Link(
                        target = str(sr.id), source = str(connection.id),
                        value = "rsc_id_%s-rsc_id_%s" % (sr.id, connection.id)
                        ),
                )
    return [nodes, links]

#from expedient.common.utils.plugins.plugininterface import PluginInterface
#
#class Plugin(PluginInterface):
#    @staticmethod
def get_start_date(slice):
    try:
        start_date = AlienSliceInfo.objects.get(slice=slice).start_date
    except:
        start_date= "Not set"
    return start_date

def get_end_date(slice):
    try:
        end_date = AlienSliceInfo.objects.get(slice=slice).end_date
    except:
        end_date= "Not set"
    return end_date

def get_controller_url(slice):
    try:
        controller_url = AlienSliceInfo.objects.get(slice=slice).controller_url
    except:
        controller_url= "Not set"
    return controller_url

def get_vlan_id(slice):
    try:
        vlan_id = AlienSliceInfo.objects.get(slice=slice).alien_vlan
    except:
        vlan_id= "Not set"
    return vlan_id

def get_status(slice):
    try:
        status = AlienSliceInfo.objects.get(slice=slice).slice_status
        if status=="":
            status="Not Allocated"
    except:
        status= "Not Allocated"
    return status

def book_time_slot(request, agg_id, slice_id, year, month):
    slice = get_object_or_404(Slice, id=slice_id)
    try:
        slice_info=AlienSliceInfo.objects.get(slice=slice)
    except Exception as e:
        try:
            sr = AlienSliceInfo()
            sr.slice=slice
            sr.save()
        except Exception as e2:
            writeToLog("Exception %s" %str(e2))


    start_date=request.POST.get("start_date")
    end_date=request.POST.get("end_date")

    start_error=None
    end_error=None

    if start_date!=None:
        try:
            slice_info.start_date=start_date
            slice_info.save()
            start_error="no error"

        except Exception as e:
            writeToLog(" start date validation error %s" %str(e))
            start_error="error"

    if end_date!=None:
        try:
            slice_info.end_date=end_date
            slice_info.save()
            end_error="no error"

        except Exception as e:
            writeToLog(" end date validation error %s" %str(e))
            end_error="error"

    # Next section is used to display the calender for showing current aggregate reservation
    try:

        if year=='0':
            pYear=datetime.now().year
            pMonth=datetime.now().month
        else:
            pYear=year
            pMonth=month

        #writeToLog("year: %s" %str(pYear))
        #writeToLog("month: %s" %str(pMonth))
        lYear = int(pYear)
        lMonth = int(pMonth)
        #writeToLog("year: %s" %str(lYear))
        lCalendarFromMonth = datetime(lYear, lMonth, 1)
        lCalendarToMonth = datetime(lYear, lMonth, monthrange(lYear, lMonth)[1])

        reservedDays=get_days_allocated_in_Month(agg_id,lYear,lMonth)
        #writeToLog("reserved days: %s"%str(reservedDays))
        lCalendar = ResourceCalendar().formatmonth2(lYear, lMonth,reservedDays)

        #lCalendar=None
        lPreviousYear = lYear
        lPreviousMonth = lMonth - 1
        if lPreviousMonth == 0:
            lPreviousMonth = 12
            lPreviousYear = lYear - 1
        lNextYear = lYear
        lNextMonth = lMonth + 1
        if lNextMonth == 13:
            lNextMonth = 1
            lNextYear = lYear + 1
        lYearAfterThis = lYear + 1
        lYearBeforeThis = lYear - 1
        cal=mark_safe(lCalendar)

        monthName=named_month(lMonth)
        previousMonthName=named_month(lPreviousMonth)
        nextMonthName=named_month(lNextMonth)

    except Exception as e:
        writeToLog("Exception %s" %str(e))


    if start_error!="no error" or end_error!="no error":
        return simple.direct_to_template(
            request,
            template="alien_plugin_book_time_slot.html",
            extra_context={
                "agg_id": agg_id,
                "slice_id": slice_id,
                "year": year,
                "month": month,
                "start_error": start_error,
                "end_error": end_error,
                "Calendar":cal,
                "Month":lMonth,
                "MonthName":monthName,
                "Year":lYear,
                "PreviousMonth":lPreviousMonth,
                "PreviousMonthName":previousMonthName,
                "PreviousYear":lPreviousYear,
                "NextMonth":lNextMonth,
                "NextMonthName":nextMonthName,
                "NextYear":lNextYear,
                "breadcrumbs": (
                    ('Home', reverse("home")),
                    ("Slice %s" % slice.name, reverse("slice_detail", args=[slice_id])),
                    ("Set Time Slot",
                     request.path),
                    )
                },
            )
    else:
        return HttpResponseRedirect(reverse("slice_detail", args=[slice_id]))

def add_controller_to_slice(request, agg_id, slice_id):
    slice = get_object_or_404(Slice, id=slice_id)
    try:
        slice_info=AlienSliceInfo.objects.get(slice=slice)
    except Exception as e:
        try:
            sr = AlienSliceInfo()
            sr.slice=slice
            sr.save()
        except Exception as e2:
            writeToLog("Exception %s" %str(e2))


    #if request.method == "POST":
    url=request.POST.get("controller_url")
    writeToLog("controller url is %s" %str(url))
    controller_error=None

    if url!=None:
        try:
            validate_controller_url(url)
            controller_error="no error"
            slice_info.controller_url=url
            slice_info.save()
            DatedMessage.objects.post_message_to_user(
                        "Successfully set controller for slice %s" % slice.name,
                        request.user, msg_type=DatedMessage.TYPE_SUCCESS,
                    )

        except Exception as e:
            writeToLog(" controller validation error %s" %str(e))
            controller_error="error"

    if controller_error!="no error":
        return simple.direct_to_template(
            request,
            template="alien_plugin_add_controller.html",
            extra_context={
                "agg_id": agg_id,
                "slice_id": slice_id,
                "controller_error": controller_error,
                "breadcrumbs": (
                    ('Home', reverse("home")),
                    ("Slice %s" % slice.name, reverse("slice_detail", args=[slice_id])),
                    ("Set Alien Controller",
                     request.path),
                    )
                },
            )
    else:
        return HttpResponseRedirect(reverse("slice_detail", args=[slice_id]))


def add_vlan_to_slice(request, agg_id, slice_id):
    slice = get_object_or_404(Slice, id=slice_id)
    try:
        slice_info=AlienSliceInfo.objects.get(slice=slice)
    except Exception as e:
        try:
            sr = AlienSliceInfo()
            sr.slice=slice
            sr.save()
        except Exception as e2:
            writeToLog("Exception %s" %str(e2))


    #if request.method == "POST":
    vlan=request.POST.get("vlan_id")
    writeToLog("vlan id is %s" %str(vlan))
    vlan_error=None

    if vlan!=None:
        try:
            validate_vlan_id(vlan)
            vlan_error="no error"
            slice_info.alien_vlan=vlan
            slice_info.save()
            DatedMessage.objects.post_message_to_user(
                        "Successfully set VLAN ID for slice %s" % slice.name,
                        request.user, msg_type=DatedMessage.TYPE_SUCCESS,
                    )

        except Exception as e:
            writeToLog(" vlan validation error %s" %str(e))
            vlan_error="error"

    if vlan_error!="no error":
        return simple.direct_to_template(
            request,
            template="alien_plugin_add_vlan.html",
            extra_context={
                "agg_id": agg_id,
                "slice_id": slice_id,
                "vlan_error": vlan_error,
                "breadcrumbs": (
                    ('Home', reverse("home")),
                    ("Slice %s" % slice.name, reverse("slice_detail", args=[slice_id])),
                    ("Set Alien VLAN",
                     request.path),
                    )
                },
            )
    else:
        return HttpResponseRedirect(reverse("slice_detail", args=[slice_id]))

def calender(request, slice_id, pYear, pMonth):
    """
    Show calendar of events for specified month and year
    """
    try:
        writeToLog("year: %s" %str(pYear))
        writeToLog("month: %s" %str(pMonth))


    except Exception as e:
        writeToLog("Exception: %s" %str(e))

    return HttpResponseRedirect(reverse("slice_detail", args=[slice_id]))

def get_ui_data(slice):
    """
    Hook method. Use this very same name so Expedient can get the resources for every plugin.
    """
    try:
        slice_info=AlienSliceInfo.objects.get(slice=slice)
    except Exception as e:
        try:
            sr = AlienSliceInfo()
            sr.slice=slice
            sr.save()
        except Exception as e2:
            writeToLog("Exception %s" %str(e2))

    ui_context = dict()
    try:
        ui_context['start_date'] = get_start_date(slice)
        ui_context['end_date'] = get_end_date(slice)
        ui_context['alien_controller_url'] = get_controller_url(slice)
        ui_context['alien_vlan_id'] = get_vlan_id(slice)
        ui_context['status'] = get_status(slice)
        #ui_context['alien_controller_url'] = 11
        ui_context['sr_list'] = get_sr_list(slice)

        for agg in get_sr_aggregates(slice):

            agg_status=agg.as_leaf_class().check_status()
            if agg_status != agg.available:
                agg.available = agg_status
                agg.save()

        sr_aggs=get_sr_aggregates(slice)
        ui_context['sr_aggs'] = sr_aggs
        # synchronize am resources:

        for i, sr_agg in enumerate(sr_aggs):
            writeToLog(" id %s" %str(sr_agg.id))
            local_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'certs'))

            key_path = os.path.join(local_path, "alice-key.pem") # make sure the CA of the AM is the same which issued this certificate (e.g. copy certificates from omni)
            cert_path = os.path.join(local_path, "alice-cert.pem")

            try:
                alien_agg=AlienResourceAggregateModel.objects.get(id=sr_agg.id)
                client = GENI3Client(alien_agg.get_client_IP(), alien_agg.get_client_port(), key_path, cert_path)
                sync_am_resources(sr_agg.id, client)
            except Exception as e:
                writeToLog("Exception %s" %str(e))


        ui_context['nodes'], ui_context['links'] = get_nodes_links(slice)
    except Exception as e:
        print "[ERROR] Problem loading UI data for plugin 'alien_plugin'. Details: %s" % str(e)

    return ui_context

def named_month(pMonthNumber):
    """
    Return the name of the month, given the month number
    """
    return date(1900, pMonthNumber, 1).strftime('%B')

def home(request):
    """
    Show calendar of events this month
    """
    lToday = datetime.now()
    return calendar(request, lToday.year, lToday.month)

