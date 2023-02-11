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


def attempt_crawl(url):
    for strategy in strategies:
        if strategy.is_support_url(url):
            return strategy.process(url)
    return None


async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    url = text.split(' ')[1]
    obj = attempt_crawl(url)
    if obj is None:
        await update.message.reply_text('Not support url')
        return

    title = obj[0]
    items = obj[1]

    # Split items into 10 items per poll
    limit_items_per_poll = 10
    items_split = [items[i:i + limit_items_per_poll] for i in range(0, len(items), limit_items_per_poll)]
    print(json.dumps(items_split))

    # Ensure last poll has at least 2 items and at most 10 items
    if len(items_split[-1]) < 2:
        items_split[-1].append(items_split[-2].pop())

    print(json.dumps(items_split))

    # Create poll for each item
    current_page = 0
    for items in items_split:
        current_page += 1
        questions = []
        limit_question = limit_items_per_poll

        for item in items:
            limit_question -= 1
            if limit_question == -1:
                break

            questions.append(item['name'] + ' ' + item['price'])

        if len(questions) < 2:
            await update.message.reply_text('Không có đủ món ăn để tạo poll')
            return

        # add page to poll title if there are more than 1 page
        pool_title = title
        if len(items_split) > 1:
            pool_title += ' - P' + str(current_page)

        message = await context.bot.send_poll(
            update.effective_chat.id,
            pool_title,
            questions,
            is_anonymous=False,
            allows_multiple_answers=False,
        )
        # Save some info about the poll the bot_data for later use in receive_poll_answer
        payload = {
            message.poll.id: {
                "questions": questions,
                "message_id": message.message_id,
                "chat_id": update.effective_chat.id,
                "answers": 0,
            }
        }
        context.bot_data.update(payload)
        print("Poll created " + str(message.message_id) + " " + str(update.effective_chat.id))


def get_repo_user(user_id, context: ContextTypes.DEFAULT_TYPE) -> KeyValRepository:
    repo = context.user_data[user_id]
    if not repo or repo is not KeyValRepository:
        repo = KeyValRepository(user_id)
        context.user_data[user_id] = repo
    return repo


def get_repo_bot(context: ContextTypes.DEFAULT_TYPE) -> KeyValRepository:
    repo = context.bot_data['bot']
    if not repo or repo is not KeyValRepository:
        repo = KeyValRepository('bot')
        context.bot_data['bot'] = repo
    return repo


async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]
    try:
        questions = answered_poll["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " and "
        else:
            answer_string += questions[question_id]

    if answer_string == "":
        return

    await context.bot.send_message(
        answered_poll["chat_id"],
        f"{update.effective_user.mention_html()} chọn {answer_string}!",
        parse_mode=ParseMode.HTML,
    )

    user_repo = get_repo_user(update.effective_user.id, context)

    answered_poll["answers"] += 1
    # Close poll after three participants voted
    # if answered_poll["answers"] == 3:
    #     await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])


async def receive_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """On receiving polls, reply to it by a closed poll copying the received poll"""
    actual_poll = update.effective_message.poll
    # Only need to set the question and options, since all other parameters don't matter for
    # a closed poll
    await update.effective_message.reply_poll(
        question=actual_poll.question,
        options=[o.text for o in actual_poll.options],
        # with is_closed true, the poll/quiz is immediately closed
        is_closed=True,
        reply_markup=ReplyKeyboardRemove(),
    )


async def close_poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Close the poll reply to the command
    message = update.effective_message.reply_to_message
    if message.poll.is_closed:
        return

    print("Close poll " + str(message.chat.id) + " " + str(message.message_id))
    await context.bot.stop_poll(message.chat.id, message.message_id)

    await message.reply_text("Poll closed by " + update.effective_user.mention_html(), parse_mode=ParseMode.HTML)

    # Get results of the poll
    msg = "Poll results:\n"
    for option in message.poll.options:
        if option.voter_count > 0:
            msg += f"{option.text}: {option.voter_count}\n"
    await message.reply_text(msg)


async def info_poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Info poll reply to the command
    message = update.effective_message.reply_to_message
    print("Info poll " + str(message.chat.id) + " " + str(message.message_id))

    msg = "Poll results:\n"
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


async def bill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def checkbill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a help message"""
    await update.message.reply_text(
        "Use /poll url to create a poll, supported sites are: shopeefood, grabfood\n"
        "Use /close to close the poll.\n"
        "Use /info to get info of the poll.\n"
        "Use /bill to create a bill for the poll.\n"
        "Use /checkbill to check the bill of the poll.\n"
        "Use /paid to mark the bill as paid.\n"
        "Use /help to get this message.\n"
    )


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
    application.add_handler(MessageHandler(filters.POLL, receive_poll))
    application.add_handler(PollAnswerHandler(receive_poll_answer))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
