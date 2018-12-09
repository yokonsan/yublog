FROM python:3
MAINTAINER kyu yukun@eager.live
ENV CONFIG=docker

RUN mkdir /myapp
WORKDIR /myapp

COPY ./requirements.txt /myapp
COPY ./docker-entrypoint.sh /myapp
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install uwsgi \
    && chmod +x docker-entrypoint.sh

EXPOSE 9001

ENTRYPOINT ["bash", "docker-entrypoint.sh"]