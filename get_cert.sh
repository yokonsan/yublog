#!/bin/bash
DOMAIN=example.com
DOMAIN2=www.example.com
EMAIL=example@email.com
NGINXCONTAINER=yublog_proxy

docker ps --filter name=^/${NGINXCONTAINER}$

if [ $? -ne 0 ];then
    echo "Nginx did not start"
    docker run --rm -p 80:80 -p 443:443\
        -v $PWD/nginx/conf.crt:/etc/letsencrypt \
        certbot/certbot auth --standalone \
        -m ${EMAIL} --agree-tos \
        -d ${DOMAIN} -d ${DOMAIN2}
else
    docker stop ${NGINXCONTAINER}
    docker run --rm -p 80:80 -p 443:443\
        -v $PWD/nginx/conf.crt:/etc/letsencrypt \
        certbot/certbot auth --standalone \
        -m ${EMAIL} --agree-tos \
        -d ${DOMAIN} -d ${DOMAIN2}

    docker start ${NGINXCONTAINER}
fi
