import asyncio
import json
import logging

import yaml
from telegram import (
    ReplyKeyboardRemove,
    Update,
)
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
import modules.logic_handlers as logic_handlers
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
    print("Khai code")
    pass


async def checkbill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_document(open('./config/mp4.mp4', 'rb'))
    pass


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a help message"""
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


def main() -> None:
    """Run bot."""
    bot_token = yaml.load(open('./config/config.yml'), Loader=yaml.FullLoader)['telegram']['token']

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()
    # application.add_handler(CommandHandler("start", help_handler))
    # application.add_handler(CommandHandler("poll", poll))
    # application.add_handler(CommandHandler("close", close_poll_handler))
    # application.add_handler(CommandHandler("info", info_poll_handler))
    # application.add_handler(CommandHandler("help", help_handler))
    # application.add_handler(CommandHandler("bill", bill_handler))
    # application.add_handler(CommandHandler("checkbill", checkbill_handler))
    # application.add_handler(CommandHandler("paid", paid_handler))
    # application.add_handler(CommandHandler("delete", delete_poll_handler))
    # application.add_handler(CommandHandler("dice", game_handler))
    # application.add_handler(MessageHandler(filters.POLL, receive_poll))
    # application.add_handler(PollAnswerHandler(receive_poll_answer))

    application.add_handler(CommandHandler("chui", logic_handlers.handle_chui))
    application.add_handler(CommandHandler("start_roll", logic_handlers.handle_start_game))
    application.add_handler(CommandHandler("info_roll", logic_handlers.handle_info_game))
    application.add_handler(CommandHandler("finish_roll", logic_handlers.handle_finish_game))
    # application.add_handler(MessageHandler(filters.Sticker.ALL, logic_handlers.handle_sticker))
    application.add_handler(MessageHandler(filters.Dice.DICE, logic_handlers.handle_roll))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
