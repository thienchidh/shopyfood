import random
import string

def get_url_with_no_params(url):
    return url.split('?')[0]


def safe_get(dict, keys, default=None):
    if dict is None:
        return default

    for key in keys:
        if key not in dict:
            return default
        dict = dict[key]
        if dict is None:
            return default

    return dict


def get_values_by_key(d, key, value_compare=None):
    values = []

    if isinstance(d, dict):
        for k, v in d.items():
            if k == key:
                if value_compare is None or value_compare(v):
                    values.append(d)
            else:
                values.extend(get_values_by_key(v, key, value_compare))
    elif isinstance(d, list):
        for item in d:
            values.extend(get_values_by_key(item, key, value_compare))
    
    return values


def generate_random_id(length=8):
    # define the set of characters to use in the random ID
    characters = string.ascii_letters + string.digits

    # generate a random ID by selecting `length` characters from the set of allowed characters
    random_id = ''.join(random.choices(characters, k=length))

    # insert dashes or spaces to make the ID more readable
    random_id = '-'.join([random_id[i:i+4] for i in range(0, len(random_id), 4)])

    return random_id 