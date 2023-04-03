import asyncio
import math
import random

from telegram import (
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from . import bot_session

sticker_con_cho_nay = "CAACAgUAAxkBAAMcY_R9Pq2TX2nr5HJhnOsOtvL54loAAmIFAAILoWlUcUfqZlXc0AwuBA"

sticker_set_emgaimua = "emgaimua"


async def handle_chui(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker_set_name = sticker_set_emgaimua
    sticker_set = await context.bot.get_sticker_set(sticker_set_name)
    stickers = [sticker.file_id for sticker in sticker_set.stickers]

    random_sticker = random.choice(stickers)
    await context.bot.send_sticker(sticker=random_sticker, chat_id=update.message.chat_id)

    # await context.bot.send_sticker(sticker=sticker_con_cho_nay, chat_id=update.message.chat_id)


async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('handle_sticker')
    sticker = update.message.sticker
    if sticker:
        print("sticker file id is", sticker.file_id)
        sticker_file = await context.bot.get_file(sticker.file_id)
        file_path = sticker_file.file_path
        sticker_set_name = file_path.split('/')[1]
        print('sticker set name', file_path, sticker_set_name)

    # await update.effective_message.reply_sticker(update.message.sticker)


cache = {}
cache['players'] = []
cache['is_rolling'] = False


def is_rolling(chat_id):
    data = bot_session.get_data(chat_id=chat_id)
    if data is None:
        return False
    return data['is_rolling']


def set_rolling(chat_id: str, b: bool):
    data = bot_session.get_data(chat_id=chat_id)
    if data is None:
        return
    data['is_rolling'] = b


def get_players(chat_id):
    data = bot_session.get_data(chat_id=chat_id)
    if data is None:
        return []
    return data['players']


def set_players(chat_id: str, players):
    data = bot_session.get_data(chat_id=chat_id)
    if data is None:
        return
    data['players'] = players


def sort_players(a: str):
    base_score = math.pow(7, 10)
    scores = list(a)
    total_score = 0
    for score in scores:
        total_score += base_score * int(score)
        base_score /= 7
        if base_score == 1:
            return total_score
    return total_score


def convert_ranking_to_str(data) -> str:
    text = ""
    sorted_data = sorted(data, key=lambda x: sort_players(x['value']), reverse=True)
    counter = 1
    for player in sorted_data:
        scores = player['value']
        scores = list(scores)
        scores = ' -> '.join(scores)
        text += ("%s. %s : %s điểm\n" % (counter, player['name'], scores))
        counter += 1
    return text


async def handle_start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rolling(update.message.chat_id):
        await update.message.reply_text("Đang roll rồi, chờ end ván này đã rồi start tiếp")
        return
    bot_session.create_data(update.message.chat_id, {
        'players': [],
        'is_rolling': False
    })
    set_rolling(update.message.chat_id, True)
    await update.message.reply_text("Bắt đầu roll")
    pass


async def handle_info_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_rolling(update.message.chat_id):
        return
    text = convert_ranking_to_str(get_players(update.message.chat_id))
    await update.message.reply_text(text)


async def handle_finish_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_rolling(update.message.chat_id):
        return
    text = "Kết thúc ván, kết quả là:\n"
    players = get_players(update.message.chat_id)
    text += convert_ranking_to_str(players)
    await update.message.reply_text(text)
    bot_session.clear_data(update.message.chat_id)


async def handle_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Roll in chat_id", update.message.chat_id)
    if not is_rolling(update.message.chat_id):
        return

    if update.message.forward_from or update.message.forward_from_chat or update.message.forward_from_message_id or update.message.forward_signature or update.message.forward_sender_name or update.message.forward_date:
        return

    dice_value = update.message.dice.value
    sender_full_name = update.effective_user.full_name
    sender_username = update.effective_user.name
    chat_id = update.message.chat_id

    players = get_players(chat_id=chat_id)
    old_players = list(filter(lambda x: x['name'] == sender_username, players))
    if len(old_players) > 0:
        player = old_players[0]
        await update.message.reply_text('%s lại roll nữa' % sender_username)
        player['value'] += str(dice_value)
    else:
        players.append({
            'name': sender_username,
            'value': str(dice_value)
        })

    asyncio.create_task(send_dice_result(sender_full_name, dice_value, update))


async def send_dice_result(sender_username, dice_value, update):
    await asyncio.sleep(2.5)
    await update.message.reply_text("%s vừa roll ra %s điểm" % (sender_username, dice_value))
