import asyncio
import json
import logging
from re import L
import re
from tabulate import tabulate


import yaml
from telegram import (
    ReplyKeyboardRemove,
    Update, BotCommand, Poll,
)
from telegram.error import TelegramError

from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    filters,
)

import crawl_grabfood
import crawl_shopeefood
import quote_storate
from repository import KeyValRepository

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

strategies = [
    crawl_shopeefood,
    crawl_grabfood,
]


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
        logger.info("Poll created {0} {1} {2}".format(msg_poll_id, poll_owner_id, message.poll.id))

        # Save some info about the poll the bot_data for later use in receive_poll_answer
        payload = {
            message.poll.id: {
                "questions": questions,
                "message_id": message.message_id,
                "chat_id": update.effective_chat.id,
                "answers": dict(),  # {user_id: [answer_index]}
            }
        }
        poll_data.update(payload)
        context.bot_data.update(payload)

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

    await send_random_quote(context, update)


async def send_random_quote(context, update):
    await update.message.reply_text(quote_storate.get_random_quote())
    # await context.bot.sendDice(update.effective_chat.id, emoji='🎲')
    # send random a quote
    # TODO
    pass


def get_repo_user(user_id, context: ContextTypes.DEFAULT_TYPE) -> KeyValRepository:
    repo = context.user_data.get(user_id)
    if not repo or repo is not KeyValRepository:
        repo = KeyValRepository(user_id)
        context.user_data[user_id] = repo
    return repo


def get_repo_bot(context: ContextTypes.DEFAULT_TYPE) -> KeyValRepository:
    repo = context.bot_data.get('bot')
    if not repo or repo is not KeyValRepository:
        repo = KeyValRepository('bot')
        context.bot_data['bot'] = repo
    return repo


async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    repo = get_repo_bot(context)
    all_poll_data = repo.get('poll_data', dict())
    answer = update.poll_answer
    logger.info(f"receive_poll_answer answers {update.poll_answer}")
    answered_poll = all_poll_data.get(answer.poll_id)
    questions = answered_poll["questions"]
    answers = answered_poll["answers"]
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " + "
        else:
            answer_string += questions[question_id]

    effective_user = update.effective_user
    effective_user_id = f'{effective_user.id}'
    answers[effective_user_id] = selected_options
    repo.save()
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


