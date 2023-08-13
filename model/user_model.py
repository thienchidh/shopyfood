import json
from all_get_repo_func import *
import repository 
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
import CONST

class User:
    def __init__(self, update: Update, context: CallbackContext, user_id: int):
        repo_user = context.user_data.get(user_id)
        if not repo_user or repo_user is not KeyValRepository:
            repo_user = KeyValRepository(user_id)
            context.user_data[user_id] = repo_user
    
        self.repo_user = repo_user
        chat_id = 0
        if (update is not None and update.effective_chat is not None):
            chat_id = update.effective_chat.id
            
        self.user_name = repo_user.get("user_name", [])
        self.chat_id = chat_id
        self.full_name = repo_user.get("full_name", []) 
        self.user_id = user_id
        self.level = repo_user.get("level", 0)
        self.exp = repo_user.get("exp", 0)
        self.description = repo_user.get("description", [])
      
    def to_dict(self):
        return {
            "chat_id": self.chat_id,
            "full_name": self.full_name,
            "user_name": self.user_name,
            "user_id": self.user_id,
            "level": self.level,
            "exp": self.exp,
            "description:": self.description
        }
         
    def add_user_name(self, user_name: str):
        while (len(self.user_name) > CONST.LEN):
            self.user_name.pop()
        self.user_name.insert(0, user_name)    
        
    def add_description(self, description: str):
        while (len(self.description) > CONST.LEN):
            self.description.pop()
        self.description.insert(0, description)                   
        
    def get_user_name(self):
        if (len(self.user_name) > 0):
            return self.user_name[-1]
        return "NoFoundUserName"
        
    def get_description(self):
        if (len(self.description) > 0):
            return self.description[-1]
        return "NoFoundDescription"
        
    def get_level(self):
        return self.level
    
    def get_exp(self):
        return self.exp
    
            
    def __repr__(self):
        return json.dumps(self.to_dict())
          
    def save(self):    
        self.repo_user.set("chat_id", self.chat_id)
        self.repo_user.set("full_name", self.full_name)
        self.repo_user.set("user_name", self.user_name)
        self.repo_user.set("user_id", self.user_id)
        self.repo_user.set("level", self.level)
        self.repo_user.set("exp", self.exp)
        self.repo_user.set("description", self.description)
        self.repo_user.save()


def get_user_model(update, context, user_id):
    user = User(update, context, user_id)
    return user