import asyncio
import json
import tracemalloc  # Import the tracemalloc module
from datetime import datetime

import yaml
from tabulate import tabulate
from telegram import (
    BotCommand, Poll,
)
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler

import crawl_grabfood
import crawl_shopeefood
import modules.logic_handlers as logic_handlers
import modules.rank_handlers as rank_handlers
import quiz_loader
import quote_storate
from all_get_repo_func import *
from all_repo_get_func import *
from authority_util import check_authority
from modules.paid_handler import paid_handler, button_click
from modules.paid_poll_handlers import paid_poll_handler
from modules.remind_paid_handler import remind_paid_handler
from util import *
from model.user_model import *
from model.poll_model import *

strategies = [
    crawl_shopeefood,
    crawl_grabfood,
]


# Define commands
@check_authority(CONST.AUTHORITY_ADMIN)
async def admin_only_command(update: Update, context: CallbackContext):
    await update.message.reply_text('This command can only be accessed by administrators.')


@check_authority(CONST.AUTHORITY_MODERATOR)
async def moderator_only_command(update: Update, context: CallbackContext):
    await update.message.reply_text('This command can only be accessed by moderators and administrators.')


@check_authority(CONST.AUTHORITY_USER)
async def public_command(update: Update, context: CallbackContext):
    await update.message.reply_text('This command can be accessed by all users.')


def attempt_process(url):
    for strategy in strategies:
        if strategy.is_support_url(url):
            return strategy.process(url)
    return None


async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    alert_msg = obj[2]

    # Split items into 10 items per poll
    limit_items_per_poll = 10
    items_split = [items[i:i + limit_items_per_poll] for i in range(0, len(items), limit_items_per_poll)]
    # logger.info(json.dumps(items_split))

    # Ensure last poll has at least 2 items and at most 10 items
    if len(items_split[-1]) < 2:
        items_split[-1].append(items_split[-2].pop())

    # logger.info(json.dumps(items_split))

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
    previous_poll_id = -1
    next_poll_id = -1
    
    previous_poll = None
    poll_id = -1
    chat_id = update.effective_chat.id
    
    poll_data_manager = get_poll_model(update, context, poll_id, host_poll_id, chat_id)
    
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
        logger.info("Poll created {0} {1} {2}".format(msg_poll_id, poll_owner_id, message.poll.id))

        map_msg_poll_id_to_message_id = repo.get("map_msg_poll_id_to_message_id", dict())
        map_msg_poll_id_to_message_id.update({f"{msg_poll_id}": message.poll.id})
        repo.set("map_msg_poll_id_to_message_id", map_msg_poll_id_to_message_id)
        
        message_id = message.message_id
        poll_type = CONST.POLL_TYPE_PICK_DISH
        poll_id = message.poll.id
        chat_id = update.effective_chat.id
        
        # Save some info about the poll the bot_data for later use in receive_poll_answer
        payload = {
            poll_id : {
                "time_created": time_created,
                "questions": questions,
                "message_id": message_id,
                "chat_id": chat_id,
                "answers": dict(),  # {user_id: [answer_index]}
                "poll_type": poll_type,
                "paid_state": dict(),
                "host_poll_id": host_poll_id
            }
        }
        
        poll_contain_data = PollData()
       
        poll_contain_data.set_message_id(message_id)
        poll_contain_data.set_poll_type(poll_type)
        poll_contain_data.set_questions(questions)
        poll_contain_data.set_poll_id(poll_id)
        poll_contain_data.set_chat_id(chat_id)
        poll_contain_data.set_host_poll_id(host_poll_id)
        
        if (previous_poll is not None):
            poll_contain_data.set_previous_poll_id(previous_poll.get_poll_id())
            previous_poll.set_next_poll_id(poll_id)
            poll_data_manager.update_poll_data_by_chat_id(chat_id, previous_poll)
                    
        previous_poll = poll_contain_data
        
        poll_data.update(payload)
        context.bot_data.update(payload)
        
        poll_data_manager.push_poll_data_by_chat_id(chat_id, poll_contain_data)
        if current_page == 1:
            poll_data_manager.push_poll_id_by_chat_id(chat_id, poll_contain_data)
            user_host_poll = get_user_model(update, context, host_poll_id)
            user_host_poll.add_host_history(int(poll_id))
            user_host_poll.save()

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
    poll_data_manager.save()

    random_fn = random.choice([send_random_quote, quiz_handler, quiz_handler_2])
    await random_fn(update, context)

    if alert_msg is not None:
        await update.message.reply_text(alert_msg)


