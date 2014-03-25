
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import simple
from expedient.clearinghouse.utils import post_message_to_current_user
from expedient.common.messaging.models import DatedMessage
from expedient.common.permissions.shortcuts import give_permission_to
from io import BytesIO
from lxml import etree
from alien_plugin.controller.resource import AlienResource as AlienResourceController
from alien_plugin.forms.AlienResourceAggregate import AlienResourceAggregate as AlienResourceAggregateForm
from alien_plugin.forms.xmlrpcServerProxy import xmlrpcServerProxy as xmlrpcServerProxyForm
from alien_plugin.models.AlienResourceAggregate import AlienResourceAggregate as AlienResourceAggregateModel
from alien_plugin.models.AlienResource import AlienResource as AlienResourceModel
from alien_plugin.models.AlienAggregateReservation import AlienAggregateReservation as AlienAggregateReservationModel
from alien_plugin.controller.AggregateReservation import AggregateReservation as AggregateReservationController
from expedient.common.xmlrpc_serverproxy.forms import PasswordXMLRPCServerProxyForm

from alien_plugin.controller.geni_api_three_client import *

from datetime import date, datetime, timedelta

from alien_plugin.log.log import *
import xmlrpclib

import sys
import os.path


from datetime import datetime
from dateutil import parser as dateparser

import threading
import time

class am_resource(object):
    """
    Used to extend any object properties.
    """
    pass

def aggregate_crud(request, agg_id=None):
    '''
    Create/update a AlienResource Aggregate.
    '''

    if agg_id != None:
        aggregate = get_object_or_404(AlienResourceAggregateModel, pk=agg_id)
        client = aggregate.client
    else:
        aggregate = None
        client = None

    extra_context_dict = {}
    errors = ""

    if request.method == "GET":
        agg_form = AlienResourceAggregateForm(instance=aggregate)
        client_form = xmlrpcServerProxyForm(instance=client)
        #client_form = PasswordXMLRPCServerProxyForm(instance=client)
        
    elif request.method == "POST":
        agg_form = AlienResourceAggregateForm(
            data=request.POST, instance=aggregate)
        client_form = xmlrpcServerProxyForm(
            data=request.POST, instance=client)
        '''
        client_form = PasswordXMLRPCServerProxyForm(
            data=request.POST, instance=client)
        '''

        if client_form.is_valid() and agg_form.is_valid():
            # Ping is tried after every field check
            client = client_form.save(commit=False)
            #s = xmlrpclib.Server('https://'+client.username+':'+client.password+'@'+client.url[8:])

            local_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'certs'))

            key_path = os.path.join(local_path, "alice-key.pem") # make sure the CA of the AM is the same which issued this certificate (e.g. copy certificates from omni)
            cert_path = os.path.join(local_path, "alice-cert.pem")
            # instanciate the client

            #client2 = GENI3Client('192.168.61.164', 8001, key_path, cert_path)
            # load test credential (look into the `test/creds/TODO.md` to generate these certs)

            with open(os.path.join(local_path, "alice-cred.xml"), 'r') as f:
                TEST_CREDENTIAL = {'geni_value': f.read(), 'geni_version': '3', 'geni_type': 'geni_sfa'}
            with open(os.path.join(local_path, "pizzaslice_cred.xml"), 'r') as f:
                TEST_SLICE_CREDENTIAL = {'geni_value': f.read(), 'geni_version': '3', 'geni_type': 'geni_sfa'}


            #res=client2.listResources([TEST_CREDENTIAL], True, False)

            #s = xmlrpclib.Server('https://'+client.url[8:])

            try:
                #s.ping('ping')
                client2 = GENI3Client(aggregate.get_client_IP(), aggregate.get_client_port(), key_path, cert_path)
            except Exception as e:
                errors = "Could not connect to server: username, password or url are not correct"
                DatedMessage.objects.post_message_to_user(
                    errors, user=request.user, msg_type=DatedMessage.TYPE_ERROR,
                )
                extra_context_dict['errors'] = errors
                writeToLog("Exception: %s" %str(e))

            if not errors:
                client = client_form.save()
                aggregate = agg_form.save(commit=False)
                aggregate.client = client
                aggregate.save()
                agg_form.save_m2m()
                aggregate.save()
                # Update agg_id to sync its resources
                agg_id = aggregate.pk
                # Get resources from AlienResource AM's xmlrpc server every time the AM is updated

                try:
                    do_sync = True
                    '''
                    if agg_form.is_bound:
                        do_sync = agg_form.data.get("sync_resources")
                    else:
                        do_sync = agg_form.initial.get("sync_resources")
                    '''

                    if do_sync:

                        failed_resources = sync_am_resources(agg_id, client2)

                        if failed_resources:
                            DatedMessage.objects.post_message_to_user(
                                "Could not synchronize resources %s within Expedient" % str(failed_resources),
                                user=request.user, msg_type=DatedMessage.TYPE_WARNING,
                            )
                except:
                    warning = "Could not synchronize AM resources within Expedient"
                    DatedMessage.objects.post_message_to_user(
                        errors, user=request.user, msg_type=DatedMessage.TYPE_WARNING,
                    )
                    extra_context_dict['errors'] = warning

                give_permission_to(
                   "can_use_aggregate",
                   aggregate,
                   request.user,
                   can_delegate=True
                )
                give_permission_to(
                    "can_edit_aggregate",
                    aggregate,
                    request.user,
                    can_delegate=True
                )
                DatedMessage.objects.post_message_to_user(
                    "Successfully created/updated aggregate %s" % aggregate.name,
                    user=request.user, msg_type=DatedMessage.TYPE_SUCCESS,
                )
                return HttpResponseRedirect("/")
    else:
        return HttpResponseNotAllowed("GET", "POST")


    if not errors:
        extra_context_dict['available'] = aggregate.check_status() if agg_id else False

    # Updates the dictionary with the common fields
    extra_context_dict.update({
            "agg_form": agg_form,
            "client_form": client_form,
            "create": not agg_id,
            "aggregate": aggregate,
            "breadcrumbs": (
                ('Home', reverse("home")),
                ("%s AlienResource Aggregate" % ("Update" if agg_id else "Create"),
                 request.path),
            )
        })

    return simple.direct_to_template(
        request,
        template="alien_plugin_aggregate_crud.html",
        extra_context=extra_context_dict
    )

