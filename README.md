Dockerfile and config to run CKAN in dokku
==========================================

Setting up development environment
----------------------------------

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
