from telegram import Update
from telegram.ext import CallbackContext

from util import *


async def paid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    val_return = get_poll_owner_id_message_id(update, context)
    if (val_return is None):
        return

    poll_data_manager = get_poll_model(update, context, -1, -1, -1)
    poll_data = None

    user_paid_id = update.effective_user.id
    poll_owner_id = val_return["poll_owner_id"]
    message_id = val_return["message_id"]
    repo = get_repo_bot(context)
    poll_id = repo_get_poll_id_by_message_id(repo, message_id)
    host_poll_id = repo_get_host_poll_id_by_poll_id(repo, poll_id)
    host_user_name = repo_get_user_name_by_user_id(context, host_poll_id)
    logger.info(f"paid handler poll_owner_id : {poll_owner_id}")
    logger.info(f"paid handler message_id : {message_id}")
    logger.info(f"paid handler host_poll_id : {host_poll_id}")
    logger.info(f"paid handler user_name : {host_user_name}")


    list_poll_ids = poll_data_manager.get_list_poll_id_follow_message_id(message_id)

    logger.info(f"paid handler list_poll_ids : {list_poll_ids}")

    headers = ["STT", "Name", "Dish", "Price", "Paid"]
    table_data = [
        headers,
    ]
    subtotal_int = 0

    for poll_id in list_poll_ids:
        poll_data = poll_data_manager.get_poll_data_by_poll_id(poll_id)

        if poll_data is not None:
            logger.info(f"user_paid_id {user_paid_id}")
            logger.info(f"poll_id {poll_id}")

            for key in poll_data.get_answers():
                list_answer_of_this_user = poll_data.get_answers()[key]
                logger.info(f"list_answer_of_this_user {list_answer_of_this_user}")
                if (str(key) == str(user_paid_id)):
                    poll_data.set_paid_state_by_user_id(user_paid_id, 1)
                    repo.save()

    poll_data_manager.save()
    # list of column headers
    subtotal_str = '{:,.0f}'.format(subtotal_int) + "\u0111"

    # calculate the subtotal
    # subtotal = sum(row["Price"] for row in table_data)
    subtotal_row = ["-", "-", f"-", "-"]
    table_data.append(subtotal_row)
    # add a row for the subtotal
    subtotal_row = ["", "", f"Subtotal {subtotal_str}", ""]
    table_data.append(subtotal_row)

    time_created = -1 if poll_data is None else poll_data.get_time_created()
    host_poll_id = -1 if poll_data is None else poll_data.get_host_poll_id()

    date_at_midnight_at_time_created = get_datetime_at_midnight_at_timestamp(time_created)
    host_user_name = repo_get_user_name_by_user_id(context, host_poll_id)
    description = repo_get_description_by_user_id(context, host_poll_id)

    paid_user_name = update.effective_user.name
    str_header = f"{paid_user_name} da paid cho:\n{date_at_midnight_at_time_created}\nHost: {host_user_name} - {description}"
    await update.effective_message.reply_text(text=f"<pre>{str_header}\n</pre>", parse_mode=ParseMode.HTML)


# Define a callback query handler function
async def button_click(update: Update, context: CallbackContext):
    """Handle button click events."""
    query = update.callback_query
    await query.answer()
    logger.info(f"button click update: {update}")
    logger.info(f"button click query {query}")

    # Perform actions based on the button clicked
    if query.data == 'button1':
        logger.info("Button 1 clicked")
        await query.edit_message_text(text='Button 1 clicked!')
    elif query.data == 'button2':
        logger.info("Button 2 clicked")
        await query.edit_message_text(text='Button 2 clicked!')
    elif query.data == 'button3':
        logger.info("Button 3 clicked!")
        await query.edit_message_text(text='Button 3 clicked!')
