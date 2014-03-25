
import re
from django.db import models
from django.conf import settings
from expedient.clearinghouse.resources import models as resource_models
from expedient.clearinghouse.slice import models as slice_models
from expedient.clearinghouse.aggregate import models as aggregate_models
from expedient.common.xmlrpc_serverproxy.models import PasswordXMLRPCServerProxy

from expedient.common.utils import create_or_update, modelfields
from expedient.clearinghouse.slice.models import Slice
from django.core.exceptions import ValidationError


cntrlr_url_re = re.compile(r"(tcp|ssl):(?P<address>[\w\.]*):(?P<port>\d*)")
def validate_controller_url(value):
    def error():
        raise ValidationError(
            u"Invalid controller URL. The format is "
            "tcp:<hostname>:<port> or ssl:<hostname>:<port>. Port must "
            "be less than %s" % (2**16),
            code="invalid",
        )

    def self_fv_error():
        raise ValidationError(
            u"Invalid controller URL. You can not use the Island FlowVisor as your controller.",code="invalid",
        )

    m = cntrlr_url_re.match(value)
    if m:
        port = m.group("port")
	if m.group("address") == "127.0.0.1" or m.group("address") == settings.SITE_IP_ADDR or m.group("address") == settings.SITE_DOMAIN:
            self_fv_error()
        elif not port:
            error()
        else:
            port = int(port)
            if port > 2**16-1:
                error()
    else:
        error()

def validate_vlan_id(value):
    first_vlan_id=1
    last_vlan_id=500
    def error():
        raise ValidationError(
            u"Invalid VLAN ID "
            "ID must be in the range %s %e" %str(first_vlan_id) %str(last_vlan_id),
            code="invalid",
        )
    try:
        vlan_id=int(value)
        if vlan_id<first_vlan_id or vlan_id>last_vlan_id:
            error()
    except:
        error()

class AlienSliceInfo(models.Model):
    class Meta:
        """Meta class for AlienResource model."""
        app_label = 'alien_plugin'

    slice = models.OneToOneField(slice_models.Slice)
    start_date= models.DateTimeField(
        help_text="start date of reservation", null=True, blank=True)
    end_date= models.DateTimeField(
        help_text="end date of reservation", null=True, blank=True)
    slice_urn= models.CharField(max_length = 1024, default = "")

    slice_status= models.CharField(max_length = 1024, default = "")

    controller_url = models.CharField(
        "OpenFlow controller URL", max_length=100, default = "Not set",
        validators=[validate_controller_url],
        help_text=u"The format should be tcp:hostname:port or ssl:hostname:port")
    alien_vlan=models.IntegerField(null=True, blank=True )
    ofelia_vlan=models.IntegerField(null=True, blank=True)