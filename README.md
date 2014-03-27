
1. Requirements
---------------

* GNU/Linux Debian-based distros
* Python 2.6


2. Installation for Expedient
---------------------------------------------------

- Install MySQL server

    apt-get install mysql-server

- Create Expedient database.

    mysql -p
    mysql> CREATE DATABASE expedient;
    Query OK, 1 row affected (0.00 sec)

    mysql> GRANT ALL ON expedient.* TO userName@127.0.0.1 IDENTIFIED BY 'password';
    Query OK, 0 rows affected (0.00 sec)

- Clone the OCF repository under folder /opt:

    cd /opt
    git clone https://github.com/fp7-ofelia/ocf.git ofelia

- In the file:
     /opt/ofelia/expedient/bin/versions/default/install/lib/pypelib

  change the line: 

     /usr/bin/wget https://github.com/fp7-ofelia/pypelib/raw/deb/pypelib_latest_all.deb || error "Could not download pypel$

  into: 

     /usr/bin/wget --no-check-certificate https://github.com/fp7-ofelia/pypelib/raw/deb/pypelib_latest_all.deb || error "Could not download pypel$
     
   
- Trigger OFVER installation by performing the following as a root user:

    cd /opt/ofelia/expedient/bin
    ./ofver install

Note 1: When installation starts, ofver will ask if it is an OFELIA project installation or not. Select No (N) for non OFELIA testbeds.

Note 2: you will need to create the certificates for the Certification Authority (CA) first and for the component (i.e. expedient) later. Do not use the same Common Name (CN) for both of them, and make sure that the CN you use in the component later certificate (you can use an IP) is the same you then set in the SITE_DOMAIN field in the localsettings.py file

Note 3: Modify the localsettings.py or mySettings.py depending on the component (i.e. expedient) being installed: 
        The next lines need to be changed:

          ROOT_USERNAME = "user"
          ROOT_PASSWORD = "pass"

          DATABASE_NAME = "expedient"
          DATABASE_USER = "user"
          DATABASE_PASSWORD = "pass"

          SITE_DOMAIN = "localhost:1234" 



- Run: ./opt/ofelia/expedient/src/python/expedient/clearinghouse/manage.py  create_default_root

- try locally to open https://localhost/ , and to login into expedient.

- to install other components Optin and VM Manager, check https://github.com/fp7-ofelia/ocf

3. Installation for TB-plugin
---------------------------------------------------
- Clone the plugin folder:

    git clone https://github.com/fp7-alien/OCF-TBPlugin.git TB-plugin

- Copy the folder TB-plugin/alien_plugin under /opt/ofelia/expedient/src/python/plugins/

- Synchronize database:

    cd /opt/ofelia/expedient/src/python/expedient/clearinghouse
    python manage.py syncdb

- Restart Apache

- After that, an aggregate manager with the type 'Alien Resource Aggregate' can be created:

    Server URL: https://<IP-of-TBAM>:<port-of-TBAM>/
