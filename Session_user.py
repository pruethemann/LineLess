# -*- coding: utf-8 -*-

import sqlite3
from datetime import date, datetime, time
from dateutil import parser
import os
from Log import Log

class Session_user(object):   
    db = ''
    c = ''  

    def __init__(self,username): 
        here = os.path.dirname(os.path.realpath(__file__)) 
        subdir = os.path.dirname(here) # cd ..
        importFile = os.path.join(subdir, 'DB', username)     
        
        try:
            self.connect_db(importFile)
            print("Successfully connected to ", username)
        except Exception:
            print("DB ", username, " not found!")
            
        ### Execute to reduce file size SQL
#        self.vacuum()
            
    def insert_follows(self,userID, username, datefollow, dateunfollow, reciprocal, origin, metrics, date_engage):   
#        origin = origin.encode('utf8')      
        self.c.execute('''INSERT INTO Follows(userID, username, datefollow, dateunfollow, reciprocal, origin,follower_count, following_count, media_count, is_private, date_engage)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?)''', (userID, username, datefollow, dateunfollow, reciprocal, origin,metrics['follower_count'], metrics['following_count'], metrics['media_count'], metrics['is_private'], date_engage))
        self.db.commit() 
        
    def insert_likes(self,mediaID,userID,origin,caption):
        now = datetime.now()
#        origin = origin.encode('utf8')
#        caption = caption.encode('utf8')        
        try:
            self.c.execute('''INSERT INTO Likes(mediaID, userID, date, origin, caption)
                              VALUES(?,?,?,?,?)''', (mediaID,userID, now, origin,caption))
            self.db.commit()
        except Exception:
            Log("Somehow this mediaID is already in database?? "+ str( userID ) + "mediaID: " + str( mediaID) )
            
    def insert_tag(self,tag):   
        old =  datetime(1990,1,1)  
        tag = tag#.encode('utf8')         
        try:
            self.c.execute('''INSERT INTO Tags(tag, last_update, follower, follower_total, efficiency)
                              VALUES(?,?,?,?,?)''', (tag, old, 0, 0, 0))
            self.db.commit()  
        except Exception as inst:
            Log("Tag " + tag + " has already been added. Or DB is locked")
            print(inst.args)
            
    def insert_daily_stats(self,follower_count, following_count):   
        now = datetime.now() 
        now = str(now.year) + '-' + str(now.month) + '-' + str(now.day) + ' ' + str(now.hour) + ':' + str(now.minute)
        try:
            self.c.execute('''INSERT INTO Daily_Stats(date, followers, following)
                              VALUES(?,?,?)''', (now, follower_count, following_count))              
        except Exception: 
            self.c.execute('''UPDATE Daily_Stats SET followers = ? WHERE date = ? ''',
             (follower_count, now)) 
            self.c.execute('''UPDATE Daily_Stats SET following = ? WHERE date = ? ''',
             (following_count, now))             
        self.db.commit()

    def insert_queues(self,queue):    
        ## Delete old entries first
        self.c.execute('''DELETE FROM Queue''')
       
        for item in queue:
            for t in item:
                userID = item[t][0]
                username = item[t][1]
                origin = item[t][2]#.decode('utf8')  
                
                if t == 'media':                                 
                    mediaID = item[t][3]                
                    caption = item[t][4]#.encode('utf8')  
                    timer = item[t][5]
                    self.c.execute('''INSERT INTO Queue(userID, username, origin, mediaID, caption, time)
                              VALUES(?,?,?,?,?,?)''', (userID, username, origin, mediaID, caption, timer))   
                elif t == 'user': # user 
                    timer = item[t][3]
                    metrics = item[t][4]       
