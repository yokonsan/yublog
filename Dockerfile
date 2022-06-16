FROM python:3.8.7
LABEL creator="yokon" email="15152347277@163.com"
ENV CONFIG=docker

RUN mkdir /myapp
WORKDIR /myapp

COPY ./requirements.txt /myapp
COPY ./docker-entrypoint.sh /myapp
RUN pip install --upgrade pip \
    && pip install -i https://pypi.douban.com/simple/ -r requirements.txt \
    && pip install -i https://pypi.douban.com/simple/ uwsgi \
    && chmod +x docker-entrypoint.sh

EXPOSE 9001

# ENTRYPOINT ["bash", "docker-entrypoint.sh"]