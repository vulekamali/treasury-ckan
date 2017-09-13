Dockerfile and config to run CKAN in dokku
==========================================

Setting up development environment
----------------------------------

While you can set up CKAN directly on your OS, docker-compose is useful to develop and test the docker/dokku-specific aspects.

- create database
- start services
```
docker-compose up
```
- Set up database and first sysadmin user.
```
docker-compose exec ckan bash
cd src/ckan
paster db init -c /ckan.ini
paster sysadmin add admin email="admin@admin.admin" -c /ckan.ini
```

### Rebuilding the search index

You might need to rebuild the search index, e.g. if you newly/re-created the docker volume holding the `ckan` solr core data.

```
docker-compose exec ckan bash
cd src/ckan
paster --plugin=ckan search-index rebuild -c /ckan.ini
```