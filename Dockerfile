# base image
FROM python:3.10-alpine

# set working directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# add requirements (to leverage Docker cache)
ADD ./requirements.txt /usr/src/app/requirements.txt

# install requirements
RUN apk add --update-cache \
 make automake gcc g++ linux-headers subversion python3-dev gcc libc-dev gmp-dev libffi-dev tzdata libpq-dev python3-dev
ENV TZ="America/New_York"
RUN cp /usr/share/zoneinfo/America/New_York /etc/localtime

RUN export LDFLAGS="-L/usr/local/opt/openssl/lib -L /usr/local/opt/gmp/lib"
RUN export CPPFLAGS="-I/usr/local/opt/openssl/include -I/usr/local/opt/gmp/include"

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ARG SCALA_VERSION=2.12.11
ARG SBT_VERSION=1.3.9
ENV SCALA_HOME=/usr/share/scala

RUN apk add openjdk11-jre
COPY . /usr/src/app
