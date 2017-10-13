FROM openup/ckan:deps-latest
MAINTAINER OpenUp

RUN pip install ckanext-envvars \
                boto3 \
                git+https://github.com/keitaroinc/ckanext-s3filestore.git@v0.0.8 \
                git+https://github.com/OpenUpSA/ckanext-satreasury.git@master \
                -e git+https://github.com/ckan/ckanext-googleanalytics.git@v2.0.2#egg=ckanext-googleanalytics \
                git+https://github.com/OpenUpSA/ckanext-gdoc.git@master

RUN ln -s ./src/ckan/ckan/config/who.ini /who.ini
ADD ckan.ini /ckan.ini
ADD resource_formats.json /resource_formats.json

CMD ["newrelic-admin", "run-program", "gunicorn", "--workers", "2", "--worker-class", "gevent", "--paste", "ckan.ini", "-t", "600", "--log-file", "-"]