async def send_random_quote(update, context):
    await update.effective_message.reply_text(quote_storate.get_random_quote())


async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    repo = get_repo_bot(context)
    all_poll_data = repo.get('poll_data', dict())
    answer = update.poll_answer
    poll_id = answer.poll_id
    answered_poll = all_poll_data.get(answer.poll_id)

    selected_options = answer.option_ids
    effective_user = update.effective_user
    effective_user_id = f'{effective_user.id}'
    host_poll_id = -1
    chat_id = -1

    

    if answered_poll is None:
        logger.info("Khong get duoc poll id")
        return
    poll_type = answered_poll["poll_type"]
    if poll_type is not None:
        if poll_type == CONST.POLL_TYPE_QUIZ_1 or poll_type == CONST.POLL_TYPE_QUIZ_2:
            logger.info("day la poll type quiz 1")
            # return
            # pass
            # elif poll_type == CONST.POLL_TYPE_QUIZ_2:
            logger.info("day la poll type quiz 2")
            logger.info(f"poll_id: {answer.poll_id}")
            user_answers = answered_poll["user_answers"]
            correct_options_id = int(answered_poll["correct_options_id"])
            one_selected_option = int(selected_options[0])
            # variable_question = answered_poll["question"]
            # string_md5_question = hashlib.md5(variable_question).hexdigest()
            payload = {
                effective_user_id: {
                    "timestamp": time.time(),
                    "answers": one_selected_option,
                    "answer_correct": (one_selected_option == correct_options_id)
                }
            }
            user_answers.update(payload)

            datetime_midnight = get_datetime_at_midnight()
            # logger.info(f"datetime_midnight : {datetime_midnight}")
            day_info_at_specific_date = repo_get_repo_bot_day_info_at_specific_date(repo, datetime_midnight)
            user_info = day_info_at_specific_date.get("user_info", dict())
            if effective_user_id not in user_info:
                payload_user_info = {
                    effective_user_id: {
                        "choose_poll": []
                    }
                }
                user_info.update(payload_user_info)

            specifict_user_info = user_info.get(effective_user_id, dict())
            choose_poll = specifict_user_info.get("choose_poll", [])
            choose_poll.append(answer.poll_id)
            user_info[effective_user_id]["choose_poll"] = choose_poll
            save_data_user_name(repo, effective_user_id, effective_user)
            # repo.save()
            return
            pass
        elif poll_type == CONST.POLL_TYPE_PICK_DISH:
            logger.info("day la poll type chon mon")
            poll_data_manager = get_poll_model(update, context, poll_id, host_poll_id, chat_id)
            chat_id = poll_data_manager.get_poll_data_by_poll_id(poll_id).get_chat_id()
            poll_data_manager.set_chat_id(chat_id)
            poll_data_container = poll_data_manager.get_poll_data_by_poll_id(poll_id)
            logger.info(f"receive_poll_answer chat_id {chat_id} poll_id {poll_id}");
            pass
        else:
            logger.info("khong thuoc cac loai tren")
            pass
    questions = answered_poll["questions"]
    answers = answered_poll["answers"]
    paid_state = repo_get_all_user_paid_state_by_poll_id(repo, answer.poll_id)

    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " + "
        else:
            answer_string += questions[question_id]

    answers[effective_user_id] = selected_options
    paid_state[effective_user_id] = -1
    poll_data_container.set_answers_by_user_id(effective_user_id, selected_options)
    save_data_user_name(repo, effective_user_id, effective_user)
    poll_data_manager.save()
    if answer_string == "":
        await context.bot.send_message(
            answered_poll["chat_id"],
            f"{effective_user.mention_html()} không chọn nữa!",
            parse_mode=ParseMode.HTML,
        )
        return

    await context.bot.send_message(
        answered_poll["chat_id"],
        f"{effective_user.mention_html()} chọn {answer_string}!",
        parse_mode=ParseMode.HTML,
    )


