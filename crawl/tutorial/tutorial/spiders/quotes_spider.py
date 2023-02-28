from pathlib import Path

import scrapy
import json

data = []

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    def start_requests(self):
        urls = [
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-1-982",
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-2-995",
            'https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-3-1003',
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-4-1005",
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-5-1006",
            "https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-6-1008"
        ]
        name_file = "output.json"
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

        print("selfdata ", data)
        with open(f'{name_file}', "w") as f:
            json.dump(data, f)           

    def parse(self, response):
        # scrapy shell 'https://doctailieu.com/trac-nghiem/bo-de-trac-nghiem-lich-su-van-minh-the-gioi-phan-3-1003'

        # page = response.url.split("/")[-2]
        # filename = f'quotes-{page}.html'
        # Path(filename).write_bytes(response.body)
        # self.log(f'Saved file {filename}')
        
        name_file = response.url.split("/")[-1] + "output.json"

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
        print("selfdata ", data)
        with open(f'{name_file}', "w") as f:
            json.dump(data, f)  
    

         
