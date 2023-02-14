# load all from config/quotes
import random


def load_quotes():
    quotes = []
    with open("./config/quotes", "r") as f:
        quotes.extend(f.readlines())
    return quotes


quotes = load_quotes()


def get_random_quote():
    return random.choice(quotes)
