import re
import csv
import os
import yaml


basedir = '../data/provincial/temps'


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
                            file_text = text_file.read()
                            front_matter, content = file_text.split("---")
                            front_matter = front_matter.strip()
                            metadata = {}
                            print
                            print "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"
                            print file_path
                            for line in front_matter.split("\n"):
                                key, value = line.split(":", 1)
                                metadata[key] = value
                            print metadata
                            print content[:100]
