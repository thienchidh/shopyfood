import json

import requests
from bs4 import BeautifulSoup

import util

headers = {
    'authority': 'food.grab.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'vi',
    'dnt': '1',
    'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
}


def extract_json_data(scripts):
    print('scripts.length', len(scripts))
    for script in scripts:
        print('script.text', script.text)
        json_load = json.loads(script.text)
        if util.safe_get(json_load, ['@type']) == "Restaurant":
            return json_load

    return None


def is_support_url(url):
    return url.startswith('https://food.grab.com/')


def process(url):
    print('process', url)
    response = requests.get(url, headers=headers)

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all the script have class "next-head" and type "application/ld+json"
    scripts = soup.find_all('script', {'type': 'application/ld+json'})

    json_data = extract_json_data(scripts)

    title = util.safe_get(json_data, ['name'])
    items = []

    values = util.get_values_by_key(json_data, '@type', lambda v: v == 'MenuItem')

    for value in values:
        if not value['available']:
            continue

        item = {
            'name': util.safe_get(value, ['name']),
            'price': util.safe_get(value, ['offers', 'price'])
        }
        items.append(item)

    return "[Grab] " + title, items
