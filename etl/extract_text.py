import json
import subprocess
import os
import regex as re
import pprint
import string


def extract_pages(basename):
    filename_p1_3 = "%s-p1-3.pdf" % basename
    if os.path.isfile(filename_p1_3):
        print "File exists: '%s'" % filename_p1_3
    else:
        command = ['pdftk', original_filename, 'cat', '1-3', 'output', filename_p1_3]
        print command
        exit_code = subprocess.call(command)
        if exit_code:
            raise Exception("Exit code %s for command %r" % (exit_code, command))
    return filename_p1_3


def ocr(basename, filename_p1_3):
    filename_p1_3_noext = os.path.splitext(filename_p1_3)[0]
    ocr_filename = "%s-OCRd.pdf" % filename_p1_3_noext
    if os.path.isfile(ocr_filename):
        print "File exists: '%s'" % ocr_filename
    else:
        print "Doesn't exists: '%s'" % ocr_filename
        return
        command = "etl/ocr-pdf '%s'" % filename_p1_3
        print command
        exit_code = subprocess.call(command, shell=True)
        if exit_code:
            raise Exception("Exit code %s for command %r" % (exit_code, command))
    return ocr_filename


def extract_text(basename, ocr_filename):
    txt_filename = "%s.txt" % basename
    if os.path.isfile(txt_filename):
        print "File exists: '%s'" % txt_filename
    else:
        command = ["pdftotext", "-layout", ocr_filename, txt_filename]
        print command
        exit_code = subprocess.call(command)
        if exit_code:
            raise Exception("Exit code %s for command %r" % (exit_code, command))
    return txt_filename


overview_matcher = re.compile(r'\n(?:1\.)?\s*Overview\n\s*(?P<overview_content>.+)(?:Review of the current financial year|$)', flags=re.DOTALL)

wanted_headings = [
    'Vision',
    'Mission',
    'Strategic Objectives',
    'Core functions and responsibilities',
]
headings = [
    'Acts, Rules and Regulations',
    'Consititutional mandates',
    'Core functions and responsibilities',
    'Core functions',
    'Demands and changes in services',
    'External activities and other events relevant to budget decisions',
    'Legislative and other mandates',
    'Legislative mandate',
    'Main services',
    'Main Services and Core functions',
    'Mission',
    'Overview of the main services that the department intends to deliver',
    'Policy mandates',
    'Strategic Objectives',
    'Vision',
]
headings_regex = '(?:%s)\n' % '|'.join(headings)
subsection_match_regex = r'^(\n[]*%s.+?)+$' % headings_regex
subsection_split_regex = r'^(?:\n[]*(?P<heading>%s)(?P<content>.+?))+$' % headings_regex
subsection_matcher = re.compile(subsection_match_regex, flags=re.DOTALL)
subsection_splitter =  re.compile(subsection_split_regex, flags=re.DOTALL + re.IGNORECASE)

print subsection_split_regex

def text_to_markdown(basename, txt_filename):
    dirname = "%s_markdown" % basename

    with open(txt_filename) as txt_file:
        text = txt_file.read()
        match = overview_matcher.search(text)
        if match:
            print
            print
            overview_content = match.group('overview_content')
            subsection_matches = subsection_matcher.match('\n' + overview_content)
            if subsection_matches:
                for subsection in subsection_matches.captures(1):
                    split_subsection = subsection_splitter.match(subsection)
                    heading = split_subsection.group('heading').strip()
                    if heading in wanted_headings:
                        print "### " + split_subsection.group('heading')
                        print
                        print clean_text(split_subsection.group('content'))
                        print "----------------------"
                print "======================================="
            else:
                print "---------------------"
                print "No subsection matches"
                print "---------------------"
                print subsection_match_regex
                #print overview_content
        else:
            print
            print
            print "========== no overview section =========="
    return dirname


broken_line_regex = r'([a-z,])\s+([a-z0-9])'
broken_line_matcher = re.compile(broken_line_regex, flags=re.DOTALL)
list_item_regex = r'\s*[^\w](\s+)(\w+)'
list_item_matcher = re.compile(list_item_regex)
printable = set(string.printable)
header_regex = '^.{0,20}Estimates of Provincial Revenue and Expenditure.{0,20}$'
header_matcher = re.compile(header_regex, flags=re.MULTILINE)


def clean_text(content):
    content = list_item_matcher.sub('', content)
    content = broken_line_matcher.sub('\\1 \\2', content)
    content = list_item_matcher.sub('\\1- \\2', content)
    content = filter(lambda x: x in printable, content)

    return content


with open('etl-data/scraped.jsonl') as jsonfile:
    for line in jsonfile.readlines():
        item = json.loads(line)
        if item.get('path', '').endswith('.pdf'):
            original_filename = item['path']
            original_filename_noext = os.path.splitext(original_filename)[0]

            filename_p1_3 = extract_pages(original_filename_noext)
            print

            ocr_filename = ocr(original_filename_noext, filename_p1_3)
            print

            ocr_filename_noext = os.path.splitext(ocr_filename)[0]
            ocr_txt_filename = extract_text(ocr_filename_noext, ocr_filename)
            txt_filename = extract_text(original_filename_noext, original_filename)
            print

            markdown_folder = text_to_markdown(original_filename, txt_filename)
            #markdown_folder = text_to_markdown(original_filename, ocr_txt_filename)
            print
