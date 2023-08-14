import asyncio
from cmath import log
import json
import random
import re
import time
from all_get_repo_func import *
from all_repo_get_func import *
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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, Updater, CommandHandler, InlineQueryHandler, CallbackQueryHandler
from model.poll_model import get_poll_model

from util import *

async def paid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message.reply_to_message
    
    val_return = get_poll_owner_id_message_id(update, context)
    if (val_return is None):
        return
    
    poll_data_manager = get_poll_model(update, context, -1, -1, -1)
    poll_data = None
    
    user_paid_id = update.effective_user.id
    poll_owner_id = val_return["poll_owner_id"]
    message_id = val_return["message_id"]
    repo = get_repo_bot(context)
    poll_id = repo_get_poll_id_by_message_id(repo, message_id)
    host_poll_id = repo_get_host_poll_id_by_poll_id(repo, poll_id)
    host_user_name = repo_get_user_name_by_user_id(context, host_poll_id)
    user_paid_user_name = repo_get_user_name_by_user_id(context, user_paid_id)
    logger.info(f"paid handler poll_owner_id : {poll_owner_id}")
    logger.info(f"paid handler message_id : {message_id}")
    logger.info(f"paid handler host_poll_id : {host_poll_id}")
    logger.info(f"paid handler user_name : {host_user_name}")


    list_poll_ids = poll_data_manager.get_list_poll_id_follow_message_id(message_id)
    
    # logger.info(f"paid handler parent_id : {parent_id}")
    logger.info(f"paid handler list_poll_ids : {list_poll_ids}")
    chat_id_names = repo.compute_if_absent('chat_id_names', lambda k: dict())
    # logger.info(f"paid handler chat_id_names : {chat_id_names}")
    
    headers = ["STT", "Name", "Dish", "Price", "Paid"]
    table_data = [
        headers,
        # {"STT": 1, "Name": "John", "Dish": "Pizza", "Price": 10.99},
        # [1, "John", "Pizza", 10.99],
        # [1, "John", "Pizza", 10.99]
    ]
    index = 0
    subtotal_int = 0

    for poll_id in list_poll_ids:
        # poll_data = repo_get_poll_data_by_poll_id(repo, poll_id_each)
        poll_data = poll_data_manager.get_poll_data_by_poll_id(poll_id)
        
        # logger.info(f"poll_data {poll_data}")
           
        if poll_data is not None:
            logger.info(f"user_paid_id {user_paid_id}")
            logger.info(f"poll_id {poll_id}")
            # repo_set_paid_state_by_user_id_poll_id(repo, user_paid_id, poll_id)
            # repo.save()
            for key in poll_data.get_answers():
                list_answer_of_this_user = poll_data.get_answers()[key]
                logger.info(f"list_answer_of_this_user {list_answer_of_this_user}")
                if (str(key) == str(user_paid_id)):
                    poll_data.set_paid_state_by_user_id(user_paid_id, 1)
                    repo.save()
                    continue
          

    poll_data_manager.save()                    
    # list of column headers
    subtotal_str = '{:,.0f}'.format(subtotal_int) + "\u0111"

    # calculate the subtotal
    # subtotal = sum(row["Price"] for row in table_data)
    subtotal_row = ["-", "-", f"-", "-"]
    table_data.append(subtotal_row)
    # add a row for the subtotal
    subtotal_row = ["", "", f"Subtotal {subtotal_str}", ""]
    table_data.append(subtotal_row)
    subtotal_row = ["", "", f"AppFee {100}", ""]
    table_data.append(subtotal_row)
    subtotal_row = ["", "", f"Discount1 {100}", ""]
    table_data.append(subtotal_row)
    subtotal_row = ["", "", f"Discount2 {100}", ""]
    table_data.append(subtotal_row)
    # print the table using the tabulate library
    # string = tabulate(table_data, headers="firstrow", showindex=True)
    # print(string)

    time_created = -1 if poll_data is None else poll_data.get_time_created()
    host_poll_id = -1 if poll_data is None else poll_data.get_host_poll_id()
   
    date_at_midnight_at_time_created = get_datetime_at_midnight_at_timestamp(time_created)
    table_str = tabulate(table_data, headers="firstrow", tablefmt='orgtbl', showindex=False)
    host_user_name = repo_get_user_name_by_user_id(context, host_poll_id)
    phone = repo_get_phone_by_user_id(context, host_poll_id)
    description = repo_get_description_by_user_id(context, host_poll_id)
    
    # await update.effective_message.reply_document(open('./config/mp4.mp4', 'rb'))
    paid_user_name = repo_get_user_name_by_user_id(context, user_paid_id)
    str_header = f"{paid_user_name} da paid cho:\n{date_at_midnight_at_time_created}\nHost: {host_user_name} - {description}"
    await update.effective_message.reply_text(text=f"<pre>{str_header}\n</pre>", parse_mode=ParseMode.HTML)
    pass
    
    return
    # xu ly case reply message 
    if message is None or message.poll is None:
        message_text = update.message.text
        
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='button1')],
            [InlineKeyboardButton("No", callback_data='button2')]
        ]
        # await update.message.reply_text(f'{update.effective_user.mention_html()} Trả cho poll nào thế?',
                                        # parse_mode=ParseMode.HTML)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"@{user_paid_user_name} da paid, Host @{host_user_name} check paid bạn ơi ", reply_markup=reply_markup)
        return


# Define a callback query handler function
async def button_click(update: Update, context: CallbackContext):
    """Handle button click events."""
    query = update.callback_query
    query.answer()
    logger.info(f"button click update: {update}")
    logger.info(f"button click query {query}")
    
    # Perform actions based on the button clicked
    if query.data == 'button1':
        logger.info("Button 1 clicked")
        await query.edit_message_text(text='Button 1 clicked!')
    elif query.data == 'button2':
        logger.info("Button 2 clicked")
        await query.edit_message_text(text='Button 2 clicked!')
    elif query.data == 'button3':
        logger.info("Button 3 clicked!")
        await query.edit_message_text(text='Button 3 clicked!')
    
