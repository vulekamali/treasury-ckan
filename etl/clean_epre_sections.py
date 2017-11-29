import regex as re
import csv
import os
import yaml


basedir = '../data/provincial/temps'

count = 0

incompletes = set()
with open('../data/provincial/temps/missing.csv') as missings_file:
    reader = csv.DictReader(missings_file)
    for row in reader:
        incompletes.add(os.path.join(basedir, row['text_file']))


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

                            regex = r"^\s*(?:# *(?P<heading>[\w ]+)[\r\n]+(?P<content>[^#]+))+\s*$"
                            match = re.match(regex, content, flags=re.MULTILINE)
                            if match:
                                for capture in match.captures():
                                    print "%r" % capture
                                count += 1
                                print count
                            else:
                                print "%s" % content
                                if file_path in incompletes:
                                    print "#### known incomplete"
                                else:
                                    print os.path.join(year, geographic_region, filename)
                                    print
                                    raise Exception("%r" % file_path)