def delete_resources(agg_id):
    resource_set = AlienResourceAggregateModel.objects.get(id = agg_id).resource_set.all()
    for resource in resource_set:
        resource.delete()

def delete_reservations(agg_id):
    try:
        agg = AlienResourceAggregateModel.objects.get(id = agg_id)
        reservation_set = AlienAggregateReservationModel.objects.filter(aggregate = agg)

        for reservation in reservation_set:
            reservation.delete()
    except Exception as e:
        writeToLog("Exception %s" %str(e))

def get_reservations(agg_id):
    try:
        agg = AlienResourceAggregateModel.objects.get(id = agg_id)
        reservation_set = AlienAggregateReservationModel.objects.filter(aggregate = agg)
        return reservation_set
    except Exception as e:
        writeToLog("Exception %s" %str(e))
        return None

def get_reservations_in_Month(agg_id,year,month):
    try:
        agg = AlienResourceAggregateModel.objects.get(id = agg_id)
        reservation_set = AlienAggregateReservationModel.objects.filter(aggregate = agg)
        month_reservation=[]
        for reservation in reservation_set:
            if reservation.start_date.year==year and reservation.start_date.month==month:
                month_reservation.append(reservation)
        return month_reservation
    except Exception as e:
        writeToLog("Exception %s" %str(e))
        return None

def get_days_allocated_in_Month(agg_id,year,month):
    try:
        month_reservation=get_reservations_in_Month(agg_id,year,month)

        days=[]
        for reservation in month_reservation:
            for day in range(1,31):
                try:
                    t = datetime(year, month, day, 14, 00)
                    if reservation.start_date<=t<=reservation.end_date:
                        days.append(day)
                except:
                    pass
                '''
                writeToLog("33333 %s %s %s" %(str(day),str(reservation.start_date.day),str(reservation.end_date.day)))
                if day>=reservation.start_date.day and day<=reservation.end_date.day:
                    days.append(day)
                if day>=reservation.start_date.day and month<reservation.end_date.month:
                    days.append(day)
                '''
        return days

    except Exception as e:
        writeToLog("Exception %s" %str(e))
        return None


def sync_am_resources(agg_id, geni3_Client):
    """
    Retrieves AlienResource objects from the AM's xmlrpc server every time the AM is updated
    """
    connections = dict()
    failed_resources = []

    local_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'certs'))

    with open(os.path.join(local_path, "alice-cred.xml"), 'r') as f:
        TEST_CREDENTIAL = {'geni_value': f.read(), 'geni_version': '3', 'geni_type': 'geni_sfa'}

    resources = geni3_Client.listResources([TEST_CREDENTIAL], True, False)

    try:
        context = etree.iterparse(BytesIO(resources['value']))
    except Exception as e:
        writeToLog("Exception %s" %str(e))

    delete_resources(agg_id)

    delete_reservations(agg_id)

    aggregate = AlienResourceAggregateModel.objects.get(id = agg_id)

#    for slice in aggregate.slice_set:
    # File (nodes)

    for action, elem in context:
        node_name = ""
        instance = am_resource()
        children_context = elem.iterchildren()
        # Node (tags)

        for elem in children_context:

            ls=str(elem.tag).partition("}")
            element=ls[2]

            if element=="switch":
                dpid=elem.attrib.get("dpid")

                setattr(instance, "name", dpid)
                connections[dpid] = []
                if instance:
                    AlienResourceController.create(instance, agg_id)

            elif element=="link":
                srcDpid=elem.attrib.get("dpidSrc")
                dstDpid=elem.attrib.get("dpidDst")
                srcPort=elem.attrib.get("portSrc")
                dstPort=elem.attrib.get("portDst")
                connections[srcDpid].append(dstDpid)
            elif element=="reservation":
                writeToLog("reservation %s" %str(elem.attrib.get("start_time")))
                try:
                    st_date=elem.attrib.get("start_time")
                    sdate = datetime.strptime(st_date , '%d/%m/%Y %H:%M:%S')
                    sdate=sdate.strftime("%Y-%m-%d %H:%M:%S")
                    ed_date=elem.attrib.get("end_time")
                    edate = datetime.strptime(ed_date , '%d/%m/%Y %H:%M:%S')
                    edate=edate.strftime("%Y-%m-%d %H:%M:%S")
                    s_urn=elem.attrib.get("slice_urn")
                    writeToLog("reservation start %s" %str(st_date))
                    writeToLog("reservation end %s" %str(ed_date))
                except Exception as e:
                    writeToLog("Exception %s"%str(e))

                AggregateReservationController.create(agg_id,sdate,edate,s_urn)

    for node, node_connections in connections.iteritems():
            connections_aux = []
            for connection in node_connections:
                try:
                    # Linked to another AlienResources
                    res = AlienResourceModel.objects.get(name = connection)
                    if res:
                        connections_aux.append(res)
                except:
                   pass
            connections[node] = connections_aux
            # Setting connections on resource with name as in 'node' var
            node_resource = AlienResourceModel.objects.get(name = node)
            node_resource.set_connections(connections[node])
            node_resource.save()

