import logger
from all_repo_get_func import *

def stat_at_day_index(repo, day_index = 0):
    
    if day_index is None:
        day_index = 0
    if day_index > 0:
        day_index = 0

    logger.info("stat_at_day_index ")

    headers = ["STT", "Name", "num_correct", "num_incorrect"]
    table_data = [
        headers,
       
    ]
    stt = 1
    all_user_info_at_day_index = repo_get_all_user_info_at_day_index(repo, day_index)
    for user_id in all_user_info_at_day_index:
        # logger.info(f"stat_at_day_index specifict_user_info {all_user_info_at_day_index[user_id]}")
        choose_poll = repo_get_all_choose_poll_of_specific_user_at_day_index(repo, user_id, day_index)
        # logger.info(f"stat_at_day_index choose_poll {choose_poll}")
        num_correct = 0
        num_incorrect = 0
        for poll_id in choose_poll:
            poll_data = repo_get_poll_data_by_poll_id(repo, poll_id)
            logger.info(f"poll_data {poll_id} {poll_data}")
            specific_user_ansswers = repo_get_specific_user_answers_by_poll_id(repo, poll_id, user_id)
            logger.info(f"specific_user_ansswers {user_id} {poll_id} {specific_user_ansswers}")
            answer_correct = specific_user_ansswers.get("answer_correct", False)
            if (answer_correct):
                num_correct += 1
            else:
                num_incorrect += 1
            

        user_name = repo_get_user_chat_id_name_by_user_id(repo, user_id)
        row_data = [stt, user_name, num_correct, num_incorrect]
        table_data.append(row_data)
        stt+=1   
    return table_data        

    
    pass