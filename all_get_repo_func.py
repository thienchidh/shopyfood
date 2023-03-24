from asyncio.log import logger
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    filters, )

from repository import KeyValRepository


def get_repo_bot(context: ContextTypes.DEFAULT_TYPE) -> KeyValRepository:
    repo = context.bot_data.get('bot')
    if not repo or repo is not KeyValRepository:
        repo = KeyValRepository('bot')
        context.bot_data['bot'] = repo
    return repo

def get_repo_user(user_id, context: ContextTypes.DEFAULT_TYPE) -> KeyValRepository:
    repo = context.user_data.get(user_id)
    if not repo or repo is not KeyValRepository:
        repo = KeyValRepository(user_id)
        context.user_data[user_id] = repo
    return repo


    

