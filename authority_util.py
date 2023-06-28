from telegram import (
    Update, BotCommand, Poll,
)
from functools import wraps
from telegram.ext import CallbackContext, Updater, CommandHandler, InlineQueryHandler, CallbackQueryHandler
from logger import logger
import CONST


def is_admin(user_id):
    is_admin_local = (user_id == 123) or (user_id == CONST.THANHHV3_USER_ID)
    return is_admin_local
     


# Define decorator function for authority check
def check_authority(authority_level):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: CallbackContext):
            user_authority = await get_user_authority(update.effective_user.id)
            if user_authority >= authority_level:
                await func(update, context)
            else:
                await update.message.reply_text('You do not have sufficient authority to access this command.')
        return wrapper
    return decorator

# Simulated function to retrieve user authority level (replace with your own implementation)
async def get_user_authority(user_id):
    # Retrieve user authority level from database or other data source
    # This is a placeholder implementation; replace it with your own logic
    logger.info(f"userId: {user_id} {type(user_id)}")
    logger.info(f"userId: {user_id == CONST.THANHHV3_USER_ID}")
    if is_admin(user_id):  # User ID example
        return CONST.AUTHORITY_ADMIN
    elif user_id == 456:  # User ID example
        return CONST.AUTHORITY_MODERATOR
    else:
        return CONST.AUTHORITY_USER