#                    print(metrics)
#                    print("user: ",userID, username, origin, timer, metrics['follower_count'], metrics['following_count'], metrics['media_count'], metrics['is_private'] )
                    self.c.execute('''INSERT INTO Queue(userID, username, origin, time, follower_count, following_count, media_count, is_private)
                              VALUES(?,?,?,?,?,?,?,?)''', (userID, username, origin, timer, metrics['follower_count'], metrics['following_count'], metrics['media_count'], metrics['is_private']))             
                else:
                    print("shit happens, as usual")
        self.db.commit()
             
        
    def delete_queues(self):    
        ## Delete old entries first
        self.c.execute("delete from queue where id = '%s' " % 1)       
        self.db.commit()        

    def fetch_queue(self):       
        self.c.execute('''SELECT userID, username, origin, mediaID, caption, time, follower_count, following_count, media_count, is_private FROM Queue''')
        queue = [] 
        for row in self.c:    
            temp = []
            item = {}
            if row[3] != None: #mediaID
                temp.append(row[0]) # userID 
                temp.append(row[1]) # username
                temp.append(row[2]) # origin
                temp.append(row[3]) # mediaID
                temp.append(row[4]) # caption
                temp.append( parser.parse(row[5])) # time
                item['media'] = temp
            else: #user follows
                temp.append(row[0]) # userID 
                temp.append(row[1]) # username
                temp.append(row[2]) # origin
                temp.append( parser.parse(row[5])) # time
                metrics = {}
                
                metrics['follower_count'] = row[6]
                metrics['following_count'] = row[7]
                metrics['media_count'] = row[8] 
                metrics['is_private'] = row[9]   
                temp.append(metrics)
                
                item['user'] = temp
            queue.append(item)          
        return queue  
    
        
    def fetch_follows(self, metrics = False):              
        self.c.execute('''SELECT userID, username, datefollow, dateunfollow, reciprocal, origin, date_engage, white FROM Follows''')
        users = {}
        for row in self.c:    
            user = {}
            user['username'] = row[1]   
            
            if row[2] == None:
                user['datefollow'] = None
            else:
                user['datefollow'] = parser.parse(row[2])
                
            if row[3] == None:
                user['dateunfollow'] = row[3]     
            else:
                user['dateunfollow'] = parser.parse(row[3])
                
            if row[4] == None:
                user['reciprocal'] = None  
            else:
                user['reciprocal'] = parser.parse(row[4] )    
                
            user['origin'] = row[5]
            
            if row[6] == 'private' or row[6]== None:
                user['date_engage'] = row[6]          
            else:               
                user['date_engage'] = parser.parse(row[6])
            
            user['whitelist'] = bool( row[7] )
                
            users[row[0]] = user #dic with userIDs enthält dics mit allen daten. UserID is INT!!!
            
        ## import additional metrics            
        if metrics:
            self.c.execute('''SELECT userID, follower_count, following_count, media_count, is_private FROM Follows''')       

            for row in self.c:    
                userID = row[0]
                user = users[userID] ## get existing dic and extend it
                user['follower_count'] = row[1]
                user['following_count'] = row[2]     
                user['media_count'] = row[3]  
                user['is_private'] = bool(row[4])   
                users[userID] = user
                
        return users
    
    def fetch_follows_list(self):       
        self.c.execute('''SELECT userID, username, datefollow, dateunfollow, reciprocal, date_engage FROM Follows''')
        follows = [] 
        for row in self.c:    
            follower = []
            follower.append(row[0]) # userID as string
            follower.append(row[2]) # datefollow
            follower.append(row[3]) # dateunfollow
            follower.append(row[4]) # reciprocal
            follower.append(row[5]) # engage date
            follows.append(follower) 
        return follows    
    
    def fetch_likes(self):       
        self.c.execute('''SELECT mediaID, userID, date, origin FROM Likes''')
        likes = {}
        for row in self.c:     
            like = {}
            like['userID'] = row[1]   
            like['date'] = parser.parse(row[2])            
            like['origin'] = row[3]                              
            likes[row[0]] = like #dic with mediaID enthält dics mit allen daten
        return likes       
    

    def fetch_tags(self):       
        self.c.execute('''SELECT tag, last_update, follower, follower_total, efficiency FROM Tags''')
        tags = {}
        for row in self.c:
                if row[1] == 'black': #ignore blackList
                    continue
                tag = {}                
                tag['last_update'] = parser.parse( row[1] )
                tag['follower'] = row[2]
                tag['follower_total'] = row[3]
                tag['efficiency'] = row[4]
                tags[row[0]]= tag
        return tags
             
                
    def fetch_users(self):       
        self.c.execute('''SELECT userID, username, last_update, L_follower,L_follower_total,L_efficiency, C_follower, C_follower_total, C_efficiency FROM Users''')
        users = {}
        for row in self.c:
                if row[2] == 'black': #ignore blackList
                    continue
                user = {}
                user['username'] = row[1]
                user['last_update'] = parser.parse( row[2] )
                user['L_follower'] = row[3]
                user['L_follower_total'] = row[4]
                user['L_efficiency'] = row[5]
                user['C_follower'] = row[6]
                user['C_follower_total'] = row[7]
                user['C_efficiency'] = row[8]
                users[row[0]] = user #userID as Int?
        return users


    def fetch_own_posts(self):       
        self.c.execute('''SELECT nr, mediaID, comment_count_soll, comment_count_ist, like_count_soll, like_count_ist, upload_date, location, undersampling, last_update FROM Own_posts''')
        own_posts = {}
        for row in self.c:
                mediaID = row[1]
                post = {}
                post['post_nr'] = row[0]
                post['comment_count_soll'] = row[2]        
                post['comment_count_ist'] = row[3]                  
                post['like_count_soll'] = row[4]
                post['like_count_ist'] = row[5]
                post['upload_date'] = row[6]                
                post['location'] = row[7]
                post['undersampling'] = row[8]  
                post['last_update'] = parser.parse( row[9] )
                own_posts[mediaID] = post
        return own_posts
    
    def insert_own_post(self,nr, mediaID, like_count, comment_count, upload_date, location,last_update):   
        undersampling = -50 ## To initiate an import of all likes and comments eventhough they don't have 50 likes yet. 
        try:
            self.c.execute('''INSERT INTO Own_posts(nr, mediaID, comment_count_soll, comment_count_ist, like_count_soll, like_count_ist, upload_date, location, undersampling, last_update)
                              VALUES(?,?,?,?,?,?,?,?,?,?)''', (nr, mediaID, comment_count, 0, like_count, 0, upload_date, location, undersampling, last_update))     
            Log("Post nr. " + nr, " imported. Likes:" + like_count + "Comments:" + comment_count + "Upload:" + upload_date + "location:" + location)                  
        except Exception:            
             return False   # post already exists     
        self.db.commit() 
  

    def insert_user(self,userID, username):   
        old =  datetime(1990,1,1)  
        try:
            self.c.execute('''INSERT INTO Users(userID, username, last_update, L_follower,L_follower_total,L_efficiency, C_follower, C_follower_total, C_efficiency)
                              VALUES(?,?,?,?,?,?,?,?,?)''', (userID, username, old, 0, 0, 0, 0, 0, 0))     
            Log("User " + username + " " + str(userID )+ " imported.")                  
        except Exception:            
             return False
