from ckanapi import RemoteCKAN, ValidationError
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
parser.add_argument('--resources-file', help='CSV with resource data')
parser.add_argument('--resources-base', help='base local directory for resource files')

args = parser.parse_args()

ckan = RemoteCKAN('https://treasurydata.openup.org.za', apikey=args.apikey)

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


def group_id(geographic_region, financial_year):
    return slugify('%s province %s' % (
        prov_abbrev[geographic_region], finyear[financial_year]))


def package_id(geographic_region, department_name, financial_year):
    short_dept = slugify(department_name, max_length=85, word_boundary=True)
    return slugify('prov dept %s %s %s' % (
        prov_abbrev[geographic_region], short_dept, finyear[financial_year]))


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
            geographic_region = row['geographic_region']
            financial_year = row['year']
            department_name = row['department_name']
            pid = package_id(geographic_region, department_name, financial_year)
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
            financial_year = row['financial_year']
            dept_name = row['department_name']
            pid = package_id(geo_region, dept_name, financial_year)
            title = "%s Department: %s %s" % (geo_region, dept_name, finyear[financial_year])
            print pid
            print title
            package_fields = {
                'id': pid,
                'name': pid,
                'title': title,
                'license_id': 'other-pd',
                'groups': [{'name': group_id(geo_region, financial_year)}],
                'tags': [
                    { 'vocabulary_id': vocab_map['spheres'],
                      'name': 'Provincial' },
                    { 'vocabulary_id': vocab_map['financial_years'],
                      'name': finyear[financial_year] },
                    { 'vocabulary_id': vocab_map['provinces'],
                      'name': geo_region },
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
            try:
                package = ckan.action.package_create(**package_fields)
                print package
            except ValidationError, e:
                if e.error_dict[u'name'] == [u'That URL is already in use.']:
                    print "Package exists. Updating."
                    package = ckan.action.package_patch(**package_fields)
                    print package
                else:
                    print e


if 'sync-groups' in args.tasks:
    df_depts = pd.read_csv('metadata/departments.csv')
    years = set(df_depts['financial_year'].tolist())
    geographic_regions = set(df_depts['geographic_region'].tolist())
    for year in years:
        financial_year = finyear[str(year)]
        for region in geographic_regions:
            gid = group_id(region, str(year))
            title = "%s Province %s" % (region, financial_year)
            extras=[
                { 'key': 'Geographic Region', 'value': region },
                { 'key': 'Financial Year', 'value': financial_year },
            ]
            group = ckan.action.group_create(
                name=gid,
                title=title,
                extras=extras,
            )
            print group
