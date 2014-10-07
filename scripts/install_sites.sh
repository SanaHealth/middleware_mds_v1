#!bin/bash
################################################################################
# For Ubuntu systems
# Copies and installs the wsgi files needed to serve mds from apache
################################################################################
mkdir -p /var/www/wsgi
cp ../include/wsgi/mds.wsgi /var/www/wsgi
chown -R www-data:www-data /var/www/wsgi

# apache site configs
mkdir -p /etc/apache2/sites-available
cp ../include/etc/sites-available/* /etc/apache2/sites-available/
#
a2ensite sana.default
a2ensite sana.default.ssl
service apache2 restart
