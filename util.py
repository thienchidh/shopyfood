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
