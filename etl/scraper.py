import os
import scrapy
import urllib
import urlparse
import zipfile


REGEX_EPRE = r'\d\. Estimates of Provincial Revenue and Expenditure$'
REGEX_EPRE_XLS_ROOT = r'\d\. Estimates of Provincial Revenue and Expenditure standardised tables in Excel format'
REGEX_EPRE_VOTE_PDF = r'Vote \d.+'


class URLItem(scrapy.Item):
    year = scrapy.Field()
    jurisdiction = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()


class FileItem(scrapy.Item):
    year = scrapy.Field()
    jurisdiction = scrapy.Field()
    path = scrapy.Field()
    name = scrapy.Field()


class TreasurySpider(scrapy.Spider):
    name = 'treasury'
    start_urls = ['http://www.treasury.gov.za/documents/provincial%20budget/default.aspx']

    def parse(self, response):
        for anchor in response.css('a'):
            if anchor.xpath('text()').re('^\d{4}$'):
                year = anchor.xpath('text()').extract_first().strip()
                url = abs_url(response, anchor)
                request = scrapy.Request(url, self.parse_year)
                request.meta['year'] = year
                yield request

    def parse_year(self, response):
        for anchor in response.css('a'):
            if anchor.xpath('text()').re(REGEX_EPRE):
                url = abs_url(response, anchor)
                request = response.request.replace(url=url, callback=self.parse_epre_provinces)
                yield request

            if anchor.xpath('text()').re(REGEX_EPRE_XLS_ROOT):
                url = abs_url(response, anchor)
                request = response.request.replace(url=url, callback=self.parse_epre_xls_provinces)
                yield request

    def parse_epre_provinces(self, response):
        dirname = os.path.dirname(urlparse.urlparse(response.url).path)
        for anchor in response.css('a'):
            url = abs_url(response, anchor)
            if dirname in url:
                request = response.request.replace(url=url, callback=self.parse_epre_province)
                request.meta['province'] = anchor.xpath('text()').extract_first().strip()
                yield request

    def parse_epre_xls_provinces(self, response):
        dirname = os.path.dirname(urlparse.urlparse(response.url).path)
        for anchor in response.css('a'):
            url = abs_url(response, anchor)
            if dirname in url:
                label = anchor.xpath('text()').extract_first().strip()
                if url.endswith('.zip') and 'dataset' not in label.lower():
                    province = label
                    directory = os.path.join('etl-scraped', response.meta['year'], province)
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    filename = os.path.join(directory, 'epre-xls.zip')
                    if not os.path.isfile(filename):
                        urllib.urlretrieve(url, filename)
                    zip_ref = zipfile.ZipFile(filename, 'r')
                    zip_ref.extractall(directory)
                    zip_ref.close()
                    for filename in os.listdir(directory):
                        name, extension = os.path.splitext(filename)
                        if extension in ('.xls', '.xlsx', '.xlsm'):
                            item = FileItem()
                            item['path'] = os.path.join(directory, filename)
                            item['jurisdiction'] = province
                            item['year'] = response.meta['year']
                            item['name'] = filename
                            yield item

    def parse_epre_province(self, response):
        for anchor in response.css('a'):
            if anchor.xpath('text()').re(REGEX_EPRE):
                url = abs_url(response, anchor)
                yield response.request.replace(url=url, callback=self.parse_epre_province_chapters)

    def parse_epre_province_chapters(self, response):
        for anchor in response.css('a'):
            if anchor.xpath('text()').re(REGEX_EPRE_VOTE_PDF):
                url = abs_url(response, anchor)
                item = URLItem()
                item['url'] = url
                item['jurisdiction'] = response.meta['province']
                item['year'] = response.meta['year']
                item['name'] = anchor.xpath('text()').extract_first().strip()
                yield item


def abs_url(response, anchor):
    return urlparse.urljoin(response.url, anchor.xpath('@href').extract_first().strip())
