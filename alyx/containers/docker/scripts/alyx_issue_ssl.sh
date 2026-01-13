#!/bin/bash
set -e
# This script is used to create a new SSL certificate for the Alyx server if certificates do not exist
# $APACHE_SERVER_NAME is the hostname, e.g. example.com, sub.example.com, or localhost

if [ "$APACHE_SERVER_NAME" = "localhost" ]; then
    echo "Deactivating SSL module for localhost."
    # Command to deactivate SSL module
    a2dismod ssl
    echo "Skipping certificate generation for localhost."
    exit 0
else
    echo "Enabling SSL module for $APACHE_SERVER_NAME."
    # Command to enable SSL module
    a2enmod ssl
    echo "SSL module enabled for $APACHE_SERVER_NAME."
fi

# First check if the certificate files exist
if [ ! -f /etc/ssl/certs/alyx_privkey.pem ] || [ ! -f  /etc/ssl/certs/alyx_fullchain.pem ]; then
    echo "SSL certificate files do not exist. Proceeding with certificate generation"
    # To get apache running for the certbot challenge we first create a temporary self-signed certificate
    echo "Generating self-signed SSL certificate for $APACHE_SERVER_NAME"
    openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
        -keyout /etc/ssl/certs/alyx_privkey.pem \
        -out /etc/ssl/certs/alyx_fullchain.pem \
        -subj "/C=GB/ST=London/L=London/O=IBL/OU=IT/CN=${APACHE_SERVER_NAME}" &&

    echo "Attempting to issue certificates for $APACHE_SERVER_NAME"
    # Start apache server with self-signed certificates
    apache2ctl start
    # Generate a new SSL certificate using certbot, which will overwrite the self-signed ones
    if [ -n "$CERTBOT_SG" ]; then  # call script to temporarily remove firewall for certbot challange
        /bin/bash /home/iblalyx/crons/renew_docker_certs.sh  # TODO issue flag for this script
    else
        certbot --apache --noninteractive --agree-tos --email $APACHE_SERVER_ADMIN --force-renewal -d $APACHE_SERVER_NAME
    fi
    # Assert that the certificate files were created
    if [ ! -f /etc/letsencrypt/live/$APACHE_SERVER_NAME/fullchain.pem ] || [ ! -f /etc/letsencrypt/live/$APACHE_SERVER_NAME/privkey.pem ]; then
        echo "Error: Certificate generation failed."
        exit 1
    fi
    rm -f /etc/ssl/certs/alyx_privkey.pem
    rm -f /etc/ssl/certs/alyx_fullchain.pem
    ln -s /etc/letsencrypt/live/$APACHE_SERVER_NAME/fullchain.pem /etc/ssl/certs/alyx_fullchain.pem
    ln -s /etc/letsencrypt/live/$APACHE_SERVER_NAME/privkey.pem /etc/ssl/certs/alyx_privkey.pem
    echo "Certificate generation successful."
    # Remove the temporary self-signed certificate files if they exist
    rm -f /etc/letsencrypt/live/$APACHE_SERVER_NAME-0001/
    rm /etc/letsencrypt/renewal/$APACHE_SERVER_NAME-0001.conf

    # Stop apache server (NB: will be started by docker-compose)
    apache2ctl stop

fi
