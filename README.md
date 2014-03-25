OCF-TBPlugin
Expedient plugin that provides an interface to the Time Based Aggregate Manager (TBAM)

Installation:

1- copy the folder alien_plugin under .../ofelia/expedient/src/python/plugins/

2- Synchronize database:

    cd .../ofelia/expedient/src/python/expedient/clearinghouse

    python manage.py syncdb

3- Restart Apache

4- After that, an aggregate manager with the type 'Alien Resource Aggregate' can be created:
    
    Server URL: https://<IP-of-TBAM>:<port-of-TBAM>/

