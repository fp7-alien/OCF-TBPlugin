
from django.db import models
from django.core.exceptions import MultipleObjectsReturned
from expedient.clearinghouse.aggregate.models import Aggregate
from expedient.common.permissions.shortcuts import must_have_permission
from alien_plugin.models.AlienResource import AlienResource
from alien_plugin.models.AlienSliceInfo import AlienSliceInfo
from alien_plugin.log.log import *
from expedient.common.messaging.models import DatedMessage
from expedient.common.timer.models import Job
from expedient.common.timer.exceptions import JobAlreadyScheduled
from random import randrange
#from django.conf import settings
from django.core.urlresolvers import reverse
#from expedient.common.xmlrpc_serverproxy.models import PasswordXMLRPCServerProxy
from alien_plugin.controller.geni_api_three_client import *

from alien_plugin.log.log import *
#from alien_plugin.controller.GUIdispatcher import *

import lxml.etree
import lxml.builder
import os.path
from datetime import datetime

from plugins.openflow.plugin.models import OpenFlowAggregate


from io import BytesIO
from lxml import etree

from xml.etree.ElementTree import Element, SubElement, Comment, tostring

# AlienResource Aggregate class
class AlienResourceAggregate(Aggregate):
    # Alien Resource Aggregate information field
    information = "An aggregate of Alien resources"
    
    class Meta:
        app_label = 'alien_plugin'
        verbose_name = "Alien Resource Aggregate"

    client = models.OneToOneField('xmlrpcServerProxy', editable = False, blank = True, null = True)
    #client = models.OneToOneField(PasswordXMLRPCServerProxy)
    '''
    def setup_new_aggregate(self, base_uri):
        self.client.install_trusted_ca()

        if base_uri.endswith("/"): base_uri = base_uri[:-1]
        try:
#            logger.debug("Registering topology callback at %s%s" % (
#                base_uri, reverse("openflow_open_xmlrpc")))
            err = self.client.proxy.register_topology_callback(
                "%s%s" % (base_uri, reverse("openflow_open_xmlrpc")),
                "%s" % self.pk,
            )
            if err:
                return err
        except Exception as ret_exception:
            import traceback
            writeToLog("XML RPC call failed to aggregate %s" % self.name)
            traceback.print_exc()
            return str(ret_exception)

        # schedule a job to automatically update resources

        try:
            Job.objects.schedule(
                settings.OPENFLOW_TOPOLOGY_UPDATE_PERIOD,
                self.update_topology,
            )
        except JobAlreadyScheduled:
            pass

        err = self.update_topology()
        if err: return err
        '''

    def check_status(self):
        #writeToLog("----TBAM Status Check----" )
        """Checks whether the aggregate is available or not.

        @return: True if the aggregate is available, False otherwise.
        """
        local_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'certs'))
        key_path = os.path.join(local_path, "alice-key.pem") # make sure the CA of the AM is the same which issued this certificate (e.g. copy certificates from omni)
        cert_path = os.path.join(local_path, "alice-cert.pem")


        try:
            client2 = GENI3Client(self.get_client_IP(), self.get_client_port(), key_path, cert_path)
            with open(os.path.join(local_path, "alice-cred.xml"), 'r') as f:
                TEST_CREDENTIAL = {'geni_value': f.read(), 'geni_version': '3', 'geni_type': 'geni_sfa'}
            #resources = client2.listResources([TEST_CREDENTIAL], True, False)
            resources = client2.getVersion()

            av=True
            #writeToLog("client :%s" %str(self.client.url))
            #writeToLog("client :%s" %str(self.get_client_IP()))
            #writeToLog("client :%s" %str(self.get_client_port()))
            #sync_am_resources(self.id, client2)
        except Exception as e:
            av=False
            writeToLog("Exception: %s" %str(e))
        return av

    def start_slice(self, slice):
        #writeToLog("starting slice ")
        sr_aggs = []
        try:
            sr_aggs = slice.aggregates.filter(leaf_name=AlienResourceAggregate.__name__.lower())
        except:
            pass
        for agg in sr_aggs:

            agg_status=agg.as_leaf_class().check_status()
            writeToLog("status is checked %s" %str(agg_status))
            if agg_status != agg.available:
                agg.available = agg_status
                agg.save()


        super(AlienResourceAggregate, self).start_slice(slice)

        info = AlienSliceInfo.objects.get(slice=slice)

        writeToLog("starting alien slice %s" %str(info.id))
        writeToLog("starting alien slice %s" %str(info.slice_urn))
        writeToLog("starting alien slice %s" %info.start_date.strftime("%d/%m/%y %H:%M:%S"))
        ## create xml file for slice allocation:

        root = Element('rspec')
        root.set('type', 'request')

        root.set('xmlns', 'http://www.geni.net/resources/rspec/3')
        root.set('xmlns:xs', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xmlns:aggregate', 'http://example.com/aggregate')
        root.set('xs:schemaLocation', 'http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/ad.xsd http://example.com/dhcp/req.xsd')


        ch1 = SubElement(root, 'aggregate:slice',
                             {'slice_urn':'urn:publicid:IDN+test:fp7-ofelia:eu+slice+pizzaslice',
                              })

        ch2 = SubElement(root, 'aggregate:timeslot',
                             {'start_time':info.start_date.strftime("%d/%m/%Y %H:%M:%S"),
                              'end_time':info.end_date.strftime("%d/%m/%Y %H:%M:%S"),
                              })

        ch3 = SubElement(root, 'aggregate:VLAN',
                             {'ALIEN':str(info.alien_vlan),
                              'OFELIA':'3',
                              })

        ch4 = SubElement(root, 'aggregate:controller',
                             {'url':str(info.controller_url),
                              })

        ## send allocate slice to TBAM
        writeToLog("starting alien slice %s" %tostring(root))

        local_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'certs'))
        key_path = os.path.join(local_path, "alice-key.pem") # make sure the CA of the AM is the same which issued this certificate (e.g. copy certificates from omni)
        cert_path = os.path.join(local_path, "alice-cert.pem")

        returned_rspec=''
        message=''
        slice_status=''

        try:
            client2 = GENI3Client(self.get_client_IP(), self.get_client_port(), key_path, cert_path)
            with open(os.path.join(local_path, "alice-cred.xml"), 'r') as f:
                TEST_CREDENTIAL = {'geni_value': f.read(), 'geni_version': '3', 'geni_type': 'geni_sfa'}
            with open(os.path.join(local_path, "pizzaslice_cred.xml"), 'r') as f:
                TEST_SLICE_CREDENTIAL = {'geni_value': f.read(), 'geni_version': '3', 'geni_type': 'geni_sfa'}

            #resources = client2.listResources([TEST_CREDENTIAL], True, False)

            TEST_SLICE_URN = 'urn:publicid:IDN+test:fp7-ofelia:eu+slice+pizzaslice'
            #TEST_SLICE_URN = 'slice1'
            #client2.allocate(TEST_SLICE_URN, [TEST_SLICE_CREDENTIAL], tostring(root), datetime.now())

            '''

            try:
                client2.delete([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL])
            except:
                pass
            '''

            res1=client2.allocate(TEST_SLICE_URN, [TEST_SLICE_CREDENTIAL], tostring(root), datetime.now())
            ### check if manifast is received
            try:
                returned_rspec=res1['value']['geni_rspec']
            except Exception as e:
                writeToLog("Exception %s" %str(res1))
                message=str(res1['output'])
                raise Exception(message)

            ### parse the returned output
            ### if manifest is returned, change status of slice to allocated
            if returned_rspec!='':
                try:
                    context = etree.iterparse(BytesIO(returned_rspec))
                    for action, elem in context:
                        resType=elem.attrib.get("type")
                        if resType=='manifest':
                            slice_status='allocated'
                            alien_slice=AlienSliceInfo.objects.get(slice=slice)
                            alien_slice.slice_status='allocated'
                            alien_slice.save()

                            break
                except Exception as e:
                    writeToLog("Exception  %s" %str(e))
                    message=str(e)
                    raise Exception(message)

            #writeToLog("slice status:  %s" %str(slice_status))

            # if slice status is allocated
            if slice_status=='allocated':
                # check if the slice include ofelia island
                ofelia_aggs = []
                try:
                    ofelia_aggs = slice.aggregates.filter(leaf_name=OpenFlowAggregate.__name__.lower())
                    #writeToLog("length %s" %str(len(ofelia_aggs)))

                    if len(ofelia_aggs)>0:

                        res=client2.provision([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL], best_effort=True, end_time= datetime.now())
                        #writeToLog("provision result: %s" %str(res))
                        #writeToLog("slice status: %s" %str(client2.status([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL])))

                        ##
                        ### check if manifast is received
                        try:
                            returned_rspec=res1['value']['geni_rspec']
                        except Exception as e:
                            writeToLog("Exception %s" %str(res1))
                            message=str(res1['output'])
                            raise Exception(message)

                        ### parse the returned output
                        ### if manifest is returned, change status of slice to allocated
                        if returned_rspec!='':
                            try:
                                context = etree.iterparse(BytesIO(returned_rspec))
                                for action, elem in context:
                                    resType=elem.attrib.get("type")
                                    if resType=='manifest':
                                        slice_status='allocated'
                                        alien_slice=AlienSliceInfo.objects.get(slice=slice)
                                        alien_slice.slice_status='provisioned'
                                        alien_slice.save()

                                        break
                            except Exception as e:
                                writeToLog("Exception  %s" %str(e))
                                message=str(e)
                                raise Exception(message)
                        ##

                        alien_slice=AlienSliceInfo.objects.get(slice=slice)

                        ### call allocate to update vlan ID
                        ofelia_vlan=5
                        alien_slice.ofelia_vlan=ofelia_vlan
                        alien_slice.save()

                        #### make new xml file for allocation
                        root2 = Element('rspec')
                        root2.set('type', 'request')
                        root2.set('xmlns', 'http://www.geni.net/resources/rspec/3')
                        root2.set('xmlns:xs', 'http://www.w3.org/2001/XMLSchema-instance')
                        root2.set('xmlns:aggregate', 'http://example.com/aggregate')
                        root2.set('xs:schemaLocation', 'http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/ad.xsd http://example.com/dhcp/req.xsd')

                        ch1 = SubElement(root2, 'aggregate:slice',
                                         {'slice_urn':'urn:publicid:IDN+test:fp7-ofelia:eu+slice+pizzaslice',
                                          })
                        ch2 = SubElement(root2, 'aggregate:timeslot',
                                         {'start_time':alien_slice.start_date.strftime("%d/%m/%Y %H:%M:%S"),
                                          'end_time':alien_slice.end_date.strftime("%d/%m/%Y %H:%M:%S"),
                                          })

                        ch3 = SubElement(root2, 'aggregate:VLAN',
                                         {'ALIEN':str(alien_slice.alien_vlan),
                                          'OFELIA':str(alien_slice.ofelia_vlan),
                                          })
                        ch4 = SubElement(root2, 'aggregate:controller',
                                         {'url':str(alien_slice.controller_url),
                                          })

                        res1=client2.allocate(TEST_SLICE_URN, [TEST_SLICE_CREDENTIAL], tostring(root), datetime.now())
                        try:
                            returned_rspec=res1['value']['geni_rspec']

                        except Exception as e:
                            writeToLog("Exception %s" %str(res1))
                            message=str(res1['output'])
                            raise Exception(message)


                    else:
                        #### call provision

                        res=client2.provision([TEST_SLICE_URN], [TEST_SLICE_CREDENTIAL], best_effort=True, end_time= datetime.now())
                        #writeToLog("provision result: %s" %str(res))
                        alien_slice=AlienSliceInfo.objects.get(slice=slice)
                        alien_slice.slice_status='provisioned'
                        writeToLog("Provisioning is sucessful")
                        alien_slice.save()

                except:
                    pass

            #writeToLog("allocation output %s "%str(res1['value']))
        except Exception as e:
            writeToLog("Exception %s" %str(e))
            message=str(e)
            raise Exception("Can't start slice  %s %s :" % (slice.name,message))



    def stop_slice(self, slice):
        super(AlienResourceAggregate, self).stop_slice(slice)
        pass