#            print("User ", username, userID, " has already been added.")
             
         
    def update_own_post_soll(self, mediaID, like_count, comment_count):   
        try:
            self.c.execute('''UPDATE Own_posts SET like_count_soll = ? WHERE mediaID = ? ''',
             (like_count, mediaID))    
            self.c.execute('''UPDATE Own_posts SET comment_count_soll = ? WHERE mediaID = ? ''',
             (comment_count, mediaID))       
            self.c.execute('''UPDATE Own_posts SET last_update = ? WHERE mediaID = ? ''',
             (datetime.now(), mediaID))      
                         
        except Exception:   
            Log("you fucked it up")
            return False        
        self.db.commit() 
        
    def update_own_post_ist(self, mediaID, like_count, comment_count,undersampling):   
#        try:
        self.c.execute('''UPDATE Own_posts SET like_count_ist = ? WHERE mediaID = ? ''',
         (like_count, mediaID))    
        self.c.execute('''UPDATE Own_posts SET comment_count_ist = ? WHERE mediaID = ? ''',
         (comment_count, mediaID))   
        if like_count == 0:
            undersampling = -50 ## Import has not been completed yet
        self.c.execute('''UPDATE Own_posts SET undersampling = ? WHERE mediaID = ? ''',
         (undersampling, mediaID))                              
