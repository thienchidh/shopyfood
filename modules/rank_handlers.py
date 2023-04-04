import logger
from all_repo_get_func import *

def calculate_point(repo, user_id, poll_id):
    all_user_answers_by_poll_id = repo_get_all_user_answers_by_poll_id(repo, poll_id)
    array_user_id = [{"user_id": key, "timestamp": value["timestamp"], "answer_correct": value["answer_correct"]} for key, value in all_user_answers_by_poll_id.items()]
    answer_right = 0 
    answer_wrong = 0
    bonus_point_fast_answer = 0

    sort_array = sorted(array_user_id, key=lambda x: x["timestamp"])
    indexed_sort_array = [ {"index": i, "point": max(0, 0), **obj} for i, obj in enumerate(sort_array)]
    logger.info(f"user_id: {user_id}")
    logger.info(f"indexed_sort_array: {indexed_sort_array}")
    logger.info(f"poll_id: {poll_id}")

    

    filtered_elements = [element for element in indexed_sort_array if element["user_id"] == user_id]
    logger.info(f"filtered_elements: {filtered_elements}")
    if (len(filtered_elements) <= 0):
        return 0 
    

    bonus_point_fast_answer = filtered_elements[0]["point"] if filtered_elements[0]["answer_correct"] == True else 0
    answer_right = 1 if filtered_elements[0]["answer_correct"] == True else 0
    answer_wrong = 1 if filtered_elements[0]["answer_correct"] == False else 0

    total_point = answer_right * 3 + answer_wrong * -1 + bonus_point_fast_answer 
    
    return total_point

def stat_at_day_index(repo, day_index = 0):
    
    if day_index is None:
        day_index = 0
    if day_index > 0:
        day_index = 0

    logger.info("stat_at_day_index ")

    headers = ["STT", "Name", "num_correct", "num_incorrect", "total_point"]
    table_data = [
        headers,
       
    ]
    stt = 1
    all_user_info_at_day_index = repo_get_all_user_info_at_day_index(repo, day_index)
    array_need_sort = []
    
    for user_id in all_user_info_at_day_index:
        # logger.info(f"stat_at_day_index specifict_user_info {all_user_info_at_day_index[user_id]}")
        choose_poll = repo_get_all_choose_poll_of_specific_user_at_day_index(repo, user_id, day_index)
        # logger.info(f"stat_at_day_index choose_poll {choose_poll}")
        num_correct = 0
        num_incorrect = 0
        total_point = 0
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

            total_point += calculate_point(repo, user_id, poll_id)

        user_name = repo_get_user_chat_id_name_by_user_id(repo, user_id)
        # row_data = [stt, user_name, num_correct, num_incorrect, total_point]
        # table_data.append(row_data)
        # stt+=1   
        
        array_need_sort.append({"stt": stt, "user_name": user_name, "total_point": total_point, "num_correct": num_correct, "num_incorrect": num_incorrect })

    sort_array = sorted(array_need_sort, key=lambda x: -x["total_point"])    
    for element in sort_array:
        user_name = element["user_name"]
        num_correct = element["num_correct"]
        num_incorrect = element["num_incorrect"]
        total_point = element["total_point"]
        row_data = [stt, user_name, num_correct, num_incorrect, total_point]
        table_data.append(row_data)
        stt+=1


    return table_data        

    
    pass