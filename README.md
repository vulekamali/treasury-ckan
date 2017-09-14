Dockerfile and config to run CKAN in dokku
==========================================

This CKAN installation depends on
 - Postgres - main database and DataStore plugin ad-hoc tables
 - Solr - search on the site
 - Redis - as a queue for background processes
 - S3 - object (file) storage

It is recommended to use an HTTP cache in front of CKAN in production.

Setting up in production
------------------------

We set up Solr and Redis on the same server and use a remote Postgres instance.

### Solr

Deploy an instance of [Solr configured for CKAN](https://github.com/OpenUpSA/ckan-solr-dokku)

### Redis

We use the dokku Redis plugin.

Install the plugin according to https://github.com/dokku/dokku-redis#installation

```
dokku redis:create ckan-redis
```

### Postgres

Create the database and credentials

```
create user ckan_default with password 'some good password';
alter role ckan_default with login;
grant ckan_default to superuser;
create database ckan_default with owner ckan_default;
```

### S3

Create a bucket and a programmatic access user, and grant the user full access to the bucket with the following policy

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                "arn:aws:s3:::treasury-data-portal/*",
                "arn:aws:s3:::treasury-data-portal"
            ]
        }
    ]
}
```

### CKAN

Create the CKAN app in dokku

```
dokku apps:create ckan
```

Get the Redis `Dsn` (connection details) for setting in CKAN environment in the next step with `/0` appended.

```
dokku redis:info ckan-redis
```

Set CKAN environment variables, replacing these examples with actual producation ones

- REDIS_URL: use the Redis _Dsn_
- SOLR_URL: use the alias given for the docker link below
- BEAKER_SESSION_SECRET: this must be a secret long random string. Each time it changes it invalidates any active sessions.
- S3FILESTORE__SIGNATURE_VERSION: use as-is - no idea why the plugin requires this.

```
dokku config:set ckan CKAN_SQLALCHEMY_URL=postgres://ckan_default:password@host/ckan_default \
                      CKAN_REDIS_URL=.../0 \
                      CKAN_SOLR_URL=http://solr:8983/solr/ckan \
                      CKAN_SITE_URL=http://treasurydata.openup.org.za/ \
                      CKAN___BEAKER__SESSION__SECRET= \
                      CKAN_SMTP_SERVER= \
                      CKAN_SMTP_USER= \
                      CKAN_SMTP_PASSWORD= \
                      CKAN_SMTP_MAIL_FROM=webapps+treasury-portal@openup.org.za \
                      CKAN___CKANEXT__S3FILESTORE__AWS_BUCKET_NAME=treasury-data-portal \
                      CKAN___CKANEXT__S3FILESTORE__AWS_ACCESS_KEY_ID= \
                      CKAN___CKANEXT__S3FILESTORE__AWS_SECRET_ACCESS_KEY= \
                      CKAN___CKANEXT__S3FILESTORE__HOST_NAME=http://s3-eu-west-1.amazonaws.com/treasury-data-portal \
                      CKAN___CKANEXT__S3FILESTORE__REGION_NAME=eu-west-1 \
                      CKAN___CKANEXT__S3FILESTORE__SIGNATURE_VERSION=s3v4
```

Link CKAN and Redis

```
dokku redis:link ckan-redis ckan
```

Link CKAN and Solr

```
dokku docker-options:add ckan run,deploy --link ckan-solr.web.1:solr
```

Create a named docker volume and onfigure ckan to use the volume just so we can configure an upload path. It _should_ be kept clear by the s3 plugin.


```
docker volume create --name ckan-filestore
dokku docker-options:add ckan run,deploy --volume ckan-filestore:/var/lib/ckan/default
```

Allow large file uploads by creating an nginx config file (and directory if needed) at `/home/dokku/ckan/nginx.conf.d/ckan.conf` with the following:

```
client_max_body_size 100M;
client_body_timeout 120s;
```

Then let nginx load it

```
sudo chown dokku:dokku /home/dokku/ckan/nginx.conf.d/ckan.conf
sudo service nginx reload
```

Add the dokku app remote to your local git clone

```
git remote add dokku dokku@dokku7.code4sa.org:ckan
```

Push the app to the dokku remote

```
git push dokku master
```

Set up database and first sysadmin user.

```
dokku run ckan bash
cd src/ckan
paster db init -c /ckan.ini
paster sysadmin add admin email="webapps@openup.org.za" -c /ckan.ini
```

### HTTP Cache

http://docs.ckan.org/en/ckan-2.7.0/maintaining/installing/deployment.html#create-the-nginx-config-file or cloudflare?

Setting up development environment
----------------------------------

While you can set up CKAN directly on your OS, docker-compose is useful to develop and test the docker/dokku-specific aspects.

- create database
- create a file `env.dev` in the project root, based on `env.tmpl` with S3 bucket config
  - To help you avoid committing sensitive information in this file to git, env* is hidden by gitignore.
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