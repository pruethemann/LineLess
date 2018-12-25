import sqlite3
from datetime import datetime
import os
from InstagramAPI import InstagramAPI
from Log import Log
import sys

class UserManagement(object):

    def __init__(self,username, pwd, support = False): 
        
        path_here = os.path.dirname(os.path.realpath(__file__)) 
        subdir = os.path.dirname(path_here)
        filename_logins = os.path.join(subdir, 'DB', 'Logins')  
        filename_user = os.path.join(subdir, 'DB', username)          
        
        ## Mit login verbinden oder neu erstellen
        try:
            db = sqlite3.connect(filename_logins)
            c = db.cursor()
            self.createLogins(c)
            print("Sucess! New Logins-DB created!!!")                        
        except Exception:
            print("Sucess! Zu Logins-Database verknüpft")    
            
        db.commit()         
        # Neuen User einfügen
     
        user_exists = self.add_login(username, pwd, support, c)
        db.commit()
        db.close()

        if user_exists:        
        # Neue Userdatabase erstellen
            try: 
                db = sqlite3.connect(filename_user)
                c = db.cursor()
                self.create_user(username,c)  
                db.commit()
                db.close()
                print(username, " successfuly got a new database")
            except Exception:
                print(username, "User wurde bereits eingefügt")        
  
    def createLogins(self,c):             
        c.execute('''
                       CREATE TABLE "Logins" ( `id` INTEGER, `username` TEXT UNIQUE, `userID` INTEGER UNIQUE, `pwd` TEXT, `likes_left` INTEGER, `follows_left` INTEGER, `last_update` TEXT, `max_following` INTEGER, `last_update_friendship` TEXT, `last_update_friendship_recent` TEXT, `last_update_own_posts` TEXT, `supporter` BLOB, PRIMARY KEY(`id`) )
                       ''')     
        print("ACHTUNG: Völlig neue Database erstellt")        
    
    def create_user(self,username,c):
        c.execute('''
                  CREATE TABLE "Commented" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `mediaID_userID_nr` TEXT UNIQUE, `username` TEXT, `comment` TEXT, `is_private` BLOB )
                  ''')
        
        c.execute('''
                  CREATE TABLE "Daily_Stats" ( `date` TEXT UNIQUE, `followers` INTEGER, `following` INTEGER )                                                                  
                  ''')                                              
        c.execute('''
                  CREATE TABLE "Follows" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `userID` INTEGER UNIQUE, `username` TEXT, `datefollow` TEXT, `dateunfollow` TEXT, `reciprocal` TEXT, `origin` TEXT, `date_engage` TEXT, `follower_count` INTEGER, `following_count` INTEGER, `media_count` INTEGER, `is_private` INTEGER, `white` INTEGER )                                                              
                  ''')  
        c.execute('''
                  CREATE TABLE "Liked" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `mediaID_userID` TEXT UNIQUE, `username` TEXT, `is_private` BLOB )      
                  ''')   
        c.execute('''
                  CREATE TABLE "Likes" ( `id` INTEGER, `mediaID` INTEGER UNIQUE, `userid` INTEGER, `date` TEXT, `origin` TEXT, `caption` TEXT, PRIMARY KEY(`id`) )      
                  ''')          
        c.execute('''
                  CREATE TABLE "Own_posts" ( `nr` INTEGER UNIQUE, `mediaID` INTEGER UNIQUE, `comment_count_soll` INTEGER, `comment_count_ist` INTEGER, `like_count_soll` INTEGER, `like_count_ist` INTEGER, `upload_date` TEXT, `location` INTEGER, `undersampling` INTEGER, `last_update` TEXT )      
                  ''')          
        c.execute('''
                  CREATE TABLE "Queue" ( `userID` INTEGER, `username` INTEGER, `origin` TEXT, `mediaID` INTEGER, `caption` INTEGER, `time` TEXT, `follower_count` INTEGER, `following_count` INTEGER, `media_count` INTEGER, `is_private` INTEGER )      
                  ''')          
        c.execute('''
                  CREATE TABLE "Tags" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `tag` TEXT UNIQUE, `last_update` TEXT, `follower` INTEGER, `follower_total` INTEGER, `efficiency` REAL )      
                  ''') 
        c.execute('''
                  CREATE TABLE "Users" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `userID` INTEGER UNIQUE, `username` TEXT, `last_update` TEXT, `L_follower` INTEGER, `L_follower_total` INTEGER, `L_efficiency` REAL, `C_follower` INTEGER, `C_follower_total` INTEGER, `C_efficiency` REAL )      
                  ''')      
          
        
    def add_login(self,username, pwd, support, c ):
        old =  datetime(1990,1,1)                  
        
        if support: ## settings for support accounts
            max_following = 0
        else:
            max_following = 500                   
        
        try:
            c.execute('''INSERT INTO Logins(username, pwd, likes_left, follows_left, last_update, max_following, last_update_friendship, last_update_friendship_recent, last_update_own_posts, supporter)                                                                   
                          VALUES(?,?,?,?,?,?,?,?,?,?)''', (username, pwd,0,0,old,max_following,old, old, old, support))
            
        except Exception as inst:
            print("username ", username, " already exists in Login DB")
            print(inst.args)    
            return False
            ## Insert UserID
        userID = self.get_userID(username)
        
        if userID == False:
            return False

        c.execute('''UPDATE Logins SET userID = ? WHERE username = ? ''',
         (userID, username))  

        return True                       
            
    def get_userID(self,username):
        ## Login with a supporter. To do: Connect to DB
        username_host = "underfcuk"
        pwd = "instafame"
        
        try:
            API = InstagramAPI(username_host, pwd)
            API.login()
        except Exception as inst:
            print(inst.args)
            return False   
        
        try:        
            API.searchUsername(username) # user_name to user_id
            return API.LastJson["user"]["pk"]
        except Exception as inst:
            print('Error get userID: ' , API.LastJson) #user exisitiert nicht
            ### To do: Delete username entry
            return False      
        
UserManagement('dress.the.stress', None)