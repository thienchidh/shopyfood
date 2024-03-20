from asyncore import poll
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


def repo_get_all_user_paid_state_by_poll_id(repo, poll_id):
    poll_by_poll_id = repo_get_poll_data_by_poll_id(repo, poll_id)
    if (poll_by_poll_id.get("paid_state") is None):
        poll_by_poll_id["paid_state"] = dict()
    all_user_paid_state_at_poll = poll_by_poll_id.get("paid_state")
    return all_user_paid_state_at_poll


def repo_set_paid_state_by_user_id_poll_id(repo, user_id, poll_id):
    all_user_paid_state_at_poll = repo_get_all_user_paid_state_by_poll_id(repo, poll_id)
    logger.info(f"all_user_paid_state_at_poll {user_id} {all_user_paid_state_at_poll} ")
    if f"{user_id}" in all_user_paid_state_at_poll:
        logger.info(f"repo_set_paid_state_by_user_id_poll_id {user_id} {poll_id} ")
        all_user_paid_state_at_poll[f"{user_id}"] = 1


def repo_get_poll_from_poll_history(repo, poll_index=-1):
    poll_history = repo.get("poll_history")
    if poll_history is None:
        return None
    if poll_index >= 0 and poll_index < len(poll_history):
        return poll_history[poll_index]
    if poll_index < 0 and abs(poll_index) <= len(poll_history):
        return poll_history[poll_index]
    return None


def repo_get_host_poll_id_by_poll_id(repo, poll_id):
    poll_by_poll_id = repo_get_poll_data_by_poll_id(repo, poll_id)
    host_poll_id = poll_by_poll_id.get("host_poll_id")
    if host_poll_id is None:
        poll_by_poll_id["host_poll_id"] = -1
    host_poll_id = poll_by_poll_id.get("host_poll_id", -1)
    return host_poll_id

def repo_get_time_created_by_poll_id(repo, poll_id):
    poll_by_poll_id = repo_get_poll_data_by_poll_id(repo, poll_id)
    time_created = poll_by_poll_id.get("time_created")
    if time_created is None:
        poll_by_poll_id["time_created"] = time.time()
    time_created = poll_by_poll_id.get("time_created", -1)
    return time_created


def repo_get_parent_poll_ids_from_specific_chat_id_by_message_id(repo, chat_id, message_id):
    parent_poll_ids = repo.get("parent_poll_ids", dict()).get(chat_id, dict())
    parent_id = parent_poll_ids.get(message_id)
    return parent_id

def repo_get_list_child_poll_ids_from_specific_chat_id_by_parent_id(repo, chat_id, parent_id):
    poll_group_ids = repo.get('poll_group_ids', dict()).get(chat_id, dict())
    list_poll_ids = poll_group_ids.get(parent_id, dict())
    return list_poll_ids

def repo_get_poll_id_by_message_id(repo, message_id):
    map_msg_poll_id_to_message_id = repo.get("map_msg_poll_id_to_message_id", dict())
    poll_id = map_msg_poll_id_to_message_id.get(message_id, dict())
    return poll_id


def repo_get_user_name_by_user_id(context, user_id):
    repo_user = get_repo_user(user_id, context)
    list_user_name = repo_user.get("user_name", [])
    if (len(list_user_name) == 0):
        # get username from telegram
        return "NotFoundUserName"
    return list_user_name[0]


def repo_get_phone_by_user_id(context, user_id):
    repo_user = get_repo_user(user_id, context)
    list_phone = repo_user.get("phone", [])
    if (len(list_phone) == 0):
        return "NotFoundPhone"
    return list_phone[0]


def repo_get_description_by_user_id(context, user_id):
    repo_user = get_repo_user(user_id, context)
    list_description = repo_user.get("description", [])
    if (len(list_description) == 0):
        return "NotFoundDescription"
    return list_description[0]
