import asyncio
from asyncio.log import logger
import math
import random

from telegram import (
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from util import generate_random_id

from . import bot_session

import time
import threading
import random
import datetime
from itertools import combinations


emoji_list = [
    "👿", "👹", "👺", "💀", "👻", "👽", "🤖", "😺", "😸", "😹"
    ]

sampled_combinations = None

def generate_unique_combos():
    global sampled_combinations
    if (sampled_combinations is not None):
        return sampled_combinations       
    
    unique_combos = []

    # Generate all possible unique combinations of 6 emoji
    all_combinations = list(combinations(emoji_list, 6))

    # Randomly sample 100 unique combinations from the list
    sampled_combinations = random.sample(all_combinations, 100)
    return sampled_combinations
    


async def dice_animation(rolling_message, sampled_combinations):
    for i in range(5):  # Roll the dice 5 times for the animation
        await asyncio.sleep(0.1)  # Wait for 1 second
        value = random.randint(0, 99)
        combo_str = ''.join(sampled_combinations[value])
        await rolling_message.edit_text(f'Rolling: {combo_str}')
    final_value = random.randint(1, 6)
    await rolling_message.edit_text(f'Final dice value: {final_value}')
    
async def dice_roll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    print(f"Roll in chat_id {chat_id}")
    array = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚄']
    rolling_message = await update.message.reply_text(f'Rolling the dice...{array[0]}')
    sampled_combinations = generate_unique_combos()
    
    asyncio.create_task(dice_animation(rolling_message, sampled_combinations))    
    
    
# async def dice_roll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     print("Roll in chat_id", update.message.chat_id)
#     array = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚄']
#     rolling_message = await update.message.reply_text(f'Rolling the dice...{array[0]}')
#     sampled_combinations = generate_unique_combos()
#     # logger.info(f"sampled_combinations: {sampled_combinations}")
    
#     async def dice_animation():
#         for i in range(5):  # Roll the dice 5 times for the animation
#             time.sleep(1)  # Wait for 1 second
#             # value = random.randint(0, 5)  # Generate a random number between 1 and 6
#             value = random.randint(0, 99)
#             combo_str = ''.join(sampled_combinations[value + i])
#             # logger.info(f"combo_str: {combo_str}")

#             await rolling_message.edit_text(f'Rolling: {combo_str}')
#         final_value = random.randint(1, 6)
#         await rolling_message.edit_text(f'Final dice value: {final_value}')
#     await dice_animation()        
    
    

