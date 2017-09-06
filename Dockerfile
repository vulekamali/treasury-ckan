#FROM ubuntu:16.04
FROM ckan-linux-deps
MAINTAINER OpenUp

RUN pip install ckanext-envvars
RUN ln -s ./src/ckan/ckan/config/who.ini /who.ini
ADD ckan.ini /ckan.ini

CMD ["paster", "serve", "ckan.ini"]