# -*- coding: utf-8 -*-

import sqlite3
from datetime import date, datetime, time
from dateutil import parser
from random import randint
import os

class Session_login(object):   
    db = ''
    c = ''  
    d = {} #user_data
    username = ''
    likesCount = 0
    followersCount = 0

    def __init__(self,username):  
        here = os.path.dirname(os.path.realpath(__file__)) 
        subdir = os.path.dirname(here) # cd ..
        importFile = os.path.join(subdir, 'DB', 'Logins')                       
        
        try:
            self.connect_db(importFile)
            print('Successfully connected to Logins', username)
        except Exception:
            print("Logins - DB not found!")
        self.username = username 
        self.fetch_login(username)
        
    def connect_db(self,db):
        self.db = sqlite3.connect(db)
        self.c = self.db.cursor()        

    def fetch_login(self,username):       
        self.c.execute('''SELECT username, userID, pwd, likes_left, follows_left, last_update,  max_following, last_update_friendship, last_update_friendship_recent, last_update_own_posts FROM Logins''')
        for row in self.c:
            if row[0] == username:
                    self.d['username'] = row[0]
                    self.d['userID']= row[1]
                    self.d['pwd'] = row[2]
                    self.d['likes_left'] = row[3]
                    self.d['follows_left'] = row[4]     
                    self.d['last_update'] = parser.parse( row[5] )
                    self.d['max_following'] = row[6]   
                    self.d['last_update_friendship'] = parser.parse( row[7] ) 
                    self.d['last_update_friendship_recent'] = parser.parse( row[8] ) 
                    self.d['last_update_own_posts'] = parser.parse( row[9] ) 
       
    def get_limits(self):
        self.fetch_login(self.username)
        return self.d['follows_left']        
        
    def set_limits(self,limit):   
        now = datetime.now()
        self.c.execute('''UPDATE Logins SET follows_left = ? WHERE username = ? ''',
         (limit, self.username))    
        self.c.execute('''UPDATE Logins SET last_update = ? WHERE username = ? ''',
         (now, self.username))               
        print(self.username, " got ", limit, " sweet new follows today. Go for it!")             
        self.db.commit()    

    def update_limits(self,limit):   
        self.fetch_login(self.username)           
        self.c.execute('''UPDATE Logins SET follows_left = ? WHERE username = ? ''',
         (self.d['follows_left'] - limit, self.username))           
        self.db.commit()    
   
    def update_last_update_friendship(self): 
        now = datetime.now()    
        self.c.execute('''UPDATE Logins SET last_update_friendship = ? WHERE username = ? ''',
         (now, self.username))           
        self.db.commit()  
        
    def update_last_update_friendship_recent(self): 
        now = datetime.now()    
        self.c.execute('''UPDATE Logins SET last_update_friendship_recent = ? WHERE username = ? ''',
         (now, self.username))      
        self.db.commit()           

    def update_last_update_own_posts(self): 
        now = datetime.now()    
        self.c.execute('''UPDATE Logins SET last_update_own_posts = ? WHERE username = ? ''',
         (now, self.username))      
        self.db.commit()           
    
       
    def set_max_following(self,max):
         self.c.execute('''UPDATE Logins SET max_following = ? WHERE username = ? ''',
             (max, self.username))    
         
    def close(self):
        self.db.close()        