#    def get_resources(self, slice_id):
    def get_resources(self):
        try:
#            return AlienResource.objects.filter(slice_id = slice_id, aggregate = self.pk)

            DatedMessage.objects.post_message_to_user(
                                "Could not synchronize resources %s within Expedient" % str("qqqqqqqqqqqqq"),
                                user="root", msg_type=DatedMessage.TYPE_WARNING,
                            )
            return AlienResource.objects.filter(aggregate = self.pk)
        except Exception as e:
            return []

    def remove_from_project(self, project, next):
        """
        aggregate.remove_from_project on a AlienResource AM will get here first to check
        that no slice inside the project contains AlienResource's for the given aggregate
        """
        # Check permission because it won't always call parent method (where permission checks)
        must_have_permission("user", self.as_leaf_class(), "can_use_aggregate")

        alien_plugins = self.resource_set.filter_for_class(AlienResource).filter(AlienResource__project_id=project.uuid)
        offending_slices = []
        for resource in alien_plugins:
            offending_slices.append(str(resource.AlienResource.get_slice_name()))
        # Aggregate has AlienResource's in slices -> stop slices and remove AM from it if possible
        if offending_slices:
            for slice in project.slice_set.all():
                try:
                    self.stop_slice(slice)
                    self.remove_from_slice(slice, next)
                except:
                    pass
            raise MultipleObjectsReturned("Please delete all Alien Resources inside aggregate '%s' before removing it from slices %s" % (self.name, str(offending_slices)))
        # Aggregate has no AlienResource's in slices (OK) -> delete completely from project (parent method)
        else:
            return super(AlienResourceAggregate, self).remove_from_project(project, next)

    def remove_from_slice(self, slice, next):
        """
        aggregate.remove_from_slice on a AlienResource AM will get here first to check
        that the slice does not contain AlienResource's for the given aggregate
        """
        # Warn if any AlienResource (created in this slice) is found inside the AlienResource AM
        #if self.resource_set.filter_for_class(AlienResource).filter(AlienResource__slice_id=slice.uuid):
        #    raise MultipleObjectsReturned("Please delete all Alien Resources inside aggregate '%s' before removing it" % str(self.name))
        return super(AlienResourceAggregate, self).remove_from_slice(slice, next)

    def get_client_IP(self):
        list=self.client.url.split("://")
        list=list[1].split(":")
        return list[0]

    def get_client_port(self):
        list=self.client.url.split(":")
        list=list[2].split("/")
        return list[0]

