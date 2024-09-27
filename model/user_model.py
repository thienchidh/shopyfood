import json
from all_get_repo_func import *
import repository 
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
import CONST

class TopLink:
    def __init__(self, links=None):
        if links is None:
            links = []
        self.links = links

    def to_dict(self):
        return {
            "links": self.links
        }
    
    def add_link(self, url: str):
        for link in self.links:
            if link['url'] == url:
                link['num_host'] += 1
                break
        else:
            self.links.append({"url": url, "num_host": 1})
    
    def get_links(self):
        return self.links

    def get_top_links(self, top_n=10):
        sorted_links = sorted(self.links, key=lambda x: x['num_host'], reverse=True)
        return sorted_links[:top_n]
    
    def __repr__(self):
        return json.dumps(self.to_dict())
          
    def save(self, repo_user):    
        repo_user.set("links", self.links)
        repo_user.save()


class User:
    def __init__(self, update: Update, context: CallbackContext, user_id: int):
        self.repo_user = context.user_data.get(user_id)
        if not self.repo_user or not isinstance(self.repo_user, KeyValRepository):
            self.repo_user = KeyValRepository(user_id)
            context.user_data[user_id] = self.repo_user

        self.chat_id = update.effective_chat.id if update and update.effective_chat else 0
        self.user_id = user_id
        self.user_name = self.repo_user.get("user_name", [])
        self.full_name = self.repo_user.get("full_name", [])
        self.level = self.repo_user.get("level", 0)
        self.exp = self.repo_user.get("exp", 0)
        self.description = self.repo_user.get("description", [])
        self.host_history = self.repo_user.get("host_history", [])
        self.top_link = TopLink(self.repo_user.get("links", []))
      
    def to_dict(self):
        return {
            "chat_id": self.chat_id,
            "full_name": self.full_name,
            "user_name": self.user_name,
            "user_id": self.user_id,
            "level": self.level,
            "exp": self.exp,
            "description": self.description,
            "host_history": self.host_history,
            "links": self.top_link.get_links()
        }
         
    def add_user_name(self, user_name: str):
        while len(self.user_name) >= CONST.LEN:
            self.user_name.pop()
        self.user_name.insert(0, user_name)    
        
    def add_description(self, description: str):
        while len(self.description) >= CONST.LEN:
            self.description.pop()
        self.description.insert(0, description)   
        
    def add_host_history(self, poll_id: int):
        self.host_history.append(poll_id)
        
    def get_host_times(self):
        return len(self.host_history)        
        
    def get_user_name(self):
        return self.user_name[-1] if self.user_name else "NoFoundUserName"
        
    def get_description(self):
        return self.description[-1] if self.description else "NoFoundDescription"
    
    def get_latest_description(self):
        return self.description[0] if self.description else "NoFoundDescription"
        
    def get_level(self):
        return self.level
    
    def get_exp(self):
        return self.exp
    
    def get_links(self):
        return self.top_link.get_links()
    
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
        self.repo_user.set("host_history", self.host_history)
        self.top_link.save(self.repo_user)

def get_user_model(update, context, user_id):
    return User(update, context, user_id)