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


def append_to_last_line(filename, string_to_append):
    try:

        # Open the file in write mode to save changes
        with open(filename, 'a') as file:
            file.writelines(string_to_append + "\n")

        print(f"Successfully appended '{string_to_append}' to the last line of {filename}.")
    except Exception as e:
        print(f"An error occurred: {e}")
        


async def spend_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message.reply_to_message
    message_text = update.message.text
    
    user_id = update.effective_user.id
    current_datetime = datetime.now()

    # Format the date and time
    formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    timestampe_str = formatted_datetime
    logger.info(f"user_id {user_id}")
    string_append = f"{timestampe_str} {user_id} {message_text}"
    # user_id_top_link = "top_link"
    # user = get_user_model(update, context, user_id_top_link)
    # top_links = user.get_links()
    # logger.info(f"top links {top_links}")
    # message = "Top Links:\n"
    # for i, link in enumerate(top_links, 1):
        # message += f"{i}. {link['url']} - Hosted {link['num_host']} times\n"
    # update.message.reply_text(message)
    append_to_last_line("spend_log.txt", string_append)
    
    await update.effective_message.reply_text(message_text)
    
