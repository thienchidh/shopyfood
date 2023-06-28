from datetime import datetime, timedelta
import random
import re
import string
from logger import logger
import CONST
import hashlib
import time
from all_get_repo_func import *
from all_repo_get_func import *

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
    date_now_time_stamp = datetime.now().timestamp()
    return get_datetime_at_midnight_at_timestamp(date_now_time_stamp)

def get_datetime_at_midnight_and_add_days(days):
    date_now = datetime.now()
    datetime_midnight = datetime(date_now.year, date_now.month, date_now.day, 0, 0)
    datetime_cal = datetime_midnight + timedelta(days=days)
    return datetime_cal.strftime("%Y-%b-%d")

def get_datetime_at_midnight_at_timestamp(timestamps):
    date_time = datetime.fromtimestamp(timestamps)
    datetime_midnight = datetime(date_time.year, date_time.month, date_time.day, 0, 0)
    return datetime_midnight.strftime("%Y-%b-%d")  

def remove_non_digits(input_string):
    """
    Removes any non-digit characters from the input string and returns the resulting string
    """
    output_string = ''.join(filter(str.isdigit, input_string))
    return output_string


def get_poll_owner_id_message_id(update, context):
    repo = get_repo_bot(context)
    message = update.effective_message.reply_to_message
    # logger.info(f"checkbill_hander update.effective_message {update.effective_message}")
    # logger.info(f"checkbill_hander update.message {update.message}")
    element_poll_history = None
    if not message or message.poll is None:
        # logger.info("checkbill_hander Poll not found")
        # logger.info(f"checkbill_handler {message}") #-> expect None
        # logger.info(f"checkbill_handler {update.message.text}")  #-> expect text
        message_text = update.message.text
        regex_message_text = r"^([^ ]+)\s([\+\-]{0,1}\d+)(.*)$"
        if message_text is not None:
            match = re.match(regex_message_text, message_text)
            if match is not None:
                part1 = match.group(1)
                part2 = match.group(2)
                if part2 is not None:
                    poll_index = int(part2)
                    # logger.info(f'message text: {message_text} {part1} {part2} {paramChoice}')
                    element_poll_history = repo_get_poll_from_poll_history(repo, poll_index)
                else:
                    element_poll_history = repo_get_poll_from_poll_history(repo, -1)
            else:
                element_poll_history = repo_get_poll_from_poll_history(repo, -1)
        else:
            logger.info("checkbill_handler can't find suitable poll")
            return

        message = update.message

    if element_poll_history is None:
        message_id = f'{message.message_id}'
    else:
        # logger.info(f"checkbill_handler element_poll_history {element_poll_history}")
        msg_poll_id = element_poll_history["msg_poll_id"]
        message_id = msg_poll_id
        map_msg_poll_id_to_message_id = repo.get("map_msg_poll_id_to_message_id", dict())
        # logger.info(f"checkbill_handler map_msg_poll_id_to_message_id {map_msg_poll_id_to_message_id}")
        # logger.info(f"checkbill_handler map_msg_poll_id_to_message_id {map_msg_poll_id_to_message_id}")
        # message_id = str(map_msg_poll_id_to_message_id.get(str(msg_poll_id), f"{message.message_id}"))
        # logger.info(f"checkbill_handler map_msg_poll_id_to_message_id[] {map_msg_poll_id_to_message_id[str(msg_poll_id)]}")
        # logger.info(f"checkbill_handler map_msg_poll_id_to_message_id.get {map_msg_poll_id_to_message_id.get(msg_poll_id)}")

    poll_owner_id = f'{message.chat.id}'
    
    return {"poll_owner_id": poll_owner_id, "message_id": message_id}
