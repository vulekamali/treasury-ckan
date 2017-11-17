import json
import subprocess
import os
import regex as re
import pprint
import string
import csv


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


overview_matcher = re.compile(r'\n(?:1\.)?\s*Overview\n\s*(?P<overview_content>.+)(?:Review of the current financ(?:ial|e) year|$)', flags=re.DOTALL + re.IGNORECASE)

wanted_headings = [
    'Broad policies, priorities and strategic goals',
    'Core functions and responsibilities',
    'Core functions and responsibilities',
    'Core functions',
    'Core Functions of the Department',
    'Core values',
    'Demands and changes in services',
    'Demand for services',
    'Departmental Structure',
    'Functions of the Department',
    'Goals',
    'Main services',
    'Main Services and Core functions',
    'Mission',
    'Mission statement',
    'Mission and strategic goals',
    'Other roles',
    'Overview of the main services that the department intends to deliver',
    'Strategic Goals',
    'Strategic Objectives',
    'Values',
    'Vision',
]
headings = [
    'Acts, Rules and Regulations',
    'Broad policies, priorities and strategic goals',
    'Broad Policies and Legislative Mandates'
    'Consititutional mandates',
    'Core functions and responsibilities',
    'Core functions',
    'Core values',
    'Demands and changes in services',
    'Demand for and changes in the services',
    'Demand for services',
    'Departmental Structure',
    'External activities and other events relevant to budget decisions',
    'Functions of the Department',
    'Goals',
    'Legal mandates',
    'Legislative and other mandates',
    'Legislative mandate',
    'Legislative mandates',
    'Legislation',
    'Mandate of the department',
    'Main services',
    'Main Services and Core functions',
    'Main services to be delivered',
    'Mission',
    'Mission statement',
    'Mission and strategic goals',
    'Other roles',
    'Overview of the main services that the department intends to deliver',
    'Policy mandates',
    'Services Rendered',
    'Strategic Goals',
    'Strategic Objectives',
    'Strategic Policy Directions',
    'The role',
    'Values',
    'Vision',
]
headings_regex = '(?:%s)(?: of (\w{2,20}| ){1,9})?\n' % '|'.join(headings)
subsection_match_regex = r'^(\n[]*%s.+?)+$' % headings_regex
subsection_split_regex = r'^(?:\n[]*(?P<heading>%s)(?P<content>.+?))+$' % headings_regex
subsection_matcher = re.compile(subsection_match_regex, flags=re.DOTALL + re.IGNORECASE)
subsection_splitter =  re.compile(subsection_split_regex, flags=re.DOTALL + re.IGNORECASE)

print subsection_split_regex

def text_to_markdown(basename, txt_filename, item):
    print "text_to_markdown(%r, %r)" % (basename, txt_filename)
    dirname = "%s_markdown" % basename
    found_subsections = False

    with open(txt_filename) as txt_file:
        text = txt_file.read()
        match = overview_matcher.search(text)
        file_metadata = []
        if match:
            overview_content = match.group('overview_content')
            subsection_matches = subsection_matcher.match('\n' + overview_content)
            if subsection_matches:
                for idx, subsection in enumerate(subsection_matches.captures(1), start=1):
                    split_subsection = subsection_splitter.match(subsection)
                    heading = split_subsection.group('heading').strip()
                    if any([w.startswith(heading) for w in wanted_headings]):
                        section_markdown = clean_text(split_subsection.group('content'))

                        if not os.path.exists(dirname):
                            os.makedirs(dirname)
                        filename = "%s/%s-%s.md" % (dirname, idx, heading)
                        with open(filename, 'wb') as outfile:
                            outfile.write(section_markdown)
                        found_subsections = True

                        file_metadata.append({
                            'path': filename,
                            'year': item['year'],
                            'geographic_region': item['geographic_region'],
                            'index': idx,
                            'heading': heading,
                        })
            else:
                print "-------------------------"
                print "| No subsection matches |"
                print "-------------------------"
        else:
            print "========== Overview section not found =========="
    return dirname, found_subsections, file_metadata


page_number_regex = r'\n\s*\d+\s*\n'
page_number_matcher = re.compile(page_number_regex)
broken_line_regex = r'([a-z,])\s+([a-z0-9])'
broken_line_matcher = re.compile(broken_line_regex, flags=re.DOTALL)
new_para_regex = r'(\w)\n+([A-Z0-9])'
new_para_matcher = re.compile(new_para_regex, flags=re.DOTALL)
list_item_regex = r'\n\s*[^\w](\s+)(\w+)'
list_item_matcher = re.compile(list_item_regex)
bullet_regex = r'\n(\s*)[oe* -]+\s+(\w+)'
bullet_matcher = re.compile(bullet_regex)
stray_bullet_regex = r'\s+e\s+'
stray_bullet_matcher = re.compile(stray_bullet_regex)
printable = set(string.printable)
header_regex = '^.{0,20}Estimates of Provincial Revenue and Expenditure.{0,20}$'
header_matcher = re.compile(header_regex, flags=re.MULTILINE)


def clean_text(content):
    content = header_matcher.sub('', content)
    content = page_number_matcher.sub('\n', content)
    content = broken_line_matcher.sub('\\1 \\2', content)
    content = list_item_matcher.sub('\n\\1- \\2', content)
    content = new_para_matcher.sub('\\1\n\n\\2', content)
    content = bullet_matcher.sub('\n\\1- \\2', content)
    content = bullet_matcher.sub('\n- ', content)
    content = filter(lambda x: x in printable, content)

    return content


with open('etl-data/scraped.jsonl') as scraped_file:
    with open('etl-data/epre_text.csv', 'wb') as outfile:
        fieldnames = ['path', 'year', 'geographic_region', 'index', 'heading']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for line in scraped_file.readlines():
            item = json.loads(line)
            if item.get('path', '').endswith('.pdf'):
                if '2015/KwaZulu-Natal/Vote 10 : The Royal Household.pdf' in item['path']:
                    continue

                original_filename = item['path']
                original_filename_noext = os.path.splitext(original_filename)[0]

                filename_p1_3 = extract_pages(original_filename_noext)

                txt_filename = extract_text(original_filename_noext, original_filename)

                markdown_folder, found_subsections, file_metadata \
                    = text_to_markdown(original_filename_noext, txt_filename, item)
                print markdown_folder
                print "%s wanted subsections found in original PDF" % len(file_metadata)

                if False: #len(file_metadata) > 1:
                    writer.writerows(file_metadata)
                else:
                    ocr_filename = ocr(original_filename_noext, filename_p1_3)

                    ocr_filename_noext = os.path.splitext(ocr_filename)[0]
                    ocr_txt_filename = extract_text(ocr_filename_noext, ocr_filename)

                    markdown_folder, found_subsections, file_metadata \
                        = text_to_markdown(original_filename_noext, ocr_txt_filename, item)
                    print markdown_folder

                    print "%s wanted subsections found in OCRd PDF" % len(file_metadata)
                    writer.writerows(file_metadata)
                print