async def stop_polls(context, list_poll_ids, poll_owner_id):
    tasks = [context.bot.stop_poll(poll_owner_id, poll_id) for poll_id in list_poll_ids]
    await asyncio.gather(*tasks)
    for poll_id in list_poll_ids:
        logger.info("Close poll {} {}".format(poll_owner_id, poll_id))


async def close_poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Close the poll reply to the command
    message = update.effective_message.reply_to_message
    if not message or message.poll is None:
        logger.info("Poll not found")
        return

    poll_owner_id = f'{message.chat.id}'
    poll_id = f'{message.message_id}'

    logger.info("close poll poll " + poll_owner_id + " " + poll_id)

    repo = get_repo_bot(context)
    parent_poll_ids = repo.get('parent_poll_ids', dict()).get(poll_owner_id, dict())
    poll_group_ids = repo.get('poll_group_ids', dict()).get(poll_owner_id, dict())

    parent_id = parent_poll_ids.get(poll_id)
    list_poll_ids = poll_group_ids.get(parent_id)

    await stop_polls(context, list_poll_ids, poll_owner_id)

    await message.reply_text(
        f"{len(list_poll_ids)} Poll closed by {update.effective_user.mention_html()}",
        parse_mode=ParseMode.HTML
    )

    await checkbill_handler(update, context)


async def info_poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Info poll reply to the command
    message = update.effective_message.reply_to_message
    logger.info("Info poll " + str(message.chat.id) + " " + str(message.message_id))

    msg = "Kết quả poll:\n"
    for option in message.poll.options:
        if option.voter_count > 0:
            msg += f"{option.text}: {option.voter_count}\n"
    await message.reply_text(msg)


#     TODO: Add bill handler

async def delete_polls(context, list_poll_ids, poll_owner_id):
    tasks = [context.bot.delete_message(poll_owner_id, poll_id) for poll_id in list_poll_ids]
    await asyncio.gather(*tasks)
    for poll_id in list_poll_ids:
        logger.info("Delete poll {} {}".format(poll_owner_id, poll_id))


async def delete_poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Delete poll reply to the command
    message = update.effective_message.reply_to_message
    if not message or message.poll is None:
        logger.info("Poll not found")
        return

    poll_owner_id = f'{message.chat.id}'
    poll_id = f'{message.message_id}'

    logger.info("Info poll " + poll_owner_id + " " + poll_id)

    repo = get_repo_bot(context)
    parent_poll_ids = repo.get('parent_poll_ids', dict()).get(poll_owner_id, dict())
    poll_group_ids = repo.get('poll_group_ids', dict()).get(poll_owner_id, dict())

    parent_id = parent_poll_ids.get(poll_id)
    list_poll_ids = poll_group_ids.get(parent_id, list())

    await delete_polls(context, list_poll_ids, poll_owner_id)


# dice_handler
async def dice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    limit = int(update.effective_message.text.split(' ')[1])
    limit = max(1, min(limit, 20))
    for i in range(0, limit):
        await update.effective_message.reply_dice()


async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = await quiz_loader.get_quiz_api()
    print("Question is", question)
    options = question['answers']
    randint = question['correct']
    message = await update.effective_message.reply_poll(
        question=question['question'],
        options=options,
        is_anonymous=False,
        type=Poll.QUIZ,
        correct_option_id=randint,
        explanation="Đáp án đúng là {}".format(options[randint]),
    )
    save_data_for_quiz(update, context, message, question, CONST.POLL_TYPE_QUIZ_1)


