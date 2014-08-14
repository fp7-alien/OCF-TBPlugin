

from django.db import models

class xmlrpcServerProxy(models.Model):

    class Meta:
        app_label = 'alien_plugin'

    username = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Username to use to access the remote server.")
    password = models.CharField(
        max_length=24, blank=True, null=True,
        help_text="Password to use to access the remote server.")

    #max_password_age = models.PositiveIntegerField(
    #    'Max Password age (days)', default=0,
    #    help_text="If this is set to non-zero, the password "\
    #        "will automatically be changed once the password ages past the "\
    #        "maximum. The new password is then randomly generated.")
    #password_timestamp = models.DateTimeField(auto_now_add=True)
    url = models.URLField("Server URL", verify_exists = False, max_length=1024,
         help_text="URL used to access the remote server's xmlrpc interface, should be https://DOMAIN_OR_IP:PORT/ROUTE_TO_XMLRPC_INTERFACE")
