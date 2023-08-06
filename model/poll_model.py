import json
from all_get_repo_func import *
import repository 
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
import CONST
import time


class PollData:
    def __init__(self):
        chat_id = -1
        poll_id = -1
        host_poll_id = -1
        questions = []
        poll_type = "NONE"
        time_created = time.time()
        answers = dict()
        message_id = -1
        paid_state = dict()
        previous_poll_id = -1
        next_poll_id = -1
        
        self.chat_id = chat_id
        self.poll_id = poll_id
        self.host_poll_id = host_poll_id
        self.questions = questions
        self.poll_type = poll_type
        self.time_created = time_created
        self.answers = answers
        self.message_id = message_id
        self.paid_state = paid_state
        self.previous_poll_id = previous_poll_id
        self.next_poll_id = next_poll_id
      
      
    def set_poll_type(self, poll_type):
        self.poll_type = poll_type
          
    def set_questions(self, questions):
        self.questions = questions
        
    def set_message_id(self, message_id):
        self.message_id = message_id
        
    def set_poll_id(self, poll_id):
        self.poll_id = poll_id   
        
    def get_poll_id(self):
        return self.poll_id
        
    def set_next_poll_id(self, next_poll_id):
        self.next_poll_id = next_poll_id
        
    def set_previous_poll_id(self, previous_poll_id):
        self.previous_poll_id = previous_poll_id
        
    def get_previous_poll_id(self):
        return self.previous_poll_id
        
    def get_next_poll_id(self):
        return self.next_poll_id
    
    def set_chat_id(self, chat_id):
        self.chat_id = chat_id
        
        
    def set_host_poll_id(self, host_poll_id):
        self.host_poll_id = host_poll_id    

    def set_answers_by_user_id(self, user_id, selected_options):
        self.answers[user_id] = selected_options
        
    def set_paid_state_by_user_id(self, user_id, paid_or_not_paid):
        self.paid_state[user_id] = paid_or_not_paid        
        
    def parse(self, jsonObject):
        # logger.info(f"parse {jsonObject}")
        self.chat_id = jsonObject["chat_id"]
        self.poll_id = jsonObject["poll_id"]
        self.host_poll_id = jsonObject["host_poll_id"]
        self.questions = jsonObject["questions"]
        self.poll_type = jsonObject["poll_type"]
        self.time_created = jsonObject["time_created"]
        self.answers = jsonObject["answers"]
        # logger.info(f"parse jsonObject: {jsonObject}")
        # logger.info(f'parse jsonObject message_id: {jsonObject["message_id"]}')
        self.message_id = int(jsonObject["message_id"])
        self.paid_state = jsonObject["paid_state"]
        self.previous_poll_id = jsonObject["previous_poll_id"]
        self.next_poll_id = jsonObject["next_poll_id"]
        
        
    def get_answers(self):
        return self.answers    
        
    def get_questions(self):
        return self.questions      
              
    def get_paid_state(self):
        return self.paid_state  
    
    def get_time_created(self):
        return self.time_created
    
    def get_host_poll_id(self):
        return self.host_poll_id
    
    def get_message_id(self):
        return self.message_id
    
    def to_dict(self):
        return {
            "chat_id": self.chat_id,
            "poll_id": self.poll_id,
            "host_poll_id": self.host_poll_id,
            "questions": self.questions,
            "poll_type": self.poll_type,
            "time_created": self.time_created,
            "answers": self.answers,
            "message_id": self.message_id,
            "paid_state": self.paid_state,
            "previous_poll_id": self.previous_poll_id,
            "next_poll_id": self.next_poll_id,
        }
         
                
    def __repr__(self):
        return json.dumps(self.to_dict())
          
    def save(self):    
        self.obj = {}
        self.obj["chat_id"] = self.chat_id
        self.obj["poll_id"] = self.poll_id
        self.obj["host_poll_id"] = self.host_poll_id
        self.obj["questions"] = self.questions
        self.obj["time_created"] = self.time_created
        self.obj["answers"] = self.answers
        self.obj["message_id"] = self.message_id
        self.obj["paid_state"] = self.paid_state
        self.obj["previous_poll_id"] = self.previous_poll_id
        self.obj["next_poll_id"] = self.next_poll_id

class PollDataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, PollData):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

