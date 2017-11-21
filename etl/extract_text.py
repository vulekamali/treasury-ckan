# https://stackoverflow.com/questions/699468/python-html-sanitizer-scrubber-filter

from bs4 import BeautifulSoup
import re


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


with open('etl-data/2017/National/html/Vote 11 Public Works.html') as chapter_html_file:
    chapter_html = chapter_html_file.read()
    bs_html = BeautifulSoup(chapter_html, 'lxml')

    headings = list(bs_html.find_all('h2'))
    heading = headings.pop(0)
    for next_heading in headings:
        heading_text = clean_whitespace(heading.text)

        if heading_text not in WANTED_HEADINGS:
            heading = next_heading
            continue

        if clean_whitespace(heading.text) == 'Selected performance indicators':
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

        print "## " + heading_text
        print
        print ">>>> " + section_soup.renderContents()

        heading = next_heading