async def quiz_handler_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # logger.info(f"quiz_handler_2 update: {update}")
    # logger.info("Question is", question)
    # logger.info(f"update.effective_user {update.effective_user}")
    # logger.info(f"update.effective_message {update.effective_message}")
    # logger.info(f"update.message {update.message}")
    # logger.info(f"update.effective_message {update.effective_message}")
    message_text = update.message.text
    # logger.info(f'message text: {message_text}')
    regex_message_text = r"^([^ ]+)\s(\d+)(.*)$"

    question = None
    if message_text is not None:
        match = re.match(regex_message_text, message_text)
        if match is not None:
            part1 = match.group(1)
            part2 = match.group(2)
            if part2 is not None:
                paramChoice = int(part2) % 2
                # logger.info(f'message text: {message_text} {part1} {part2} {paramChoice}')
                question = await quiz_loader.get_quiz_api_2(paramChoice)
    else:
        pass
    if question is None:
        question = await quiz_loader.get_quiz_api_2()

    options = question['answers']
    randint = question['correct']
    logger.info(f"Question: {question}")
    logger.info(f"answers: {options}")
    message = await update.effective_message.reply_poll(
        question=question['question'],
        options=options,
        is_anonymous=False,
        type=Poll.QUIZ,
        correct_option_id=randint,
        explanation="Đáp án đúng là {}".format(options[randint]),
    )
    save_data_for_quiz(update, context, message, question, CONST.POLL_TYPE_QUIZ_2)


# quote_handler
async def quote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_random_quote(update, context)


async def rank_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo = get_repo_bot(context)
    table_data = rank_handlers.stat_at_day_index(repo)
    table_str = "----------" + datetime.now().strftime("%Y-%b-%d") + "----------" + "\n"
    table_str += tabulate(table_data, headers="firstrow", tablefmt='orgtbl', showindex=False)
    await update.effective_message.reply_text(text=f"<pre>{table_str}</pre>", parse_mode=ParseMode.HTML)
    pass


async def repeat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    num_repeat = int(update.effective_message.text.split(' ')[1])
    num_repeat = max(1, min(num_repeat, 20))

    # get message to repeat
    message = update.effective_message.reply_to_message
    if message is None:
        content = update.effective_message.text.split(' ', 2)[2]
        for i in range(0, num_repeat):
            await context.bot.send_message(update.effective_chat.id, content)
        return

    # repeat message
    for i in range(0, num_repeat):
        await context.bot.copy_message(update.effective_chat.id, update.effective_chat.id, message.message_id)


async def bill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(f"Xin chào {update.effective_user.mention_html()}",
                                              parse_mode=ParseMode.HTML)
    pass


def get_poll_data_by_message_id(context: ContextTypes.DEFAULT_TYPE, message_id):
    repo = get_repo_bot(context)
    all_poll_data = repo.get("poll_data", dict())
    for poll_id in all_poll_data:
        poll_data = all_poll_data[poll_id]
        if "message_id" in poll_data and str(poll_data["message_id"]) == message_id:
            return poll_data
    return {}


