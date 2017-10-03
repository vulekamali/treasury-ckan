FROM openup/ckan:deps-latest
MAINTAINER OpenUp

RUN pip install ckanext-envvars \
                boto3 \
                git+https://github.com/keitaroinc/ckanext-s3filestore.git@v0.0.8 \
                git+https://github.com/OpenUpSA/ckanext-satreasury.git@master \
                -e git+https://github.com/ckan/ckanext-googleanalytics.git@v2.0.2#egg=ckanext-googleanalytics

RUN ln -s ./src/ckan/ckan/config/who.ini /who.ini
ADD ckan.ini /ckan.ini

CMD ["gunicorn", "--workers", "2", "--paste", "ckan.ini"]
