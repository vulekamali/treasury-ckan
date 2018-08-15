from ckanapi import RemoteCKAN
from collections import defaultdict

import argparse

parser = argparse.ArgumentParser(description='Bring CKAN up to date with a local representation of a set of datasets')

parser.add_argument('--apikey', help='authentication key')
parser.add_argument('--instance', help='CKAN instance root URL')
parser.add_argument('--count-formats', default=False, action='store_true', help='Count the number of non-uploaded files in each format')

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