async def checkbill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo = get_repo_bot(context)
    val_return = get_poll_owner_id_message_id(update, context)
    if val_return is None:
        return
        
    poll_owner_id = val_return["poll_owner_id"]
    message_id = val_return["message_id"]

    logger.info("checkbill_handler Info poll " + poll_owner_id + " " + message_id)
    # poll_data = get_poll_data_by_message_id(context, message_id)

    # list of dictionaries representing table rows
    # list of dictionaries representing table rows
    table_data = [
    ]
    
    poll_data_manager = get_poll_model(update, context, -1, -1, -1)


    chat_id_names = repo.compute_if_absent('chat_id_names', lambda k: dict())
    list_poll_ids = poll_data_manager.get_list_poll_id_follow_message_id(message_id)

    logger.info(f"list_poll_ids {list_poll_ids}")
    if (list_poll_ids is None or len(list_poll_ids) <= 0):
        strLocal = "Check bill hơi xa rồi đó không có data!"
        await update.effective_message.reply_text(text=f"{strLocal}", parse_mode=ParseMode.HTML)
        return
        
    subtotal_int = 0
    poll_data = None
    
    for poll_id in list_poll_ids:
        poll_data = poll_data_manager.get_poll_data_by_poll_id(poll_id)
        if poll_data is not None:
            for key_answer in poll_data.get_answers():
                list_answer_of_this_user = poll_data.get_answers()[key_answer]
                logger.info(f"checkbill_handler key_answer {key_answer}")
                logger.info(f"checkbill_handler list_answer_of_this_user {list_answer_of_this_user}")
                paid_state = 0
                if key_answer in poll_data.get_paid_state():
                    if poll_data.get_paid_state()[key_answer] is not None:
                        paid_state = int(poll_data.get_paid_state()[key_answer])

                for i in list_answer_of_this_user:
                    string_answer = poll_data.get_questions()[i]
                    match = re.match(r'^(.*)\s(\d{1,3}([,.]\d{3})*).*$', string_answer)
                    if match:
                        part1_dish = match.group(1)
                        price_str = match.group(2)  # price
                        price_int = int(remove_non_digits(price_str))
                        price_str_format = '{:,.0f}'.format(price_int) + "\u0111"
                        name = chat_id_names.get(key_answer, key_answer)
                        if paid_state > 0:
                            is_paid = "PAID"
                        else:
                            is_paid = "No_PAID"

                        row = [0, f"{name}", part1_dish, price_str_format, is_paid]
                        table_data.append(row)
                        subtotal_int += price_int
                    

    # sort table by dish name
    table_data = sorted(table_data, key=lambda x: x[2])

    # recalculate the index
    index = 0
    for row in table_data:
        index += 1
        row[0] = index

    headers = ["STT", "Name", "Dish", "Price", "Paid"]
    # add first row as a header
    table_data.insert(0, headers)

    # list of column headers
    subtotal_str = "{0}đ".format('{:,.0f}'.format(subtotal_int))

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
    str_header = f"{date_at_midnight_at_time_created}\nHost: {host_user_name} - {description}"
    await update.effective_message.reply_text(text=f"<pre>{str_header}\n{table_str}</pre>", parse_mode=ParseMode.HTML)
    pass


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/poll url để tạo một bình chọn, các trang hỗ trợ là: shopeefood, grabfood\n"
        "/close để đóng bình chọn.\n"
        "/info để lấy thông tin của bình chọn.\n"
        "/bill để tạo một hóa đơn cho bình chọn.\n"
        "/checkbill để kiểm tra hóa đơn của bình chọn.\n"
        "/paid để đánh dấu hóa đơn đã thanh toán.\n"
        "/delete để xóa bình chọn.\n"
        "/help để lấy tin nhắn này.\n"
        "/dice để tạo một số ngẫu nhiên.\n"
        "/quiz để tạo một bài trắc nghiệm.\n"
        "/quiz2 để tạo một bài trắc nghiệm ver2 /quiz2 [1,2,3].\n"
        "/quote để lấy một câu trích dẫn ngẫu nhiên.\n"
        "/checkin để tạo một bình chọn checkin.\n"
        "/test để tạo một bình chọn test.\n"
        "/meme để lấy một meme ngẫu nhiên.\n"
        "/start_roll để bắt đầu roll.\n"
        "/info_roll để xem thông tin roll.\n"
        "/finish_roll để kết thúc roll.\n"
        "/repeat [n] để lặp lại tin nhắn n lần.\n"
        "/rank để xem thống kê.\n"
        "Star github: https://github.com/thienchidh/shopyfood\n"
    )

    # Define the commands that your bot will support
    commands = [
        BotCommand("start", "Bắt đầu bot"),
        BotCommand("poll", "Tạo một bình chọn, các trang hỗ trợ là: shopeefood, grabfood"),
        BotCommand("close", "Đóng bình chọn"),
        BotCommand("info", "Lấy thông tin của bình chọn"),
        BotCommand("bill", "Tạo một hóa đơn cho bình chọn"),
        BotCommand("checkbill", "Kiểm tra hóa đơn của bình chọn"),
        BotCommand("paid", "Đánh dấu hóa đơn đã thanh toán"),
        BotCommand("delete", "Xóa bình chọn"),
        BotCommand("dice", "Chơi game xúc xắc"),
        BotCommand("help", "Lấy tin nhắn này"),
        BotCommand("quiz", "Chơi game trắc nghiệm"),
        BotCommand("quiz2", "Trắc nghiệm đa lĩnh vực"),
        BotCommand("quote", "Lấy một câu trích dẫn ngẫu nhiên"),
        BotCommand("checkin", "Tạo một bình chọn checkin"),
        BotCommand("test", "Tạo một bình chọn test"),
        BotCommand("meme", "Lấy một meme ngẫu nhiên"),
        BotCommand("start_roll", "Bắt đầu roll"),
        BotCommand("info_roll", "Xem thông tin roll"),
        BotCommand("finish_roll", "Kết thúc roll"),
        BotCommand("repeat", "Lặp lại tin nhắn n lần"),
        BotCommand("rank", "Để xem thống kê"),
    ]
    await context.bot.set_my_commands(commands)


