from ckanapi import RemoteCKAN
from collections import defaultdict
from tempfile import mkdtemp

import argparse
import requests
import os
import urlparse
import urllib

upload_formats = [
    'CSV',
    'PDF',
    'XLS',
    'XLSB',
    'XLSM',
    'XLSX',
]


def download_file(url):
    tempdir = mkdtemp(prefix="budgetportal")
    print "Downloading %s" % url
    basename = urllib.unquote(os.path.basename(urlparse.urlparse(url).path))
    filename = os.path.join(tempdir, basename)
    return tempdir, urllib.urlretrieve(url, filename)[0]


parser = argparse.ArgumentParser(description='Bring CKAN up to date with a local representation of a set of datasets')

parser.add_argument('--apikey', help='authentication key')
parser.add_argument('--instance', help='CKAN instance root URL')
parser.add_argument('--count-formats', default=False, action='store_true', help='Count the number of non-uploaded files in each format')
parser.add_argument('--list-urls', default=False, action='store_true', help='List the non-uploaded URLs')
parser.add_argument('--replace-urls', default=False, action='store_true', help='Replace non-uploaded resources with an uploaded version.')

args = parser.parse_args()

ckan = RemoteCKAN(args.instance, apikey=args.apikey)

resources = ckan.action.resource_search(query='name:', order_by='url_type')['results']
non_uploads = []
for resource in resources:
    if resource['url_type'] is None:
        non_uploads.append(resource)

if args.count_formats:
    print "Format counts:"
    mimetype_counts = defaultdict(int)
    for resource in non_uploads:
        mimetype_counts[resource['format']] += 1
    for format, count in mimetype_counts.iteritems():
        print format, count
    print

if args.list_urls:
    for resource in non_uploads:
        print resource['format'], resource['url']

if args.replace_urls:
    for resource in non_uploads:
        if resource['format'] in upload_formats:
            dirname, filename = download_file(resource['url'])
            print "Uploading %s" % filename
            ckan.action.resource_patch(id=resource['id'], upload=open(filename, 'rb'))
            os.remove(filename)
            os.rmdir(dirname)
