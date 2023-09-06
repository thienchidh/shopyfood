import asyncio
from cmath import log
import json
import random
import re
import time
from logger import logger
import CONST

import yaml
from tabulate import tabulate
from telegram import (
    Update, BotCommand, Poll,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    filters, )

from model.poll_model import get_poll_model
from model.user_model import get_user_model
from util import *


async def remind_paid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message.reply_to_message
    
    val_return = get_poll_owner_id_message_id(update, context)
    if (val_return is None):
        return
    
    poll_data_manager = get_poll_model(update, context, -1, -1, -1)
    poll_data = None
    
    user_paid_id = update.effective_user.id
    message_id = val_return["message_id"]
  


    list_poll_ids = poll_data_manager.get_list_poll_id_follow_message_id(message_id)
    
    if (list_poll_ids is None or len(list_poll_ids) <= 0):
        strLocal = "Remind paidl hơi xa rồi đó không có data!"
        await update.effective_message.reply_text(text=f"{strLocal}", parse_mode=ParseMode.HTML)
        return
    
    logger.info(f"paid handler list_poll_ids : {list_poll_ids}")
        
  
    list_user_not_paid = []

    for poll_id in list_poll_ids:
        poll_data = poll_data_manager.get_poll_data_by_poll_id(poll_id)
        if poll_data is not None:
            logger.info(f"remind_paid_handler poll_id {poll_id}")
            for key in poll_data.get_answers():
                list_answer_of_this_user = poll_data.get_answers()[key]
                logger.info(f"remind_paid_handler key {key}")
                logger.info(f"remind_paid_handler list_answer_of_this_user {list_answer_of_this_user}")
                paid_state = 0
                if key in poll_data.get_paid_state():
                    if poll_data.get_paid_state()[key] is not None:
                        paid_state = int(poll_data.get_paid_state()[key])
                if (paid_state <= 0):
                    list_user_not_paid.append(int(key))

          
    strContent = ""          
    for user_id in list_user_not_paid:
        user_model = get_user_model(update, context, user_id)
        user_name = user_model.get_user_name()
        mention_html = f'<a href="tg://user?id={user_id}">@{user_name}</a>'
        strContent += f" {mention_html}"
   

    time_created = -1 if poll_data is None else poll_data.get_time_created()
    host_poll_id = -1 if poll_data is None else poll_data.get_host_poll_id()
    host_user_name = get_user_model(update, context, host_poll_id).get_user_name()
    description = get_user_model(update, context, host_poll_id).get_latest_description()
   
    date_at_midnight_at_time_created = get_datetime_at_midnight_at_timestamp(time_created)
    phone = repo_get_phone_by_user_id(context, host_poll_id)
    

    str_header = f"{strContent} may sep quen paid:\n{date_at_midnight_at_time_created}\nHost: {host_user_name} - {description}"
    await update.effective_message.reply_text(text=f"{str_header}\n", parse_mode=ParseMode.HTML)    
    return
    
