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

years = [
    '2015-16',
    '2016-17',
    '2017-18',
]

finyear = {
    '2015': '2015-16',
    '2016': '2016-17',
    '2017': '2017-18',
}

def name(province, year):
    return '%s-provincial-budget-%s' % (province.lower().replace(' ', '-'), year)

for province in provinces:
    for year in years:
        print('ckanapi -r https://treasurydata.openup.org.za -a %s action package_create name=%s title="%s Provincial Budget %s" organisation_name=treasury owner_org=national-treasury' % (
            key,
            name(province, year),
            province,
            year
        ))

print
print
print

for province in provinces:
    for year in years:
        print('ckanapi -r https://treasurydata.openup.org.za -a %s action package_update name=%s title="%s Provincial Budget %s" organisation_name=treasury owner_org=national-treasury \'financial_year:["%s"]\' '% (
            key,
            name(province, year),
            province,
            year,
            year,
        ))

print
print
print

import csv

with open('scrape_normalised_hand_fixed.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['url']:
            print('ckanapi -r https://treasurydata.openup.org.za -a %s action resource_create package_id=%s name="%s" "url=%s"'  % (
                key,
                name(row['jurisdiction'], finyear[row['year']]),
                row['name'],
                row['url'],
            ))
        else:
            print('ckanapi -r https://treasurydata.openup.org.za -a %s action resource_create package_id=%s name="%s" "upload@%s"'  % (
                key,
                name(row['jurisdiction'], finyear[row['year']]),
                row['name'],
                row['path'],
            ))
