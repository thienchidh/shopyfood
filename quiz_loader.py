import json
import random
import requests
import os


data = []

async def load_config():
    with open('config/quiz.json') as f:
        data = json.load(f)
        return data

async def load_config_path(path):
    with open(f'{path}') as f:
        data = json.load(f)
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
        stacks.append({
            "question" : result['question'],
            "answers" : answers,
            "correct": correct
        })
    return stacks.pop(0)


async def get_quiz_api_2():
    file_name = "quiz_history_12.json"
    file_path = os.path.join("crawl", f"{file_name}")
    questions = await load_config_path(f'{file_path}')
    data_question = random.choice(questions)
    return {
        'question': data_question['question'],
        'answers': data_question['answers'],
        'correct': data_question['correct_answer'],
        "explanation": data_question["explanation"]
    }