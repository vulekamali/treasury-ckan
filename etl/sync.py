from ckanapi import RemoteCKAN, ValidationError
from ckanapi.errors import NotFound
import argparse
import csv
import sys
import os
from slugify import slugify
import pandas as pd
from util import merge


parser = argparse.ArgumentParser(description='Bring CKAN up to date with a local representation of what it should look like.')
parser.add_argument('tasks', metavar='task', type=str, nargs='+',
                    help='tasks to run')
parser.add_argument('--apikey', help='authentication key')
parser.add_argument('--instance', help='CKAN instance root URL')
parser.add_argument('--resources-file', help='CSV with resource data')
parser.add_argument('--resources-base', help='base local directory for resource files')

args = parser.parse_args()

ckan = RemoteCKAN(args.instance, apikey=args.apikey)

finyear = {
    '2015': '2015-16',
    '2016': '2016-17',
    '2017': '2017-18',
}

prov_abbrev = {
    'Eastern Cape': 'EC',
    'Free State': 'FS',
    'Gauteng': 'GT',
    'KwaZulu-Natal': 'NL',
    'Limpopo': 'LP',
    'Mpumalanga': 'MP',
    'Northern Cape': 'NC',
    'North West': 'NW',
    'Western Cape': 'WC',
}

packagecache = {}


def group_id(sphere, geographic_region, financial_year):
    if sphere == 'provincial':
        return slugify('%s province %s' % (
            prov_abbrev[geographic_region], financial_year))
    elif sphere == 'national':
        return slugify('national %s' % financial_year)
    else:
        raise Exception('unknown sphere %r' % sphere)


def group_title(sphere, geographic_region, financial_year):
    if sphere == 'provincial':
        return "%s Province %s" % (geographic_region, financial_year)
    elif sphere == 'national':
        return 'National %s' % financial_year
    else:
        raise Exception('unknown sphere %r' % sphere)


def package_id(sphere ,geographic_region, department_name, financial_year):
    if sphere == 'provincial':
        short_dept = slugify(department_name, max_length=85, word_boundary=True)
        return slugify('prov dept %s %s %s' % (
            prov_abbrev[geographic_region], short_dept, financial_year))
    elif sphere == 'national':
        short_dept = slugify(department_name, max_length=96, word_boundary=True)
        return slugify('nat dept %s %s' % (short_dept, financial_year))
    else:
        raise Exception('unknown sphere %r' % sphere)

def package_title(sphere ,geographic_region, department_name, financial_year):
    if sphere == 'provincial':
        return "%s Department: %s %s" % (geo_region, dept_name, financial_year)
    elif sphere == 'national':
        return "National Department: %s %s" % (dept_name, financial_year)
    else:
        raise Exception('unknown sphere %r' % sphere)



def get_vocab_map():
    vocab_map = {}
    for vocab in ckan.action.vocabulary_list():
        vocab_map[vocab['name']] = vocab['id']
    return vocab_map


if 'upload-resources' in args.tasks:
    with open(args.resources_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print
            sphere = row['sphere']
            geographic_region = row['geographic_region']
            financial_year = finyear[row['financial_year']]
            department_name = row['department_name']
            pid = package_id(sphere, geographic_region, department_name, financial_year)
            print pid
            package = packagecache.get(pid, None)
            if not package:
                package = ckan.action.package_show(id=pid)
                packagecache[pid] = package
            resources = package['resources']
            matches = [r for r in resources if r['name'] == row['name']]
            print row['name'], row['normalised_path']
            if matches:
                print 'Resource Exists'
            else:
                if row['url']:
                    print ckan.action.resource_create(
                        package_id=pid,
                        url=row['url'],
                        name=row['name'],
                    )
                else:
                    path = args.resources_base + row['path']
                    noextension, extension = os.path.splitext(path)
                    print ckan.action.resource_create(
                        package_id=pid,
                        name=row['name'],
                        upload=open(path, 'rb')
                    )

if 'sync-packages' in args.tasks:
    with open('metadata/departments.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        vocab_map = get_vocab_map()

        for row in reader:
            geo_region = row['geographic_region']
            year_int = row['financial_year']
            financial_year = finyear[str(year_int)]
            dept_name = row['department_name']
            sphere = row['sphere']
            pid = package_id(sphere, geo_region, dept_name, financial_year)
            title = package_title(sphere, geo_region, dept_name, financial_year)
            print pid
            print title
            package_fields = {
                'id': pid,
                'name': pid,
                'title': title,
                'license_id': 'other-pd',
                'groups': [{'name': group_id(sphere, geo_region, financial_year)}],
                'tags': [
                    { 'vocabulary_id': vocab_map['spheres'],
                      'name': sphere },
                    { 'vocabulary_id': vocab_map['financial_years'],
                      'name': financial_year },
                ],
                'extras': [
                    { 'key': 'department_name', 'value': dept_name },
                    { 'key': 'Department Name', 'value': dept_name },
                    { 'key': 'department_name_slug', 'value': slugify(dept_name) },
                    { 'key': 'Vote Number', 'value': row['vote_number'] },
                    { 'key': 'vote_number', 'value': row['vote_number'] },
                    { 'key': 'geographic_region_slug', 'value': slugify(geo_region) },
                ],
                'owner_org': 'national-treasury'
            }
            if sphere == 'provincial':
                package_fields['tags'].append({
                    'vocabulary_id': vocab_map['provinces'],
                    'name': geo_region
                })
            else:
                package_fields['province'] = []
            try:
                package = ckan.action.package_create(**package_fields)
                print package
            except ValidationError, e:
                if e.error_dict.get(u'id', None) == [u'Dataset id already exists'] or \
                   e.error_dict.get(u'name', None) == [u'That URL is already in use.']:
                    print "Package exists. Updating."
                    package = ckan.action.package_patch(**package_fields)
                    print package
                else:
                    print e

if 'create-groups' in args.tasks:
    cols = ['financial_year', 'geographic_region', 'sphere']
    df_depts = pd.read_csv('metadata/departments.csv', usecols=cols)
    df_depts = df_depts.drop_duplicates()
    for index, row in df_depts.iterrows():
        year_int = row['financial_year']
        financial_year = finyear[str(year_int)]
        geographic_region = row['geographic_region']
        sphere = row['sphere']
        gid = group_id(sphere, geographic_region, financial_year)
        print gid

        group_fields = {
            'id': gid,
            'name': gid,
            'title': group_title(sphere, geographic_region, financial_year),
            'extras': [
                {'key': 'Sphere', 'value': sphere},
                {'key': 'Geographic Region', 'value': geographic_region},
                {'key': 'Financial Year', 'value': financial_year},
            ],
        }
        try:
            ckan.action.group_show(id=gid)
            print "Not recreating group"
        except NotFound:
            group = ckan.action.group_create(**group_fields)
            print group
        print