async def receive_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """On receiving polls, reply to it by a closed poll copying the received poll"""
    actual_poll = update.effective_message.poll
    logger.info('receive_poll', actual_poll.id)
    # Only need to set the question and options, since all other parameters don't matter for
    # a closed poll
    await update.effective_message.reply_poll(
        question=actual_poll.question,
        options=[o.text for o in actual_poll.options],
        # with is_closed true, the poll/quiz is immediately closed
        is_closed=True,
        reply_markup=ReplyKeyboardRemove(),
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

    logger.info("Info poll " + poll_owner_id + " " + poll_id)

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

    # Get results of the poll
    msg = "Kết quả poll:\n"
    for option in message.poll.options:
        if option.voter_count > 0:
            msg += f"{option.text}: {option.voter_count}\n"
    await message.reply_text(msg)


async def info_poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Info poll reply to the command
    message = update.effective_message.reply_to_message
    logger.info("Info poll " + str(message.chat.id) + " " + str(message.message_id))

    msg = "Kết quả poll:\n"
    for option in message.poll.options:
        if option.voter_count > 0:
            msg += f"{option.text}: {option.voter_count}\n"
    await message.reply_text(msg)


async def paid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message.reply_to_message
    if message is None or message.poll is None:
        await update.message.reply_text(f'{update.effective_user.mention_html()} Trả cho poll nào thế?',
                                        parse_mode=ParseMode.HTML)
        return


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


async def game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    limit = int(update.effective_message.text.split(' ')[1])
    limit = max(1, min(limit, 10))
    for i in range(0, limit):
        await context.bot.sendDice(update.effective_chat.id)


async def bill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("Khai code 2")
    repo = get_repo_bot(context);
    # parent_poll_ids = repo.get('parent_poll_ids', dict()).get(poll_owner_id, dict())
    # poll_group_ids = repo.get('poll_group_ids', dict()).get(poll_owner_id, dict())

    # logger.info(f"parent_poll_ids: {parent_poll_ids}")
    # logger.info(f"poll_group_ids: {poll_group_ids}")
    logger.info(update.effective_user.full_name)
    # await update.effective_message.reply_text(f"repo : {json.dumps(repo)}")
    await update.effective_message.reply_text(f"update.effective_user.full_name : {update.effective_user.full_name}")
     
    pass



def get_poll_data_by_message_id(context: ContextTypes.DEFAULT_TYPE, message_id):
    repo = get_repo_bot(context)
    all_poll_data = repo.get("poll_data", dict())
    for poll_id in all_poll_data:
        poll_data = all_poll_data[poll_id]
        #logger.info(f'value {poll_data.get("message_id", None)}')
        #logger.info(f'value of message_id {message_id}')
        #logger.info(f'type of poll_data message id {type(poll_data.get("message_id", None))}')
        #logger.info(f'type of message_id {type(message_id)}')
        #logger.info(f'type of ep kieu id {type(str(poll_data.get("message_id", None)))}')
        if ("message_id" in poll_data and str(poll_data["message_id"]) == message_id):
            #logger.info(f"foundedget_poll_data_by_message_id {poll_data} message_id {message_id}")
            return poll_data
    return {}



async def checkbill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message.reply_to_message
    if not message or message.poll is None:
        logger.info("checkbill_hander Poll not found");
        return

    poll_owner_id = f'{message.chat.id}'
    message_id = f'{message.message_id}'   

    logger.info("Info poll " + poll_owner_id + " " + message_id)
    poll_data = get_poll_data_by_message_id(context, message_id)
    repo = get_repo_bot(context)
    parent_poll_ids = repo.get('parent_poll_ids', dict()).get(poll_owner_id, dict())
    poll_group_ids = repo.get('poll_group_ids', dict()).get(poll_owner_id, dict())

    # list of dictionaries representing table rows
    # list of dictionaries representing table rows
    headers = ["STT", "Name", "Dish", "Price"]
    table_data = [
        headers,
        # {"STT": 1, "Name": "John", "Dish": "Pizza", "Price": 10.99},
        # [1, "John", "Pizza", 10.99],
        # [1, "John", "Pizza", 10.99]
    ]
    parent_id = parent_poll_ids.get(message_id)
    # List all poll that have common parent
    list_poll_ids = poll_group_ids.get(parent_id)
    # tong hop data tung poll

    logger.info(f"list_poll_ids {list_poll_ids}")
    index = 0
    subtotal_int = 0
    for message_id in list_poll_ids:
        poll_data = get_poll_data_by_message_id(context, message_id)
        logger.info(f"poll_data {poll_data}")
        if ("answers" in poll_data):
            for key in poll_data["answers"]:
                if ("questions" in poll_data):
                    list_answer_of_this_user = poll_data["answers"].get(key)
                    logger.info(f"list_answer_of_this_user {list_answer_of_this_user}")
                    for i in list_answer_of_this_user:
                        string_answer = poll_data["questions"][i]
                        match = re.match(r'^(.*?)(\d{1,3}(,\d{3})*)\s*(.*?)$', string_answer)
                        if match:
                            index += 1
                            part1 = match.group(1)
                            price_str = part2 = match.group(2) # price
                            price_int = int(price_str.replace(",", ""))
                            part3 = match.group(4)
                            row = [index, f"{key}", part1, part2 + part3]
                            table_data.append(row)
                            subtotal_int += price_int;

                    pass



   
    

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

    table_str = tabulate(table_data, headers="firstrow", tablefmt='orgtbl', showindex=False)
    
    # await update.effective_message.reply_document(open('./config/mp4.mp4', 'rb'))


    await update.effective_message.reply_text(text=f"<pre>{table_str}</pre>", parse_mode=ParseMode.HTML)
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
    )


async def checkin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    full_name = update.effective_user.full_name
    user_name = update.effective_message.from_user.username
    repo_user = get_repo_user(chat_id, context)
    list_user_name = repo_user.get("user_name", [])
    list_user_name.append(user_name)
    repo_user.set("user_name", list_user_name)
    repo_user.save()
    """Display a help message"""
    await update.message.reply_text(
        f'Id {chat_id} user_name = {user_name}')

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
    application.add_handler(CommandHandler("dice", game_handler))
    application.add_handler(CommandHandler("checkin", checkin_handler))
    application.add_handler(CommandHandler("test", test_handler))
    application.add_handler(MessageHandler(filters.POLL, receive_poll))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
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
        BotCommand("test", "Test Bot"),
    ]
    application.bot.set_my_commands(commands)
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
