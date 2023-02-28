
from cmath import exp
import math
import re
from tkinter.messagebox import NO, QUESTION
from numpy import mat
import requests
from bs4 import BeautifulSoup
import json
import scrapy

from scrapy import Selector


data = []

name_file = "fdf.json"


class MySpider(scrapy.Spider):
    name = 'myspider'
    allowed_domains = ['example.com']
    start_urls = ['http://www.example.com']

    def start_requests(self):
        print("hello world 1")
        urls = [
            'https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-3-1003'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        # Extract data from the response using XPath selectors
        print("hello world")
        title = response.xpath('//title/text()').get()
        description = response.xpath('//meta[@name="description"]/@content').get()

        # Do something with the extracted data (e.g. save it to a database)
        # ...

        print(title)
        print(description)
        # Follow links to other pages
        for href in response.css('a::attr(href)').getall():
            yield response.follow(href, self.parse)


def main():
    print("hellow rodl 2")
    mySpider = MySpider()
    mySpider.start_requests()
    pass

if __name__ == "__main__":
    main()    
