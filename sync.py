from ckanapi import RemoteCKAN
import argparse
import csv
import sys
import os

PROV_BUDGET_NOTES = "Estimates of Provincial Revenue and Expenditure (EPRE) communicates each department's budget, provides current and anticipated medium term budget trends, provide an overview of departmental estimates based on the standardised budget and programme structures for a particular sector, focuses on strategic service delivery and gives a high level overview of performance measures and targets as defined in departmental Strategic Plans and Annual Performance Plans.\n\n## Definitions of columns:\n\n### Economic Classification\nThe economic classification is defined in the [Standard Chart of Accounts (SCOA)](http://scoa.treasury.gov.za/Pages/Charts.aspx). The latest available SCOA version is used at each budget publication."

parser = argparse.ArgumentParser(description='Bring CKAN up to date with a local representation of what it should look like.')
parser.add_argument('tasks', metavar='task', type=str, nargs='+',
                    help='tasks to run')
parser.add_argument('--apikey', help='authentication key')
parser.add_argument('--resources-file', help='CSV with resource data')
parser.add_argument('--resources-base', help='base local directory for resource files')


args = parser.parse_args()

ckan = RemoteCKAN('https://treasurydata.openup.org.za', apikey=args.apikey)

provinces = [
    'Eastern Cape',
    'Free State',
    'Gauteng',
    'KwaZulu-Natal',
    'Limpopo',
    'Mpumalanga',
    'Northern Cape',
    'North West',
    'Western Cape',
]

finyear = {
    '2015': '2015-16',
    '2016': '2016-17',
    '2017': '2017-18',
}

packagecache = {}

def package_id(province, year):
    return '%s-provincial-budget-%s' % (province.lower().replace(' ', '-'), year)


if 'upload-resources' in args.tasks:
    with open(args.resources_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print
            print row['jurisdiction'], row['year'], row['name']
            pid = package_id(row['jurisdiction'], finyear[row['year']])
            package = packagecache.get(pid, None)
            if not package:
                package = ckan.action.package_show(id=pid)
                packagecache[pid] = package
            resources = package['resources']
            matches = [r for r in resources if r['name'] == row['name']]
            if matches:
                print 'YES'
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
                    if extension == '.xlsx':
                        xlsmpath = noextension + '.xlsm'
                        if os.path.isfile(xlsmpath):
                            path = xlsmpath
                    print ckan.action.resource_create(
                        package_id=pid,
                        name=row['name'],
                        upload=open(path, 'rb')
                    )

if 'update-packages' in args.tasks:
    for province in provinces[0:]:
        for year in finyear.values()[0:]:
            pid = package_id(province, year)
            print pid
            package = ckan.action.package_show(id=pid)
            package['notes'] = PROV_BUDGET_NOTES
            package['resources'] = []
            ckan.action.package_update(**package)
