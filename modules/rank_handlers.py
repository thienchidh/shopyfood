import logger
from all_repo_get_func import *

def stat_at_day_index(repo, day_index = 0):
    
    if day_index is None:
        day_index = 0
    if day_index > 0:
        day_index = 0

    logger.info("stat_at_day_index ")

    headers = ["STT", "Name", "Dish", "Price"]
    table_data = [
        headers,
       
    ]
    all_user_info_at_day_index = repo_get_all_user_info_at_day_index(repo, day_index)
    for specific_user_info in all_user_info_at_day_index:
        logger.info(f"stat_at_day_index specifict_user_info {all_user_info_at_day_index[specific_user_info]}")
   
    
    pass