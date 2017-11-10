import csv
from os import path, makedirs
from shutil import copyfile
import re

with open('metadata/epre_filenames.csv') as from_path_file:
    with open('etl-data/epre_filenames.csv', 'wb') as both_paths_file:
        reader = csv.DictReader(from_path_file)
        items = list(reader)
        fieldnames = sorted(items[0].keys() + ['normalised_path'])
        writer = csv.DictWriter(both_paths_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in items:
            if row['path']:
                from_dirname = path.dirname(row['path'])
                to_dirname = from_dirname.replace('etl-data', 'etl-data/normalised')
                if not path.exists(to_dirname):
                    makedirs(to_dirname)
                extension = path.splitext(row['path'])[1]
                to_path = '%s/%s%s' % (to_dirname, row['name'], extension)
                copyfile(row['path'], to_path)
                row['normalised_path'] = to_path
            row['department_name'] = re.sub('Vote \d+ : ', '', row['name'])
            writer.writerow(row)
copyfile('etl-data/epre_filenames.csv', 'metadata/epre_filenames.csv')