class PollDataManager:
    def __init__(self, update: Update, context: CallbackContext, chat_id):
        repo_poll_manager = context.user_data.get("poll_data_manager")
        if not repo_poll_manager or repo_poll_manager is not KeyValRepository:
            repo_poll_manager = KeyValRepository("poll_data_manager")
            context.user_data["poll_data_manager"] = repo_poll_manager            
        
        self.repo_poll_manager = repo_poll_manager
        self.chat_id = -1
            
        # logger.info(f"self.chat_id : {self.chat_id}")
        
        self.map = self.repo_poll_manager.compute_if_absent('map_by_chat_id', lambda k: dict())    
        self.map_by_chat_id = self.repo_poll_manager.compute_if_absent('map_by_chat_id', lambda k: dict()).get(f'{self.chat_id}', dict())    
        self.map_history_poll_by_chat_id_key = self.repo_poll_manager.compute_if_absent('map_history_poll_by_chat_id', lambda k: dict())  
        self.map_history_poll_by_chat_id_value = self.repo_poll_manager.compute_if_absent('map_history_poll_by_chat_id', lambda k: dict()).get(f'{self.chat_id}', [])    
        
    def get_poll_data_by_poll_id(self, poll_id) -> PollData:
        # logger.info(f"get_poll_data_by_poll_id {poll_id} {self.map_by_chat_id}")
        if (poll_id in self.map_by_chat_id):
            
            poll_data = PollData()
            # logger.info(f"get_poll_data_by_poll_id self.map_by_chat_id {self.map_by_chat_id[poll_id]} ")
            # json_object = json.loads(json.dumps(self.map_by_chat_id[poll_id]))
            json_object = self.map_by_chat_id[poll_id]
            # logger.info(f"get_poll_data_by_poll_id poll_data : {poll_data}")
            # logger.info(f"get_poll_data_by_poll_id {json_object}")
            poll_data.parse(json_object)
            return poll_data
            
        return None
    
    def get_poll_data_by_message_id(self, message_id) -> PollData:
        for key in self.map_by_chat_id:
            if (int(self.map_by_chat_id[key]["message_id"]) == int(message_id)):
                poll_id = self.map_by_chat_id[key]["poll_id"]
                return self.get_poll_data_by_poll_id(poll_id)
        return None
    
    def get_list_poll_id_follow_message_id(self, message_id):
        poll_data = self.get_poll_data_by_message_id(message_id)
        logger.info(f"get_list_poll_id_follow_message_id {message_id} {poll_data}")
        list_result = []
        if (poll_data is not None):
            root_poll_id = poll_data.get_poll_id()
            while poll_data.get_previous_poll_id() != -1:
                poll_data = self.get_poll_data_by_poll_id(poll_data.get_previous_poll_id())
                root_poll_id = poll_data.get_poll_id()
            list_result.append(root_poll_id)
            while poll_data.get_next_poll_id() != -1:
                poll_data = self.get_poll_data_by_poll_id(poll_data.get_next_poll_id())    
                list_result.append(poll_data.get_poll_id())
        return list_result                
    
    def get_poll_id_by_index(self, chat_id: int, poll_index: int):
        poll_history = self.map_history_poll_by_chat_id_key[str(chat_id)]
        if poll_history is None:
            return None
        if poll_index >= 0 and poll_index < len(poll_history):
            return poll_history[poll_index]
        if poll_index < 0 and abs(poll_index) <= len(poll_history):
            return poll_history[poll_index]
        return None
        
    
    def push_poll_data_by_chat_id(self, chat_id: int, poll_data: PollData):
        
        # logger.info(f"push_poll_data_by_chat_id {chat_id} {poll_data}")
        map_object = dict()
        json_object = json.loads(json.dumps(poll_data.to_dict()))
                
        self.map_by_chat_id[poll_data.poll_id] = json_object
        self.map[self.chat_id] = self.map_by_chat_id
        
    def push_poll_id_by_chat_id(self, chat_id: int, poll_data: PollData):    
        self.map_history_poll_by_chat_id_value.append(poll_data.poll_id)
        self.map_history_poll_by_chat_id_key[chat_id] = self.map_history_poll_by_chat_id_value
        
    def update_poll_data_by_chat_id(self, chat_id: int, poll_data: PollData):
        # map_object = self.repo_poll_manager.get(chat_id, dict())  
        # logger.info(f"update_poll_data_by_chat_id map_by_chat_id {self.map_by_chat_id}")
        # map = self.map_by_chat_id.get(chat_id, dict())
        json_object = json.loads(json.dumps(poll_data.to_dict()))
        # map_object[poll_data.poll_id] = json_object
        # map.update({ chat_id : {poll_data.poll_id : json_object}})
        # logger.info(f"update_poll_data_by_chat_id map update {json_object}")
        # self.repo_poll_manager.set("map_by_chat_id", map_by_chat_id)
        # self.repo_poll_manager.set("map_by_chat_id", map)
        self.map_by_chat_id[poll_data.poll_id] = json_object
        self.map[self.chat_id] = self.map_by_chat_id
  
            
    def __repr__(self):
        return json.dumps(self.to_dict())
          
    def save(self):    
        # self.repo_poll_manager.set("map_by_chat_id", {self.chat_id: self.map_by_chat_id})
        # logger.info(f"poll_model save {self.map}")
        self.repo_poll_manager.set("map_by_chat_id", self.map)
        self.repo_poll_manager.set("map_history_poll_by_chat_id", self.map_history_poll_by_chat_id_key)
        self.repo_poll_manager.save()


def get_poll_model(update, context, poll_id, host_poll_id, chat_id) -> PollDataManager:
    poll = PollDataManager(update, context, chat_id)
    return poll