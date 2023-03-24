from datetime import datetime, timedelta
import random
import string
from logger import logger
import CONST
import hashlib
import time
from all_get_repo_func import *

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


def save_data_user_name(repo, effective_user_id, effective_user):
    chat_id_names = repo.compute_if_absent('chat_id_names', lambda k: dict())
    chat_id_names[effective_user_id] = f'@{effective_user.username}'
    repo.save()
    pass
    
def save_data_for_quiz(update, context, message, question, poll_type):
    msg_poll_id = f'{message.message_id}'
    logger.info(f'msg_poll_id : {msg_poll_id}')
    logger.info(f'message.poll.id : {message.poll.id}')
    repo = get_repo_bot(context)
    poll_data = dict()
    payload =  {
        message.poll.id: {
            "timestamp": time.time(),
            "chat_id": update.effective_chat.id,   
            "message_id": message.message_id,
            "user_answers": {},
            "poll_type": poll_type,
            "question": question["question"],
            "options": question["answers"],
            "correct_options_id": question["correct"]      
            }
    }
    variable_question = question["question"]
    string_md5_question = hashlib.md5(variable_question.encode()).hexdigest()
    all_quiz_info_in_one = repo.compute_if_absent("all_quiz_info_in_one", lambda k: dict())
    payload_quiz_info = {
                string_md5_question: {
                    "timeline_create": [
                        {
                            "poll_id": message.poll.id,
                            "user_answer_correct": [],
                            "user_answer_wrong": []
                        }
                    ]
                }
            }
    all_quiz_info_in_one.update(payload_quiz_info)       
    poll_data.update(payload)
    all_poll_data = repo.compute_if_absent("poll_data", lambda k: dict())
    all_poll_data.update(poll_data)
    repo.save()

def get_datetime_at_midnight():
    date_now = datetime.now()
    datetime_midnight = datetime(date_now.year, date_now.month, date_now.day, 0, 0)
    return datetime_midnight.strftime("%Y-%b-%d") 

def get_datetime_at_midnight_and_add_days(days):
    date_now = datetime.now()
    datetime_midnight = datetime(date_now.year, date_now.month, date_now.day, 0, 0)
    datetime_cal = datetime_midnight + timedelta(days=days)
    return datetime_cal.strftime("%Y-%b-%d")
     

