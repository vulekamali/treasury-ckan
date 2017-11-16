import json
import subprocess
import os

with open('etl-data/scraped.jsonl') as jsonfile:
    for line in jsonfile.readlines():
        item = json.loads(line)
        if item.get('path', '').endswith('.pdf'):
            original_filename = item['path']
            original_filename_noext, extension = os.path.splitext(original_filename)

            filename_p1_3 = "%s-p1-3" % original_filename_noext
            if os.path.isfile(filename_p1_3):
                print "File exists: %s" % filename_p1_3
            else:
                split_cmd = ['pdftk', original_filename, 'cat', '1-3', 'output', filename_p1_3]
                print split_cmd
                exit_code = subprocess.call(split_cmd)
                if exit_code:
                    raise Exception("Exit code 1 for command %r" % split_cmd)
            print

            ocr_filename = "%s-OCRd.pdf" % filename_p1_3
            if os.path.isfile(ocr_filename):
                print "File exists: %s" % ocr_filename
            else:
                print "Doesn't exists: %s" % ocr_filename

                ocr_cmd = "etl/ocr-pdf '%s'" % filename_p1_3
                print ocr_cmd
                exit_code = subprocess.call(ocr_cmd, shell=True)
                if exit_code:
                    raise Exception("Exit code 1 for command %r" % ocr_cmd)
            print

            txt_filename = "%s.txt" % original_filename_noext
            if os.path.isfile(txt_filename):
                print "File exists: %s" % txt_filename
            else:
                ocr_cmd = ["pdftotext", ocr_filename, txt_filename]
                print ocr_cmd
                exit_code = subprocess.call(ocr_cmd)
                if exit_code:
                    raise Exception("Exit code 1 for command %r" % txt_cmd)
            print

            print
