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


async def top_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message.reply_to_message
    
    user_id_top_link = "top_link"
    user = get_user_model(update, context, user_id_top_link)
    top_links = user.get_links()
    logger.info(f"top links {top_links}")
    message = "Top Links:\n"
    for i, link in enumerate(top_links, 1):
        message += f"{i}. {link['url']} - Hosted {link['num_host']} times\n"
    # update.message.reply_text(message)
    await update.effective_message.reply_text(message)
    
