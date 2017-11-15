from ckanapi import RemoteCKAN
import requests

ckan = RemoteCKAN('https://treasurydata.openup.org.za')

response = ckan.action.resource_search(query="url:treasury.gov.za")

with open('etl-data/broken_links.csv', 'wb') as broken_links_file:
    for resource in response['results']:
        r = requests.head(resource['url'])
        if r.status_code == 302:
            print "BAD %s" % resource['url']
            broken_links_file.write(resource['url'] + '\n')
        elif r.status_code == 200:
            print "GOOD"
        else:
            print r
