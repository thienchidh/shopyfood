import json
import random
import requests
import os


data = []

cacheData = {}
previousChoice = 0



async def load_config():
    with open('config/quiz.json') as f:
        data = json.load(f)
        return data

async def load_config_path(path):
    if path in cacheData:
        return cacheData[path]

    with open(f'{path}') as f:
        data = json.load(f)
        cacheData[path] = data
        return data

async def get_quiz():
    questions = await load_config()
    data_question = random.choice(questions)
    return {
        'question': data_question['question'],
        'answers': data_question['answers'],
        'correct': data_question['correct_answer']
    }
    
stacks = []
url = "https://opentdb.com/api.php?amount=10&type=multiple"

async def get_quiz_api():
    if len(stacks) > 0:
        return stacks.pop(0)
    res = requests.get(url)
    data = res.json()
    print("responseX", data)
    results = data['results']
    for result in results:
        answers = result['incorrect_answers']
        correct_answer = result['correct_answer']
        answers = answers + [correct_answer]
        random.shuffle(answers)
        correct = answers.index(correct_answer)
        question = str(result['question'])
        question = question.replace("&quot;", "\"")
        question = question.replace("&#039;", "\'")

        stacks.append({
            "question" : question,
            "answers" : answers,
            "correct": correct
        })
    return stacks.pop(0)


async def get_file_name_by_choice(choice = -1):
    if choice == 0:
        return "quiz_history_12.json"
        pass
    elif choice == 1:
        return "basic_of_vietnamese_culture.json"
        pass
    else:
        return "quiz_history_12.json"
        pass

async def get_quiz_api_2(choice = -1):
    global previousChoice
    if choice == -1:
        choice = previousChoice
    file_name = await get_file_name_by_choice(choice)
    previousChoice = choice
    file_path = os.path.join("config", f"{file_name}")
    questions = await load_config_path(f'{file_path}')
    data_question = random.choice(questions)
    return {
        'question': data_question['question'],
        'answers': data_question['answers'],
        'correct': data_question['correct_answer'],
        "explanation": data_question["explanation"]
    }