import json

import requests

from util import get_url_with_no_params, safe_get

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'vi,en;q=0.9,und;q=0.8,mt;q=0.7,zh-CN;q=0.6,zh;q=0.5',
    'sec-ch-ua': '"Not_A Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'x-foody-access-token': '',
    'x-foody-api-version': '1',
    'x-foody-app-type': '1004',
    'x-foody-client-id': '',
    'x-foody-client-language': 'vi',
    'x-foody-client-type': '1',
    'x-foody-client-version': '3.0.0',
    'x-sap-ri': ''
}


def get_api_delivery(from_url):
    url = 'https://gappapi.deliverynow.vn/api/delivery/get_from_url?url=' + from_url

    print('get_api_delivery', url)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("Request failed with status code: ", response.status_code, response.text)
    return None


def get_api_detail(request_id):
    url = 'https://gappapi.deliverynow.vn/api/delivery/get_detail?id_type=2&request_id=' + request_id
    print('get_api_detail', url)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("Request failed with status code: ", response.status_code)
    return None


def get_api_delivery_dishes(request_id):
    url = 'https://gappapi.deliverynow.vn/api/dish/get_delivery_dishes?id_type=2&request_id=' + request_id

    print('get_api_delivery_dishes', url)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("Request failed with status code: ", response.status_code)
    return None


def get_url_with_no_base(url):
    return url.replace('https://shopeefood.vn/', '')


def is_support_url(url):
    return url.startswith('https://shopeefood.vn/')


def get_content_response(body):
    if body is None:
        return None

    if body['result'] != 'success':
        return None

    reply = body['reply']
    if reply is None:
        return None

    return reply


def process(full_url):
    url = get_url_with_no_base(full_url)
    url = get_url_with_no_params(url)

    delivery_id = safe_get(get_content_response(get_api_delivery(url)), ['delivery_id'])
    if delivery_id is None:
        return None

    response = get_content_response(get_api_detail(str(delivery_id)))
    alert_msg = safe_get(response, ['delivery_detail', 'delivery', 'delivery_alert', 'message', 'message'])
    title = safe_get(response, ['delivery_detail', 'name'])

    dishes = get_content_response(get_api_delivery_dishes(str(delivery_id)))
    menu_infos = safe_get(dishes, ['menu_infos'], [])

    items = []
    for menu_info in menu_infos:
        for dish in menu_info['dishes']:
            if not dish['is_available']:
                continue

            items.append({
                'name': dish['name'],
                'price': dish['price']['text'],
                'price_value': dish['price']['value'],
            })

    # unique items
    items = list({v['name']: v for v in items}.values())

    return "[Now] " + title, items, alert_msg

# if __name__ == '__main__':
#     response = process("https://shopeefood.vn/da-nang/tiem-an-vua-vit-quay-pham-cu-luong")
#     #https://gappapi.deliverynow.vn/api/delivery/get_from_url?url=da-nang/
#     print(response)
