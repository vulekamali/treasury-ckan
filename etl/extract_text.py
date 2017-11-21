# https://stackoverflow.com/questions/699468/python-html-sanitizer-scrubber-filter

from bs4 import BeautifulSoup
import re
from html2text import html2text
import csv
import os


WANTED_HEADINGS = {'Vote purpose', 'Mandate'}
whitespace_cleaner = re.compile(r'\s+')


def clean_whitespace(string):
    return whitespace_cleaner.sub(' ', string).strip()


def clean_attrs(soup):
    for tag in soup.recursiveChildGenerator():
        try:
            tag.attrs = []
        except AttributeError:
            # 'NavigableString' object has no attribute 'attrs'
            pass


VALID_TAGS = ['strong', 'em', 'p', 'ul', 'li', 'br', 'i', 'ol']


def sanitize_html(soup):
    for tag in soup.findAll(True):
        if tag.name not in VALID_TAGS:
            tag.hidden = True


def chapter_to_sections(chapter_html):
    chapter_html = chapter_html_file.read()
    bs_html = BeautifulSoup(chapter_html, 'lxml')

    headings = list(bs_html.find_all('h2'))
    heading = headings.pop(0)
    for next_heading in headings:
        heading_text = clean_whitespace(heading.text)

        if clean_whitespace(heading.text) == 'Selected performance indicators':
            break

        if heading_text not in WANTED_HEADINGS:
            heading = next_heading
            continue

        section_html = u""

        for tag in heading.next_siblings:
            if tag == next_heading:
                break
            else:
                section_html += unicode(tag)

        section_soup = BeautifulSoup(section_html, 'lxml')
        sanitize_html(section_soup)
        clean_attrs(section_soup)

        yield {
            'heading': heading_text,
            'content': html2text(unicode(section_soup)),
        }

        heading = next_heading


def ensure_file_dirs(file_path):
    dirname = os.path.dirname(file_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


with open('metadata/departments.csv') as infile:
    reader = csv.DictReader(infile)
    with open('etl-data/ene_sections.csv', 'w') as outfile:
        fieldnames = ['department_name', 'financial_year', 'sphere', 'heading', 'path']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            if row['sphere'] == 'national':
                chapter_filename = 'etl-data/%s/National/html/Vote %s %s.html' % (
                    row['financial_year'], row['vote_number'], row['department_name'])
                try:
                    with open(chapter_filename) as chapter_html_file:
                        for section in list(chapter_to_sections(chapter_html_file)):
                            section_filename = 'etl-data/%s/National/markdown/Vote %s %s/%s.md' % (
                                row['financial_year'],
                                row['vote_number'],
                                row['department_name'],
                                section['heading'],
                            )
                            ensure_file_dirs(section_filename)
                            with open(section_filename, 'wb') as section_file:
                                section_file.write(section['content'].encode('utf-8'))
                            writer.writerow({
                                'department_name': row['department_name'],
                                'financial_year': row['financial_year'],
                                'sphere': row['sphere'],
                                'heading': section['heading'],
                                'path': section_filename,
                            })
                except Exception, e:
                    print e
