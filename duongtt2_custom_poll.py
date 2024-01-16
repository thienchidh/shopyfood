import json

import requests
from bs4 import BeautifulSoup

import util

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'vi,en;q=0.9,und;q=0.8,mt;q=0.7',
    'dnt': '1',
    'origin': 'https://food.grab.com',
    'referer': 'https://food.grab.com/',
    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
}


def extract_json_data(scripts):
    for script in scripts:
        print('script.text', script.text)
        json_load = json.loads(script.text)
        if util.safe_get(json_load, ['@type']) == "Restaurant":
            return json_load

    return None


def is_support_url(url):
    return url.startswith('6f3325')


def process(url):
    print('process duongtt2', url)

    # Parse the HTML content of the page

    # Find all the script have class "next-head" and type "application/ld+json"

    title = "Cà Phê Kem"
    items = []

    item = {
        'name': "Muối đắng",
        'price': "18,000đ",
        'price_value': 18,
    }
    items.append(item)

    item = {
        'name': "Muối ngọt",
        'price': "18,000đ",
        'price_value': 18,
    }
    items.append(item)

    item = {
        'name': "Bạc xỉu",
        'price': "18,000đ",
        'price_value': 18,
    }
    items.append(item)


    item = {
        'name': "Kem trứng",
        'price': "20,000đ",
        'price_value': 20,
    }
    items.append(item)

    item = {
        'name': "Trà astiso",
        'price': "23,000đ",
        'price_value': 23,
    }
    items.append(item)


    item = {
        'name': "Bạc xỉu kem muối",
        'price': "21,000đ",
        'price_value': 21,
    }
    items.append(item)


    item = {
        'name': "Bạc xỉu kem trứng",
        'price': "23,000đ",
        'price_value': 23,
    }
    items.append(item)

    item = {
        'name': "Chocolate Mint",
        'price': "23,000đ",
        'price_value': 23,
    }
    items.append(item)


    item = {
        'name': "Cacao Kem Trứng",
        'price': "23,000đ",
        'price_value': 23,
    }
    items.append(item)

    item = {
        'name': "Trà xoài chanh leo",
        'price': "23,000đ",
        'price_value': 23,
    }
    items.append(item)


    item = {
        'name': "Trà ổi hồng",
        'price': "23,000đ",
        'price_value': 23,
    }
    items.append(item)


    # unique items
    items = list({v['name']: v for v in items}.values())

    return "[CaFe] " + title, items, None


if __name__ == '__main__':
    url = 'https://food.grab.com/vn/vi/restaurant/ch%C3%A8-53-ph%E1%BA%A1m-h%E1%BB%93ng-th%C3%A1i-delivery/VNGFVN000008hv'
    result = process(url)
    print(result)
