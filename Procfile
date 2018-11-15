web: gunicorn --workers 2 --worker-class gevent --paste ckan.ini -t 600 --log-file -
worker: paster --plugin=ckan jobs worker --config /ckan.ini