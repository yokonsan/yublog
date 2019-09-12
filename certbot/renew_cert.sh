#!/bin/bash
WEBDIR="$1"
DOMAIN=example.com
DOMAIN2=www.example.com
EMAIL=example@email.com
LED_LIST=()
WWW_ROOT=/usr/share/nginx/html
docker run --rm \
    -v ${WEBDIR}/nginx/conf.crt:/etc/letsencrypt \
    -v ${WEBDIR}/certbot/log:/var/log/letsencrypt \
    -v ${WEBDIR}/source/app/static/upload:${WWW_ROOT} \
    certbot \
    certonly --verbose --noninteractive --quiet --agree-tos \
    --webroot -w ${WWW_ROOT} \
    --email=${EMAIL} \
    -d ${DOMAIN} -d ${DOMAIN2}
CODE=$?
if [ $CODE -ne 0 ]; then
    echo "Create failure!"
fi
