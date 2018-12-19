FROM python:3
MAINTAINER kyu yukun@eager.live
ENV CONFIG=docker

RUN mkdir /myapp
WORKDIR /myapp

COPY ./requirements.txt /myapp
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install uwsgi

EXPOSE 9001

# ENTRYPOINT ["bash", "docker-entrypoint.sh"]