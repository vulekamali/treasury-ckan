import csv
from ckanapi import RemoteCKAN
import sys

apikey = sys.argv[1]

ckan = RemoteCKAN('https://treasurydata.openup.org.za', apikey=apikey)

finyear = {
    '2015': '2015-16',
    '2016': '2016-17',
    '2017': '2017-18',
}

packagecache = {}

def packag_id(province, year):
    return '%s-provincial-budget-%s' % (province.lower().replace(' ', '-'), year)

with open('scrape_normalised_hand_fixed.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        print
        print row['jurisdiction'], row['year'], row['name']
        pid = packag_id(row['jurisdiction'], finyear[row['year']])
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
                print ckan.action.resource_create(
                    package_id=pid,
                    name=row['name'],
                    upload=open(row['path'], 'rb')
                )
