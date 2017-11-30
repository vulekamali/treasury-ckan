import regex as re
import csv
import os
import yaml


basedir = '../data/provincial/temps2'


def parse_file(text_file, epre_sections_writer):
    print
    print "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"
    print file_path

    file_text = text_file.read()
    front_matter, content = file_text.split("---")
    front_matter = front_matter.strip()
    print front_matter
    metadata = {}
    for line in front_matter.split("\n"):
        key, value = line.split(":", 1)
        metadata[key] = value.strip()
    metadata['department_name'] = metadata['name'].split(':')[1]

    #print metadata

    regex = r"^\s*(?P<section># *(?P<heading>[\w ]+)[\r\n]+(?P<content>[^#]+))+\s*$"
    match = re.match(regex, content, flags=re.MULTILINE)
    if match:
        dirlist = ['etl-data', metadata['year'], metadata['geographic_region'], metadata['name']]
        dirname = os.path.join(*dirlist)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        captures = match.capturesdict()
        for idx, section in enumerate(captures['section']):
            heading = captures['heading'][idx]
            content = captures['content'][idx]
            section_filename = os.path.join(dirname, heading + ".md")
            with open(section_filename, 'wb') as section_file:
                section_file.write(content)
            epre_sections_writer.writerow({
                'department_name': metadata['department_name'],
                'financial_year': metadata['year'],
                'sphere': 'provincial',
                'heading': heading,
                'path': section_filename,
                'geographic_region': metadata['geographic_region'],
            })
        return True
    else:
        print "%s" % content
        abstract_path = os.path.join(year, geographic_region, filename)
        if content.strip() == '':
            autoblanks.write('"%s"\n"' % abstract_path)
            print "#### blank"
            return

        if file_path in incompletes:
            print "#### known incomplete"
        else:
            print abstract_path
            print
            raise Exception("%r" % file_path)


count = 0

incompletes = set()
with open('../data/provincial/temps2/missing.csv') as missings_file:
    reader = csv.DictReader(missings_file)
    for row in reader:
        incompletes.add(os.path.join(basedir, row['text_file']))
with open('../data/provincial/temps2/autoblanks.csv') as autoblanks_file:
    reader = csv.DictReader(autoblanks_file)
    for row in reader:
        incompletes.add(os.path.join(basedir, row['text_file']))

with open('etl-data/epre_sections.csv', 'wb') as epre_sections:
    headings = [
        'department_name',
        'financial_year',
        'sphere',
        'heading',
        'path',
        'geographic_region',
    ]
    epre_sections_writer = csv.DictWriter(epre_sections, fieldnames=headings)
    epre_sections_writer.writeheader()
    with open('../data/provincial/temps2/autoblanks.csv', 'wb') as autoblanks:
        autoblanks.write("text_file\n")
        for year in os.listdir(basedir):
            if re.match(r'\d{4}', year):
                year_path = os.path.join(basedir, year)
                for geographic_region in os.listdir(year_path):
                    if re.match(r'[\w ]+', geographic_region):
                        geographic_region_path = os.path.join(year_path, geographic_region)
                        for filename in os.listdir(geographic_region_path):
                            if filename.endswith('.txt'):
                                file_path = os.path.join(geographic_region_path, filename)
                                with open(file_path) as text_file:
                                    if parse_file(text_file, epre_sections_writer):
                                        count += 1
                                        print count
