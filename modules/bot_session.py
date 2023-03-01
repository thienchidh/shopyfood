cache_data = {}

def create_data(chat_id, sample):
    if chat_id in cache_data:
        return False
    cache_data[chat_id] = sample
    return True

def get_data(chat_id):
    if chat_id in cache_data:
        return cache_data[chat_id]
    return None

def clear_data(chat_id):
    del cache_data[chat_id]