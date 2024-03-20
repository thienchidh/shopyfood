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

from all_get_repo_func import *
from all_repo_get_func import *
from util import *


async def paid_poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo = get_repo_bot(context)
    val_return = get_poll_owner_id_message_id(update, context)
    if (val_return is None):
        return
    poll_owner_id = val_return["poll_owner_id"]
    message_id = val_return["message_id"]

    logger.info("Info poll " + poll_owner_id + " " + message_id)
    poll_data = get_poll_data_by_message_id(context, message_id)


    # list of dictionaries representing table rows
    # list of dictionaries representing table rows
    headers = ["STT", "Name", "Dish", "Price", "Paid"]
    table_data = [
        headers,
        # {"STT": 1, "Name": "John", "Dish": "Pizza", "Price": 10.99},
        # [1, "John", "Pizza", 10.99],
        # [1, "John", "Pizza", 10.99]
    ]
    parent_id = repo_get_parent_poll_ids_from_specific_chat_id_by_message_id(repo, poll_owner_id, message_id)
    # List all poll that have common parent
    list_poll_ids = repo_get_list_child_poll_ids_from_specific_chat_id_by_parent_id(repo, poll_owner_id, parent_id)
    # tong hop data tung poll

    chat_id_names = repo.compute_if_absent('chat_id_names', lambda k: dict())

    logger.info(f"list_poll_ids {list_poll_ids}")
    index = 0
    subtotal_int = 0
    poll_id_selected = None
    for message_id in list_poll_ids:
        poll_data = get_poll_data_by_message_id(context, message_id)
        logger.info(f"poll_data {poll_data}")
        if poll_id_selected is None:
            poll_id_selected = repo_get_poll_id_by_message_id(repo, message_id)

        if "answers" in poll_data:
            for key in poll_data["answers"]:
                if "questions" in poll_data:
                    list_answer_of_this_user = poll_data["answers"].get(key)
                    logger.info(f"list_answer_of_this_user {list_answer_of_this_user}")
                    paid_state = 0
                    if poll_data.get("paid_state") is not None:
                        if (poll_data.get("paid_state").get(key) is not None):
                            paid_state = int(poll_data.get("paid_state").get(key))

                    for i in list_answer_of_this_user:
                        string_answer = poll_data["questions"][i]
                        match = re.match(r'^(.*)\s(\d{1,3}([,.]\d{3})*).*$', string_answer)
                        if match:
                            index += 1
                            part1_dish = match.group(1)
                            price_str = match.group(2)  # price
                            price_int = int(remove_non_digits(price_str))
                            price_str_format = '{:,.0f}'.format(price_int) + "\u0111"
                            name = chat_id_names.get(key, key)
                            if (paid_state > 0):
                                is_paid = "PAID"
                            else:
                                is_paid = "No_PAID"

                            row = [index, f"{name}", part1_dish, price_str_format, is_paid]
                            table_data.append(row)
                            subtotal_int += price_int

                    pass

    # tao poll:
    # user name -> mon da pick
    # list of column headers
    subtotal_str = '{:,.0f}'.format(subtotal_int) + "\u0111"

    # calculate the subtotal
    # subtotal = sum(row["Price"] for row in table_data)
    subtotal_row = ["-", "-", f"-", "-"]
    table_data.append(subtotal_row)
    # add a row for the subtotal
    subtotal_row = ["", "", f"Subtotal {subtotal_str}", ""]
    table_data.append(subtotal_row)
    # print the table using the tabulate library
    # string = tabulate(table_data, headers="firstrow", showindex=True)
    # print(string)

    time_created = repo_get_time_created_by_poll_id(repo, poll_id_selected)
    host_poll_id = repo_get_host_poll_id_by_poll_id(repo, poll_id_selected)

    date_at_midnight_at_time_created = get_datetime_at_midnight_at_timestamp(time_created)
    table_str = tabulate(table_data, headers="firstrow", tablefmt='orgtbl', showindex=False)
    host_user_name = repo_get_user_name_by_user_id(context, host_poll_id)
    phone = repo_get_phone_by_user_id(context, host_poll_id)
    description = repo_get_description_by_user_id(context, host_poll_id)

    # await update.effective_message.reply_document(open('./config/mp4.mp4', 'rb'))
    str_header = f"{date_at_midnight_at_time_created}\nHost: {host_user_name} - {description}"
    await update.effective_message.reply_text(text=f"<pre>{str_header}\n{table_str}</pre>", parse_mode=ParseMode.HTML)
    pass

    text = update.message.text
    url = text.split(' ')[1]

    obj = attempt_process(url)
    # check obj is string
    if isinstance(obj, str):
        await update.message.reply_text(obj)
        return

    if obj is None:
        await update.message.reply_text('Không hỗ trợ địa chỉ này')
        return

    title = obj[0]
    items = obj[1]

    # Split items into 10 items per poll
    limit_items_per_poll = 10
    items_split = [items[i:i + limit_items_per_poll] for i in range(0, len(items), limit_items_per_poll)]
    logger.info(json.dumps(items_split))

    # Ensure last poll has at least 2 items and at most 10 items
    if len(items_split[-1]) < 2:
        items_split[-1].append(items_split[-2].pop())

    logger.info(json.dumps(items_split))

    repo = get_repo_bot(context)
    poll_owner_id = f'{update.effective_chat.id}'

    parent_poll_id = None
    parent_poll_ids = dict()
    poll_group_ids = []
    poll_data = dict()
    poll_ids = []
    host_poll_id = update.message.from_user.id
    time_created = time.time()

    # Create poll for each item
    current_page = 0
    for items in items_split:
        current_page += 1
        questions = [item['name'] + ' ' + item['price'] for item in items[:limit_items_per_poll]]

        if len(questions) < 2:
            await update.message.reply_text('Không có đủ món ăn để tạo poll')
            return

        # add page to poll title if there are more than 1 page
        pool_title = title
        if len(items_split) > 1:
            pool_title += ' - P' + str(current_page)

        message = await context.bot.send_poll(
            poll_owner_id,
            pool_title,
            questions,
            is_anonymous=False,
            allows_multiple_answers=True,
        )
        msg_poll_id = f'{message.message_id}'
        poll_group_ids.append(msg_poll_id)
        poll_ids.append(message.poll.id)

        if parent_poll_id is None:
            parent_poll_id = msg_poll_id
        parent_poll_ids[msg_poll_id] = parent_poll_id
        logger.info("Paid handler poll created {0} {1} {2}".format(msg_poll_id, poll_owner_id, message.poll.id))

        map_msg_poll_id_to_message_id = repo.get("map_msg_poll_id_to_message_id", dict())
        map_msg_poll_id_to_message_id.update({f"{msg_poll_id}": message.poll.id})
        repo.set("map_msg_poll_id_to_message_id", map_msg_poll_id_to_message_id)

        # Save some info about the poll the bot_data for later use in receive_poll_answer
        payload = {
            message.poll.id: {
                "time_created": time_created,
                "questions": questions,
                "message_id": message.message_id,
                "chat_id": update.effective_chat.id,
                "answers": dict(),  # {user_id: [answer_index]}
                "poll_type": CONST.POLL_TYPE_PICK_DISH,
                "paid_state": dict(),
                "host_poll_id": host_poll_id
            }
        }
        poll_data.update(payload)
        context.bot_data.update(payload)

    poll_history = repo.get("poll_history", [])
    poll_json_object = {
        "msg_poll_id": poll_group_ids[0],
        "create_at": time.time(),
        "owner_id": poll_owner_id,
    }

    poll_history.append(poll_json_object)
    repo.set("poll_history", poll_history)

    all_parent_poll_ids = repo.compute_if_absent('parent_poll_ids', lambda k: dict())
    map = all_parent_poll_ids.get(poll_owner_id, dict())
    map.update(parent_poll_ids)

    all_parent_poll_ids[poll_owner_id] = map

    all_poll_group_ids = repo.compute_if_absent('poll_group_ids', lambda k: dict())
    map = all_poll_group_ids.get(poll_owner_id, dict())
    map[parent_poll_id] = poll_group_ids

    all_poll_group_ids[poll_owner_id] = map

    all_poll_data = repo.compute_if_absent('poll_data', lambda k: dict())
    all_poll_data.update(poll_data)
    all_poll_data[poll_owner_id] = map

    repo.save()
