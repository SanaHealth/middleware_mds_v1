#!bin/bash
###################################################################
# Copies and installs the files needed to server mds from apache
###################################################################
# mds wsgi script
mkdir -p /opt/sana/wsgi
cp mds.wsgi /opt/sana/wsgi/
chown -R www-data:www-data /opt/sana/wsgi

# apache site configs
mkdir -p /etc/apache2/sites-available
cp sites-available/* /etc/apache2/sites-available/
a2ensite sana.default
a2ensite sana.default.ssl
service apache2 restart