#        except Exception:   
#            Log("you fucked it up.ist")
#            return False        
        self.db.commit() 
                
    def update_stats(self,name, module, follows, total_follows, efficiency):
        if module == 'liker':
            self.c.execute('''UPDATE Users SET L_follower = ? WHERE username = ? ''',
             (follows, name))    
            
            self.c.execute('''UPDATE Users SET L_follower_total = ? WHERE username = ? ''',
             (total_follows, name))            
    
            self.c.execute('''UPDATE Users SET L_efficiency = ? WHERE username = ? ''',
             (efficiency, name))    
            
        elif module == 'commenter':
            self.c.execute('''UPDATE Users SET C_follower = ? WHERE username = ? ''',
             (follows, name))    
    
            self.c.execute('''UPDATE Users SET C_follower_total = ? WHERE username = ? ''',
             (total_follows, name))    

            self.c.execute('''UPDATE Users SET C_efficiency = ? WHERE username = ? ''',
             (efficiency, name))    
        
        elif module == 'tags':
            self.c.execute('''UPDATE Tags SET follower = ? WHERE tag = ? ''',
             (follows, name))  
            
            self.c.execute('''UPDATE Tags SET follower_total = ? WHERE tag = ? ''',
             (total_follows, name)) 
            
            self.c.execute('''UPDATE Tags SET efficiency = ? WHERE tag = ? ''',
             (efficiency, name))     
            
        else:
            Log("You screwed it up. Shame on you")
            
          
        self.db.commit()      
      
        # To do: combine this two functions
    def update_last_update(self,userID_or_tag, module): 
        now = datetime.now()   
        if module == 'Tag':
            self.c.execute('''UPDATE Tags SET last_update = ? WHERE tag = ? ''',
             (now, userID_or_tag))
        elif module == 'Liker' or module == 'Commenter':                                               
            self.c.execute('''UPDATE Users SET last_update = ? WHERE userID = ? ''',
             (now, userID_or_tag))       
        else:
            Log("This module doesn't exist ", module)   
            
        
        self.db.commit()    

        
 # To do: Combine update_unfollow and update_friendship includ. possibility of deleted account
    def update_unfollow(self,userID, deleted = False):
        now = datetime.now()  
        if not deleted:
            self.c.execute('''UPDATE Follows SET dateunfollow = ? WHERE userID = ? ''',
             (now, userID))   
        else: ## User delted himself
            old =  datetime(1990,1,1) 
            self.c.execute('''UPDATE Follows SET dateunfollow = ? WHERE userID = ? ''',
             (old, userID))              
        self.db.commit()    
        
    def update_friendship(self,userID,reciprocal, dateunfollow):     
        self.c.execute('''UPDATE Follows SET reciprocal = ? WHERE userID = ? ''',
         (reciprocal, userID))     
        if dateunfollow != False:
            self.c.execute('''UPDATE Follows SET dateunfollow = ? WHERE userID = ? ''',
             (dateunfollow, userID))   
    
    ## gets a dic of all userIDs which are reciprocal. Updates reciprocal date and username (in case uername changed)
    ## To do: Consider solving it over bool. And keep reciprocal date as original interaction
    def update_reciprocal(self,reciprocals):            
        now = datetime.now() 
        for userID in reciprocals:
            username = reciprocals[userID]
            try: ##Insert new user, unless he already exist: check if we get metrics and use it over insert_follow func
                self.c.execute('''INSERT INTO Follows(userID, username, datefollow, dateunfollow, reciprocal, origin, date_engage, u) 
                VALUES(?,?,?,?,?,?,?,?)''', (userID, username, now, None, now, "private rec", now, 1) )             
                   
            except Exception:  
                try:      
                    sql_task = "UPDATE Follows SET username = ?, dateunfollow = ?, reciprocal = ?, u=?  WHERE userID = ?"
                    self.c.execute(sql_task, (username, None, now, 1, userID))             
                except Exception as inst: 
                    Log("Error 4: UserID " + str(userID) + " konnte nicht als reciprocal eingefügt werden. Weder neu noch als Update", inst.args)    
        
        self.db.commit()   
    
    def update_non_reciprocals(self,non_reciprocals):           
        now = datetime.now() 
        for userID in non_reciprocals:
            username = non_reciprocals[userID]
            try: ##Insert new user, unless he already exist: check if we get metrics and use it over insert_follow func
                self.c.execute('''INSERT INTO Follows(userID, username, datefollow, dateunfollow, reciprocal, origin, date_engage, u) 
                VALUES(?,?,?,?,?,?,?,?)''', (userID, username, now, None, None, "private nonrec", now, 1) )             
                   
            except Exception:  
                try:      
                    sql_task = "UPDATE Follows SET username = ?, dateunfollow = ?, reciprocal = ?, u=?  WHERE userID = ?"
                    self.c.execute(sql_task, (username, None, None, 1, userID))             
                except Exception as inst: 
                    Log("Error 5: UserID " + str(userID) + " konnte nicht als nonreciprocal eingefügt werden. Weder neu noch als Update", inst.args)   
    
    ## To do: is this function necessary or is update_reciprocal sufficient?             
    def update_fans(self, fans, all_follows):
        now = datetime.now() 
        for userID in fans:
            username = fans[userID]
            try: ##Insert new user, unless he already exist: check if we get metrics and use it over insert_follow func
                self.c.execute('''INSERT INTO Follows(userID, username, datefollow, dateunfollow, reciprocal, origin, date_engage, u) 
                VALUES(?,?,?,?,?,?,?,?)''', (userID, username, None, None, now, "Fan", now, 1) )             
                   
            except Exception:  
                try:      
                    sql_task = "UPDATE Follows SET username = ?, reciprocal = ?, u=?  WHERE userID = ?"
                    self.c.execute(sql_task, (username, now, 1, userID))  
                    self.update_dateunfollow(userID, all_follows)
                except Exception as inst: 
                    Log("Error 5: UserID " + str(userID) + " konnte nicht als nonreciprocal eingefügt werden. Weder neu noch als Update", inst.args)   
               
    ## Deletes unfollow date in case user did it manually
    def update_dateunfollow(self,userID,all_follows):  
        old = datetime.now() 
        if all_follows[userID]['dateunfollow'] == None:
            self.c.execute('''UPDATE Follows SET dateunfollow = ? WHERE userID = ? ''',
                    (old, userID))                                         
            
    # to do: insert follow is broken            
    def update_user_status(self,userID,username,status):
        old =  datetime.date(1990,1,1)  
        if status == 'reciprocal':
            try:
                self.insert_follows(userID,username,status,old)      
            except Exception:
                self.update_nonreciprocal(userID)
                
        if status == 'nonreciprocal':
            try:
                self.insert_follows(userID,username,status,old)                
            except Exception:
                self.update_nonreciprocal(userID) 
                
    def update_engage(self,userID, datum): 
        self.c.execute('''UPDATE Follows SET date_engage = ? WHERE userID = ? ''',
         (datum, userID))            
        self.db.commit()                            
            
            
    def set_white(self, username):
        try:
            self.c.execute('''UPDATE Follows SET white = ? WHERE username = ? ''',
             (1, username))    
            Log("user " + username + " is white listed.")
            self.db.commit()    
        except Exception: 
            Log(username + " not included")
                    
                
        
    def connect_db(self,db):
        self.db = sqlite3.connect(db)
        self.c = self.db.cursor()        
        
                        

    def close(self):
        self.db.close()   
        
        
        ###################################################### Engagement STats
        
    def insert_liked(self, mediaID, likers):   
        for userID in likers:
            username = likers[userID]['username'] 
            is_private = likers[userID]['is_private']    
            mediaID_userID = str(mediaID) + ' ' + str(userID)
            
            try:
                self.c.execute('''INSERT INTO Liked(mediaID_userID, username, is_private)
                                  VALUES(?,?,?)''', (mediaID_userID, username, is_private))      
            except Exception:      
                continue
        self.db.commit()   

    def insert_commented(self, mediaID, commenters):   
        comment_count = 0
        for userID in commenters:
            for i in range( len(commenters[userID]) ): # in case same user has commented several times
                username = commenters[userID][i]['username'] 
                comment = commenters[userID][i]['comment']             
                is_private = commenters[userID][i]['is_private']    
                mediaID_userID_nr = str(mediaID) + ' ' + str(userID) + ' ' + str(i+1)
                try:
                    self.c.execute('''INSERT INTO Commented(post_nr, mediaID_userID_nr, username, comment, is_private)
                                      VALUES(?,?,?,?)''', (mediaID_userID_nr, username, comment, is_private)) 
                except Exception:      
                    continue
                comment_count += 1                      
        self.db.commit()   
        return comment_count


    def fetch_liked(self):       
        self.c.execute('''SELECT mediaID_userID, username, is_private FROM Liked''')
        own_posts = {}
        for row in self.c:   
            mediaID_userID = row[0]
            username = row[1]
            is_private = row[2]
            mediaID = int( mediaID_userID.split()[0] )
            userID = int( mediaID_userID.split()[1] )       
            temp = [userID, username, is_private]           

            if mediaID not in own_posts:
                own_posts[mediaID] = []
            own_posts[mediaID].append(temp)
        return own_posts    
    #delte helping function
    def update_liked(self, mediaID_userID, nr): 
        self.c.execute('''UPDATE Liked SET mediaID_userID = ? WHERE id = ? ''',
         (mediaID_userID, nr))            
   

    def fetch_commented(self):       
        self.c.execute('''SELECT mediaID_userID_nr, username, comment, is_private FROM Commented''')
        own_posts = {}
        for row in self.c:   
            mediaID_userID = row[0]
            username = row[1]    
            comment = row[2]
            is_private = row[3]
            mediaID = int( mediaID_userID.split()[0] )
            userID = int( mediaID_userID.split()[1] )
            nr = int( mediaID_userID.split()[2] )
            temp = [userID, username, nr, comment, is_private]
            if mediaID not in own_posts:
                own_posts[mediaID] = []
            own_posts[mediaID].append(temp)

        return own_posts  

    def vacuum(self):  
        Log("VACUUM:")
        self.c.execute("VACUUM")
#        self.db.close()   


