"""
Brings a CKAN instance up to date with the datasets/resources defined in a CSV file.

Expects the following columns:

dataset_title
dataset_unique_name
dataset_url
dataset_description
resource_title
resource_url

"""

from ckanapi import RemoteCKAN, ValidationError
from ckanapi.errors import NotFound
import argparse
import csv
import sys
import os
from util import get_vocab_map

parser = argparse.ArgumentParser(description='Bring CKAN up to date with a local representation of a set of datasets')

parser.add_argument('--apikey', help='authentication key')
parser.add_argument('--instance', help='CKAN instance root URL')
parser.add_argument('--resources-file', help='CSV with resource data')
parser.add_argument('--dataset-category', help='Category of the datasets')

args = parser.parse_args()

ckan = RemoteCKAN(args.instance, apikey=args.apikey)


def sync_package(package_fields):
    print "Syncing %s" % package_fields['name'] or package_fields['title']
    try:
        package = ckan.action.package_create(**package_fields)
        return package
    except ValidationError, e:
        if e.error_dict.get(u'id', None) == [u'Dataset id already exists'] or \
           e.error_dict.get(u'name', None) == [u'That URL is already in use.']:
            print "Package exists. Updating."
            package = ckan.action.package_patch(**package_fields)
            return package
        else:
            raise e


with open(args.resources_file) as csvfile:
    reader = csv.DictReader(csvfile)
    vocabs = get_vocab_map(ckan)

    for row in reader:
        package_fields = {
            'id': row['dataset_unique_name'],
            'name': row['dataset_unique_name'],
            'title': row['dataset_title'],
            'notes': row['dataset_description'],
            'url': row['dataset_url'],
            'tags': [
                {'vocabulary_id': vocabs['categories'],
                 'name': args.dataset_category},
            ],
            'owner_org': 'national-treasury',
        }
        package = sync_package(package_fields)

        resource_fields = {
            'package_id': package['id'],
            'url': row['resource_url'],
            'name': row['resource_title'],
        }
        resources = package['resources']
        matches = [r for r in resources if r['name'] == row['resource_title']]

        if matches:
            print "Resource %s exists. Updating." % row['resource_title']
            resource_fields['id'] = matches[0]['id']
            ckan.action.resource_patch(**resource_fields)
        else:
            print "Creating resource %s" % row['resource_title']
            ckan.action.resource_create(**resource_fields)
