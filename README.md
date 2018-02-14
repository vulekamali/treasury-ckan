
Data Portal for the South African National Treasury
===================================================

This is the software repository for the South African National Treasury Data Portal.

We use CKAN to organise the datasets according to various taxonomies and use the CKAN dataset API to make the data discoverable.

This repository also contains [code and documentation to load and maintain data in CKAN](#extract-transform-load-etl).

Dockerfile and config to run CKAN in dokku
------------------------------------------

We run CKAN on the dokku platform. We use dokku's dockerfile deployment method to deploy using the the Dockerfile in this repository. Since there are numerous operating system and python dependencies that ckan relies on, we build an image with these on hub.docker.com using Dockerfile-deps.

The Dockerfile then builds on this. We install CKAN plugins using the Dockerfile, which makes it easier to try different ones and keep all plugin installation in one place. These don't take a lot of time so moving them to Dockerfile-deps isn't as important as flexibilty.

This CKAN installation depends on
 - Postgres - main database ad-hoc tables
 - Solr - search on the site
 - Redis - as a queue for background processes
 - S3 - object (file) storage
 - [CKAN DataPusher](https://github.com/OpenUpSA/ckan-datapusher) - [while limited](https://github.com/ckan/ckan/pull/3911), this might help us quickly access data programmatically.
 - NGINX - caching (when needed)

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
-- create datastore user and db
create user datastore_default with password 'some good password';
create database datastore_default with owner ckan_default;
```

*Remember to set the correct permissions for the datastore database*

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
                      CKAN_INI=/ckan.ini \
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
                      CKAN___CKANEXT__S3FILESTORE__SIGNATURE_VERSION=s3v4 \
                      NEW_RELIC_APP_NAME="Treasury CKAN" \
                      NEW_RELIC_LICENSE_KEY=...
```

Link CKAN and Redis

```
dokku redis:link ckan-redis ckan
```

Link CKAN and Solr

```
dokku docker-options:add ckan run,deploy --link ckan-solr.web.1:solr
```

Link CKAN and CKAN DataPusher

```
dokku docker-options:add ckan run,deploy --link ckan-datapusher.web.1:ckan-datapusher
```

Create a named docker volume and configure ckan to use the volume just so we can configure an upload path. It _should_ be kept clear by the s3 plugin.


```
docker volume create --name ckan-filestore
dokku docker-options:add ckan run,deploy --volume ckan-filestore:/var/lib/ckan/default
```

We customise the app nginx config to

- Allow large file uploads
- Allow a longer request timeout
- Redirect www to non-www (because peope WILL add www to links they shouldn't)
- Log to a second file showing the hostname used to access the server
- To be prepared for caching when needed.

*This breaks letsencrypt renewal so uncomment these and reload nginx to renew the letsencrypt certificate*

Add the following to the logging part of the `http` block of `/etc/nginx/nginx.conf`:

```
    log_format combined '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                        '"$http_referer" "$http_user_agent"';

    proxy_cache_path /tmp/nginx_cache levels=1:2 keys_zone=ckan:30m max_size=250m;
    proxy_temp_path /tmp/nginx_proxy 1 2;
```

Add the following nginx config file (and directory if needed) at `/home/dokku/ckan/nginx.conf.d/ckan.conf`:

```
## Caching

proxy_cache ckan;

# Don't cache or served cached copies when any of these authentication
# cookies or headers are set.
proxy_cache_bypass $cookie_auth_tkt$http_x_ckan_api_key$http_authorization;
proxy_no_cache $cookie_auth_tkt$http_x_ckan_api_key$http_authorization;

proxy_cache_valid 30m;
proxy_cache_key $host$scheme$proxy_host$request_uri;

## Uncomment to debug caching
# add_header X-Proxy-Cache $upstream_cache_status;

# Uncomment the next line to enable caching
# proxy_ignore_headers X-Accel-Expires Expires Cache-Control;

## ---

client_max_body_size 100M;
client_body_timeout 120s;

access_log  /var/log/nginx/ckan-access-extended.log ckan;

if ($host = www.budgetportal.openup.org.za) {
  return 301 $scheme://budgetportal.openup.org.za$request_uri;
}

if ($host = www.treasurydata.openup.org.za) {
  return 301 $scheme://treasurydata.openup.org.za$request_uri;
}
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

Setup cron jobs.

```
sudo mkdir /var/log/ckan/
sudo touch /var/log/ckan/cronjobs.log
sudo chown ubuntu:ubuntu /var/log/ckan/cronjobs.log
crontab -e

# hourly, update tracking stats, see http://docs.ckan.org/en/ckan-2.7.0/maintaining/tracking.html#tracking
5 * * * * /usr/bin/dokku --rm run ckan paster --plugin=ckan tracking update 2017-09-01 2>&1 >> /var/log/ckan/cronjobs.log && /usr/bin/dokku --rm run ckan paster --plugin=ckan search-index rebuild -r 2>&1 >> /var/log/ckan/cronjobs.log
```

### HTTP Cache


#### CloudFront

Create a Cache Behaviour

- Path pattern: `/`
- Viewer Protocol Policy: `Redirect HTTP to HTTPS`
- Cache Based on Selected Request Headers: `Whitelist`
  - Add custom `x-ckan-api-key`
  - Add standard `Authorization`
- Object Caching: `Customise` and set all TTLs to something sensible like 1800 (30 minutes)
- Forward Cookies: `Whitelist`
  - add `auth_tkt`
- Query String Forwarding and Caching: `Forward all, cache based on all`
- Compress Objects Automatically: `yes`

To enable, ensure it's above the default. To disable, ensure it's below the default.

To invalidate, create an Invalidation with the relevant path, e.g. /* for everything in the Distribution.

#### Nginx

To enable the nginx cache, uncomment `proxy_ignore_headers` in `/home/dokku/ckan/nginx.conf.d/ckan.conf` and reload `nginx:

```
sudo service nginx reload
```

It is important to exempt any authenticated requests from caching. Authenticated requests can be made by the AUTH_TKT cookie, and the Authorization or X-CKAN-AUTH-Key headers. For this reason, publicly-accessible requests should not use authentication.

http://docs.ckan.org/en/ckan-2.7.0/maintaining/installing/deployment.html#create-the-nginx-config-file

To invalidate: `find /path/to/your/cache -type f -delete`


### CKAN Celery

dokku apps:create ckan-celery


git remote add dokku-celery dokku@treasury1.openup.org.za:ckan

Setting up development environment
----------------------------------

While you can set up CKAN directly on your OS, docker-compose is useful to develop and test the docker/dokku-specific aspects.

- create database
- create a file `env.dev` in the project root, based on `env.tmpl` with DB and S3 bucket config
  - To help you avoid committing sensitive information in this file to git, env* is hidden by gitignore.
Start services

```
docker-compose up
```

Set up database. First we start a shell in the ckan container, then change
directory to so that the paster commands are found, then we run the paster
command which sets up the database stuff. Finally the SQL for setting up
permissions for the datastore extension. Execute these using a postgres
superuser.

```
docker-compose exec ckan bash
cd src/ckan
paster db init -c /ckan.ini
paster datastore set-permissions -c /ckan.ini
```

First sysadmin user

```
docker-compose exec ckan bash
cd src/ckan
paster sysadmin add admin email="admin@admin.admin" -c /ckan.ini
```

### Rebuilding the search index

You might need to rebuild the search index, e.g. if you newly/re-created the docker volume holding the `ckan` solr core data.

```
docker-compose exec ckan bash
cd src/ckan
paster --plugin=ckan search-index rebuild -c /ckan.ini
```

Extract, Transform, Load (ETL)
------------------------------

To start with, this will document the partly manual and irregular process of getting the data together and uploaded to CKAN.

### Estimates of Provincial Revenue and Expenditure (EPRE)

EPREs are scraped from treasury.gov.za and stored under `etl-data`. These should not be added to git. The folder is therefore gitignored.

Metadata from the scrape is also stored there, as specified by `--output`. We use Line-delimited JSON objects `jl` because the CSV output doesn't handle the two different types of items.

```
scrapy runspider --output=etl-data/scraped.jsonl --output-format=jsonl etl/scraper.py
```

A list of department names and vote numbers for each provincial government is produced from the EPRE chapters.

```
cat  etl-data/scraped.jsonl |grep pdf|egrep "(2015|2016|2017)"|jq -r '"\(.year),\(.geographic_region),\"\(.name)\""'|sort>etl-data/departments.csv
```

Use the "Text to columns" function of a spreadsheet program to split vote number and department name. Add column headers and save as `metadata/departments.csv`

The spreadsheet filenames don't match the PDF names which represent the department names. We also want the per-vote spreadsheet names to match the chapter PDFs because they should be viewed together.

We use `etl/normalize.py` to do the bulk of that. Since it's doing fuzzy matching, it makes mistakes, and you'll have to view the results and do some manual fixes. ***Beware that provinces have different for their departments and they can't just be normalised across provinces***.

```
pyhon etl/normalize.py
```

This writes `etl-data/scraped_normalised.csv` which you can then correct manually. The list of manual corrections should always be saved in metadata/fuzzy_normalisation_fixes.csv

We then save `etl-data/scraped_normalised.csv` as `metadata/epre_fienames.csv` and run `etl/rename.py` which will add the `department_name` and `normalised_path` columns, and copy the files from the scraped path to the normalised path.


Troubleshooting
===============

- If ckan can't connect to solr after rebuilding ckan-solr, restart ckan - I think it's something to do with docker linking the containers. I think Docker needs to link ckan to the new ckan-solr container which happens on restart.