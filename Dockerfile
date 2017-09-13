FROM openup/ckan-dokku:latest
MAINTAINER OpenUp

RUN pip install ckanext-envvars \
                boto3 \
                git+https://github.com/keitaroinc/ckanext-s3filestore.git@v0.0.8

RUN ln -s ./src/ckan/ckan/config/who.ini /who.ini
ADD ckan.ini /ckan.ini

CMD ["paster", "serve", "ckan.ini"]