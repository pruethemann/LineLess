# -*- coding: utf-8 -*-

import sqlite3
import os
from Log import Log
import sys

""" TO do
1. Import single line from metrics DB
2. Export function 
3. Implement into Lineless

"""

class Metrics(object):   
    db = ''
    c = ''  

    def __init__(self): 
        here = os.path.dirname(os.path.realpath(__file__)) 
        subdir = os.path.dirname(here) # cd ..
        importFile = os.path.join(subdir, 'DB', 'Metrics')     

        
        try:
            self.connect_db(importFile)
            print("Successfully connected to Metrics")
        except Exception:
            print("DB Metrics not found! Kill script.") 
            sys.exit()

                    
        
    def insert_feed(self, mediaID, feed):
        for userID in feed:                      
            self.import_users(userID, mediaID)            

            
    def import_meta(self, feed, new_mediaID, new_tags, new_location, target):     
       for userID in feed:     
            # To do: For some random reason the right value is only returned after looping twice
            for i in range(2):            
                user_meta = self.c.fetchone()
                self.c.execute("SELECT * FROM {tn} WHERE {idf}={my_id}".\
                        format(tn=target, cn='userID', idf='userID', my_id=userID))   
                
            ## Check if user exists in DB
            if user_meta:    
                mediaIDs_db = self.convert_to_list(user_meta[1])                
                              
                # update new mediaID
                if not new_mediaID in mediaIDs_db:
                    tags_db = self.convert_to_list(user_meta[3])
                    locations_db = self.convert_to_list(user_meta[4])
                    
                    tags = self.convert_to_string(tags_db, new_tags)
                    locations = self.convert_to_string(locations_db, new_location)
                    
                    mediaIDs = self.convert_to_string(mediaIDs_db, new_mediaID)
#                    print("Bei ", userID, " wird folgende mediaID angehängt ", new_mediaID)                        
                    self.update_liker(userID, mediaIDs, len(mediaIDs_db), tags, locations, target)
            
            #user doesn't exist. Insert new user with meta Data
            else:  
                tags = self.convert_to_string([], new_tags)
                locations = self.convert_to_string([], new_location)  
#                try:### try to insert a new userID which is not part of the DB                   
                self.insert_liker(userID, new_mediaID, tags, locations, target)
#                except Exception:
#                    print("For some random reason the user can be inserted. Close the DB you fucking moron")                      
       print("Imported mediaID: ", new_mediaID)
      # print("Imported tags: ", new_tags)
       print("imported locations: ", new_location)
       self.db.commit()    
    
    def convert_to_list(self,meta_str):
        meta = []
        if meta_str == None:
            return []
        
        item = ''        
        for i in meta_str:   
            if i == ' ':   ## solve the space problem
                if item == ' ':
                    continue
                meta.append(str(item))
                item = ''
            else:
                item += i
        meta.append(str(item))
        return meta  
    
    def convert_to_string(self, meta_db, meta_new):
        if meta_db == None:
            meta_db = []
        if meta_new == None:
            meta_new = ''
            
        if type(meta_new) == list:
            meta_db.extend(meta_new)        
          
        else:
            meta_db.append(str(meta_new))
      
        meta_string = ''           
        for m in meta_db:           
            meta_string += str(m) + ' '

        return meta_string.strip()      
               
   ### To do: insert try         
    def insert_liker(self,userID, mediaID, tags, location, target):                                                                                                                                                                                                                 
        try:
            sql_task = "INSERT INTO " + target + "(userID, mediaID, count, tags, locations, following_count, follower_count, media_count, is_private) VALUES(?,?,?,?,?,?,?,?,?)"
            self.c.execute(sql_task, (userID, str(mediaID), 1, tags, location, None, None, None, False) )
#           print("New user inserted ", userID, tags, location)            
        except Exception:   
            print("User ", userID, " can't be inserted into metrics")
        
    def update_liker(self,userID, mediaID, count, tags, locations, target):
        sql_task = "UPDATE " + target + " SET mediaID = ?,  count = ?,  tags = ?, locations = ? WHERE userID = ?"
        self.c.execute(sql_task, (mediaID, count, tags, locations, userID))            
#        print("New user updated ", userID, tags, locations)
        
    def update_userinfo(self,userID, userinfo):
        following_count = userinfo['following_count']
        follower_count = userinfo['follower_count']   
        media_count = userinfo['media_count']
        is_private = userinfo['is_private']
        
        ## try to update both tables. To do: think about that
        targets =['Likers', 'Commenters']   
        for t in targets:           
            try:
                sql_task = "UPDATE " + t + " SET following_count = ?,  follower_count = ?, media_count = ?, is_private = ? WHERE userID = ?"
                self.c.execute(sql_task, (following_count, follower_count, media_count, is_private, userID)) 
            except Exception:
                continue
#                print("userID ", userID, " not in table ", t)
        
        self.db.commit()  #        
             
    def connect_db(self,db):
        self.db = sqlite3.connect(db)
        self.c = self.db.cursor()        

    def close(self):
        self.db.commit()   
        self.db.close()       

    def vacuum(self):  
        Log("VACUUM metrics:")
        self.c.execute("VACUUM")
#        self.db.close()   


#Metrics()