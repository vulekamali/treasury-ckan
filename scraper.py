import scrapy
import urlparse
import os

REGEX_EPRE = r'\d\. Estimates of Provincial Revenue and Expenditure$'
REGEX_EPRE_VOTE_PDF = r'Vote \d.+'

class URLItem(scrapy.Item):
    year = scrapy.Field()
    jurisdiction = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()


class TreasurySpider(scrapy.Spider):
    name = 'treasury'
    start_urls = ['http://www.treasury.gov.za/documents/provincial%20budget/default.aspx']

    def parse(self, response):
        for anchor in response.css('a'):
            if anchor.xpath('text()').re('^\d{4}$'):
                year = anchor.xpath('text()').extract_first()
                url = urlparse.urljoin(response.url, anchor.xpath('@href').extract_first().strip())
                request = scrapy.Request(url, self.parse_year)
                request.meta['year'] = year
                yield request

    def parse_year(self, response):
        for anchor in response.css('a'):
            if anchor.xpath('text()').re(REGEX_EPRE):
                url = urlparse.urljoin(response.url, anchor.xpath('@href').extract_first().strip())
                request = response.request.replace(url=url, callback=self.parse_epre_provinces)
                yield request

    def parse_epre_provinces(self, response):
        dirname = os.path.dirname(urlparse.urlparse(response.url).path)
        for anchor in response.css('a'):
            url = urlparse.urljoin(response.url, anchor.xpath('@href').extract_first().strip())
            if dirname in url:
                request = response.request.replace(url=url, callback=self.parse_epre_province)
                request.meta['province'] = anchor.xpath('text()').extract_first()
                yield request

    def parse_epre_province(self, response):
        for anchor in response.css('a'):
            if anchor.xpath('text()').re(REGEX_EPRE):
                url = urlparse.urljoin(response.url, anchor.xpath('@href').extract_first().strip())
                yield response.request.replace(url=url, callback=self.parse_epre_province_chapters)

    def parse_epre_province_chapters(self, response):
        for anchor in response.css('a'):
            if anchor.xpath('text()').re(REGEX_EPRE_VOTE_PDF):
                url = urlparse.urljoin(response.url, anchor.xpath('@href').extract_first().strip())
                item = URLItem()
                item['url'] = url
                item['jurisdiction'] = response.meta['province']
                item['year'] = response.meta['year']
                item['name'] = anchor.xpath('text()').extract_first()
                yield item
