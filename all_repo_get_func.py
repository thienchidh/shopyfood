from logger import logger
from util import *

def repo_get_all_user_info_at_day_index(repo, day_index):
    if day_index is None:
        day_index = 0
    if day_index > 0:
        day_index = 0

    datetime_at_midnight_add_days = get_datetime_at_midnight_and_add_days(day_index)
    day_info = repo.get("day_info", dict())
    day_info_user_info = day_info.get(datetime_at_midnight_add_days, dict())
    return day_info_user_info.get("user_info", dict())
    

def repo_get_specific_user_info_at_day_index(repo, user_id, day_index):
    all_user_info_at_day_index = repo_get_all_user_info_at_day_index(repo, day_index)
    return all_user_info_at_day_index.get(user_id, dict())
    
def repo_get_all_choose_poll_of_specific_user_at_day_index(repo, user_id, day_index):
    specifict_user_at_day_index = repo_get_specific_user_info_at_day_index(repo, user_id, day_index)
    return specifict_user_at_day_index.get("choose_poll", [])    

def repo_get_user_chat_id_name_by_user_id(repo, user_id):
    chat_id_names = repo.get("chat_id_names", dict())
    return chat_id_names.get(user_id, dict())


def repo_get_poll_data_by_poll_id(repo, poll_id):
    all_poll_data = repo.get("poll_data", dict())
    return all_poll_data.get(poll_id, dict())
    
def repo_get_all_user_answers_by_poll_id(repo, poll_id):
    poll_by_poll_id = repo_get_poll_data_by_poll_id(repo, poll_id)
    all_user_answers_at_poll = poll_by_poll_id.get("user_answers", dict())
    return all_user_answers_at_poll

def repo_get_specific_user_answers_by_poll_id(repo, poll_id, user_id):
    all_user_answers_at_poll = repo_get_all_user_answers_by_poll_id(repo, poll_id)
    return all_user_answers_at_poll.get(user_id, dict())    

def repo_get_repo_bot_day_info_at_specific_date(repo, datetime_midnight):
    # repo = get_repo_bot(context)
    day_info = repo.get("day_info", dict())
    logger.info(f"get_repo_bot_day_info day_info {day_info}")

    if (datetime_midnight not in day_info):
        payload = { 
            datetime_midnight : {
                "user_info": {}
            }
        }
        day_info.update(payload)
        logger.info(f"day_info update {day_info}")
        repo.set("day_info", day_info)
        logger.info(f'day_info update get from repo {repo.get("day_info")}')
        return day_info.get(datetime_midnight)
        pass
    else:
        return day_info.get(datetime_midnight)

