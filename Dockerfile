FROM python:3
MAINTAINER yokon 15152347277@163.com
ENV CONFIG=docker

RUN mkdir /myapp
WORKDIR /myapp

COPY ./requirements.txt /myapp
RUN pip install --upgrade pip \
    && pip install -i https://pypi.douban.com/simple/ -r requirements.txt

EXPOSE 9001

# ENTRYPOINT ["bash", "docker-entrypoint.sh"]