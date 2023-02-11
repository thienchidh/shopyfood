import time

current_message = []


def add_action(message):
    current_message.append(message)


def loop():
    list = []
    # drain to local list
    while len(current_message) > 0:
        list.append(current_message.pop())

    # process list
    for message in list:
        print(message)


while True:
    try:
        loop()
    except Exception as e:
        print(e)
    finally:
        time.sleep(0.05)