async def checkin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    full_name = update.effective_user.full_name
    user_id = update.message.from_user.id
    user_name = update.effective_message.from_user.username
    user = get_user_model(update, context, user_id)
    user.add_user_name(user_name)
    description = ""
    
    
    message = update.effective_message
    logger.info(f"message checkin handler: {message}")
    if not message or message.poll is None:
        message_text = update.message.text
        logger.info(f"update.message.text: {message_text}")
        regex_message_text = r'(/[@\w]+)\s(.*)'
        if message_text is not None:
            match = re.match(regex_message_text, message_text)
            logger.info(f"match {match}")
            if match is not None:
                part1 = match.group(1)
                part2 = match.group(2)
                if part1 is not None and part2 is not None:
                    description = part2
                    user.add_description(description)
            else:
                description = user.get_description()    
   
    user.save()
    
    """Display a help message"""
    level = user.level
    exp = user.exp
    host_count = user.get_host_times()
    strText = f"ChatId: {chat_id}\n" 
    strText += f"user_name: {user_name}\n"
    strText += f"user_id: {user_id}\n"
    strText += f"level: {level}\n"
    strText += f"exp: {exp}\n" 
    strText += f"Host times: {host_count}\n"
    strText += f"Description: {description}\n"
    await update.message.reply_text(strText)


async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_message.id
    bot = context.bot
    try:
        bot_get_me_str = await bot.getMe()
        await update.message.reply_text(bot_get_me_str)
        # get all member ids in the group
        # members = bot.getChatMemberCount(chat_id)
        # members = await bot.getChatMember(chat_id)
        # members_0 = members[0]
        # members_0_str = json.dumps(members_0)
        # await update.message.reply_text(members_0_str)
        # member_ids = [member.user.id for member in bot.getChatMember(chat_id)]

        # loop through all members and get their info
        # for member_id in member_ids:
        #     member = bot.get_chat_member(chat_id, member_id)
        #     update.message.reply_text(f'{member.user.first_name} {member.user.last_name} ({member.user.username})')
        # add any other info you want to retrieve for each member

    except TelegramError as e:
        # logger.error(f"Error getting member info: {e}")
        await update.message.reply_text("Error getting member info")


def main() -> None:
    """Run bot."""
    bot_token = yaml.load(open('./config/config.yml'), Loader=yaml.FullLoader)['telegram']['token']

    tracemalloc.start()

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", help_handler))
    application.add_handler(CommandHandler("poll", poll))
    application.add_handler(CommandHandler("close", close_poll_handler))
    application.add_handler(CommandHandler("info", info_poll_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("bill", bill_handler))
    application.add_handler(CommandHandler("checkbill", checkbill_handler))
    application.add_handler(CommandHandler("paid", paid_handler))
    application.add_handler(CommandHandler("delete", delete_poll_handler))
    application.add_handler(CommandHandler("dice", dice_handler))
    application.add_handler(CommandHandler("checkin", checkin_handler))
    application.add_handler(CommandHandler("test", test_handler))
    application.add_handler(CommandHandler("quiz", quiz_handler))
    application.add_handler(CommandHandler("quiz2", quiz_handler_2))
    application.add_handler(CommandHandler("quote", quote_handler))
    application.add_handler(CommandHandler("repeat", repeat_handler))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.add_handler(CommandHandler("meme", logic_handlers.handle_chui))
    application.add_handler(CommandHandler("start_roll", logic_handlers.handle_start_game))
    application.add_handler(CommandHandler("info_roll", logic_handlers.handle_info_game))
    application.add_handler(CommandHandler("finish_roll", logic_handlers.handle_finish_game))
    application.add_handler(MessageHandler(filters.Dice.DICE, logic_handlers.handle_roll))
    application.add_handler(CommandHandler("rank", rank_handler))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler('admin', admin_only_command))
    application.add_handler(CommandHandler('moderator', moderator_only_command))
    application.add_handler(CommandHandler('public', public_command))
    application.add_handler(CommandHandler('remind', remind_paid_handler))
    application.add_handler(CommandHandler("paid_poll", paid_poll_handler))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
