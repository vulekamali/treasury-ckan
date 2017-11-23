FROM ubuntu:16.04
MAINTAINER OpenUp

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update \
 && apt-get install -y python-dev \
                       libpq-dev \
                       python-pip \
                       git-core
ADD requirement-setuptools.txt .
ADD requirements.txt .
RUN pip install -r requirement-setuptools.txt
RUN pip install -r requirements.txt
RUN pip install -e 'git+https://github.com/OpenUpSA/ckan.git@ckan-2.7.2-openup#egg=ckan'
