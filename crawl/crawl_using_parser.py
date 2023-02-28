
from cmath import exp
import math
import re
from tkinter.messagebox import NO, QUESTION
from numpy import mat
import requests
from bs4 import BeautifulSoup
import json

from scrapy import Selector
from scrapy.http import HtmlResponse

data = []

name_file = "quiz_history_12.json"

def crawl():
    url = 'https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-3-1003'
    # response = requests.get(url)
    urls = []
    urls = [
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-1-982",
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-2-995",
            'https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-3-1003',
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-4-1005",
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-5-1006",
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-6-1008"
        ]
    data = []   
    for url in urls:
        # res = HtmlResponse(url=f'{url}')
        # response = Selector(response=res)
        # print(requests.get(url).text)
        # soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        response = Selector(text=requests.get(url).text)

        table_answer = response.css("div.section-content table tr td::text").getall() 
        cau = [ int(e.split(" ")[1]) - 1  for e in table_answer[0::2]]
        dap_an = [ ord(e) - ord('A') for e in table_answer[1::2]]
        mapCauToDapAn = {}
        i = 0
        for e in cau:
            mapCauToDapAn[e] = dap_an[i]
            i+=1
        print(dap_an)
        print(mapCauToDapAn)
        print(cau)   

        i = 0
        for e in response.css("div.box-van-dap"):
            question = e.css("a::attr(title)").get()
            if (question is None):
                continue
            print(f"Cau {i+1}: {question}")
            ptag = e.css("p")
            answers = []
            incorrect_answers = ""
            correct_answer = mapCauToDapAn[i]
            explanation = ""
            for p in ptag:
                answer_val = p.css("::text").get()
                print(answer_val)
                answers.append(answer_val)
            
            print(f"Dap an dung {correct_answer}")
            json_object = {"question":f'{question}', "answers": answers, "incorrect_answers": incorrect_answers, "correct_answer" : correct_answer, "explanation" : explanation}    
            data.append(json_object)
            i+=1
        # print("selfdata ", data)
        # print("selfdata ", data)
        with open(f'{name_file}', "w") as f:
            json.dump(data, f)  


    # soup = BeautifulSoup(response.text, 'html.parser')
    # sel = Selector(text=soup.text)
    # print(sel)
    return

    data = []
    count_cau = 0
    i = 0
    for link in soup.find('div', { 'class' : 'the-article-content'}).find_all('div', {'class' : 'box-van-dap'}):
        # print(f'@{link.getText()}@')
        
        if link is None: 
            continue
        a = link.find('a')

        question = ""
        
        if a is not None:
            count_cau += 1
            print(f'Cau {count_cau}: {a.get("title")}')
            question = f'{a.get("title")}'
        # print(f'div child: {link.children}')
        # print(link.find('p').getText())
        
        for e in link.find_all('p'):
            i += 1
            # print(f'{i} : {e.text}')
            answer_string = e.text
            regex_answer_string = r'([A-D]\..*)([A-D]\..*)([A-D]\..*)([A-D]\..*)*'
            answer_string = re.match(regex_answer_string, answer_string)
            if answer_string is not None:
                print(e.text)
                pass
            break   
        # child = BeautifulSoup(link.text, "html.parser")
        # for c in child.find_all("p"):
            # print(c.text)

        json_object = {"question":f'{question}', "answers": answers, "incorrect_answers": incorrect_answers, "correct_answer" : correct_answer, "explanation" : explanation}    
        data.append(json_object)

    # find all paragraphs on the page
    # for paragraph in soup.find_all('p'):
        # print(paragraph.text)
    correct_answer_string = soup.find("div", { 'class' : 'section-content'}).find('table', { 'class' : 'table text-center'})    
    regex_cau = r"Câu \d{0,2}"
    regex_abcd = r"[ABCD]"
    regex = f"({regex_cau})({regex_abcd})"
    # print(answer_string)
    print(correct_answer_string.text)
    matches = re.findall(regex, correct_answer_string.text)
    for match in matches:
        print(match[0])
        print(match[1])
        # print(match.group(1))
        # print(match.group(2))

    with open(f'{name_file}', "w") as f:
            json.dump(data, f)

def main():
    crawl()

    
    pass

if __name__ == "__main__":
    main()    
