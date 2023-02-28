
from cmath import exp
import math
import re
from numpy import mat
import requests
from bs4 import BeautifulSoup
import json

file = "data"
url1 = ""
url = "https://vietjack.com/bai-tap-trac-nghiem-lich-su-12/bai-6-nuoc-mi.jsp"
# url = "https://vietjack.com/bai-tap-trac-nghiem-lich-su-12/trac-nghiem-phong-trao-dan-toc-dan-chu-o-viet-nam-tu-nam-1919-den-nam-1925.jsp"
links = []

def extract(text, name_file):
    regexQuestion = r"Câu \d{1,2}\.\s*</b>\s*(.*?)<\/p>"
    regexAnswer0 = r"<p>A\.\s.+<\/p>"
    regexAnswer1 = r"<p>B\.\s.+<\/p>"
    regexAnswer2 = r"<p>C\.\s.+<\/p>"
    regexAnswer3 = r"<p>D\.\s.+\s*<\/p>"
    regexRightAnswer = r"<p>Đáp án:.*<b>.*<\/b><\/p>"
    regexExplaination = r"<p>Giải thích:.*<\/p>"   
    regex = f"(({regexQuestion})|({regexAnswer0})|({regexAnswer1})|({regexAnswer2})|({regexAnswer3})|({regexRightAnswer})|({regexExplaination}))"
    matches = re.findall(regex, text)
    i = 0

    answers = []
    question = ""
    right_answers = []
    explain = ""
    data = []
    incorrect_answers = []
    correct_answers = []
    
    for match in matches:
        i+=1
        val_string = match[0]
        if (re.match(regexQuestion, val_string)):
            json_object = {"question":f'{question}', "incorrect_answers": incorrect_answers, "correct_answers" : correct_answers, "explain" : explain}
            answers = []
            right_answers = []
            explain = ""
            data.append(json_object)
            question = val_string
            pass
        else: 
            pass    

        if (re.match(regexAnswer0, val_string)):
            answers.append(val_string)
            pass
        else: 
            pass

        if (re.match(regexAnswer1, val_string)):
            answers.append(val_string)
            pass
        else: 
            pass

        if (re.match(regexAnswer2, val_string)):
            answers.append(val_string)
            pass
        else: 
            pass

        if (re.match(regexAnswer3, val_string)):
            answers.append(val_string)
            pass
        else: 
            pass

        if (re.match(regexRightAnswer, val_string)):
            right_answers.append(val_string)
            pass
        else: 
            pass

        if (re.match(regexExplaination, val_string)):
            explain = val_string
            pass
        else: 
            pass
        # part1 = match.group(1)
        # part2 = match.group(2)
        # part3 = match.group(3)
        # part4 = match.group(4)
        # part5 = match.group(5)
        # print("Part 1:", math[0])
        # print("Part 2:", part2)
        # print("Part 3:", math[2])
        # print("Part 4:", part4)
        # print("Part 5:", part5)
        print(f'Câu {i} :  {match[0]}')

    pass

    with open(f'{name_file}', "w") as f:
        json.dump(data, f)

def main() -> None:
    
    response = requests.get(url)

    html = response.text

    # print(html)
    extract(html, "output1.json")
    return
    # Open the file and read its contents
    with open('data', 'r') as file:
        text = file.read()

    extract(text)
        
    # regex = r">Câu (\d+)\. </b>(.*?)(\r?\n|<)\/p>(.*?)(\r?\n|<)\/p>(.*?)<\/p>(.*?)(\r?\n|<)\/p>"

    # matches = re.findall(regex, text)

    # for match in matches:
    #     print("Part 1:", match[1])
    #     print("Part 2:", match[2])
    #     print("Part 3:", match[3])
    #     print("Part 4:", match[4])
    #     print("Part 5:", match[5])
    

    # pass


if __name__ == "__main__":
    main()
