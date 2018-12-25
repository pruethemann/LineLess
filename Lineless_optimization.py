# -*- coding: utf-8 -*-
"""
- unique entry for liked and commented
- only update last 10 posts
- To do: Count likes and comments of posts and decide whether update is necessary

- Order Exports
To do: Add following state to ghosts
"""

from datetime import date, datetime, timedelta
from Instagram import Instagram
from Session_user import Session_user
from Session_login import Session_login
import time
from Log import Log

class Optimization(object):       
    API = ''
    squser = ''
    login_host = ''
    login_target = ''
    username_host = ''
    pwd = ''
   
    def __init__(self,username_target):  
        start_time = time.time()  
        
        ## Connect to SQL-DB HOST:
        username_host = 'underfcuk'
        self.login_host = Session_login(self.username_host)     
        pwd = self.login_host.d['pwd']
        
        ### To do: creating new API is not necessary
        self.API = Instagram(username_host, pwd, None)
        self.API.login()
        
        ## Connect to SQL db TARGET:         
        self.login_target = Session_login(username_target)
        self.squser = Session_user(username_target)
        userID_target = self.login_target.d['userID']         
        
        ### Import all own posts:
       # Activate self.import_own_posts(userID_target)                     

        ### Import all likes and comments and create XLS stats
      # Activate  self.update_engagement(userID_target)  

        ##  : update everything
        self.update_friendships(userID_target)                               
        
        ##  Followings and Followers update  
       # Activate self.update_friendships_recent(userID_target, 200)        

           
        ## Log out
        elapsed_time = time.time() - start_time 

        self.API.logout()  
        Log("\nEnd of Optimization: \n" + str( elapsed_time/60) )
               
            
    def test(self):
        myself = self.squser.fetch_own_posts()
        for p in myself:
            print(p)

    ## Engagement ##########################            
    def update_engagement(self, target_userID):       
        print("Update Engagement")
        
        # import stats of own_posts
        myself = self.squser.fetch_own_posts()
        
        limit = 0        
        for mediaID in myself:
            like_count_soll = myself[mediaID]["like_count_soll"]
            like_count_ist = myself[mediaID]["like_count_ist"]  
            undersampling = myself[mediaID]["undersampling"]  #amount of undersampling 0: no undersampling
            ### To do: Implement
            comment_count_soll = myself[mediaID]["comment_count_soll"]
            comment_count_ist = myself[mediaID]["comment_count_ist"]  
            
            if like_count_soll - like_count_ist - undersampling > 50: # to do: unless last_update is old
                self.API.login()
                likers = self.API.get_media_likers(mediaID) 
                self.squser.insert_liked(mediaID, likers)
                like_count_ist = len(likers)
                Log("Successfully imported. Likes Count: " + str( like_count_ist ) + " of mediaID " + str( mediaID ) + " Diff: " + str( like_count_soll - like_count_ist)  )  
                limit += 1
                if limit > 20: #limit to the last 6 pictures who need an update
                    Log("ATTENTION: NOT ALL LIKES OR COMMENTS HAVE BEEN IMPORTED. STATISTIC IS NOT REPRESENTATIVE. REPEAT UNTIL IMPORT IS COMPLETED")
                    break

            
    ## import own posts
    def import_own_posts(self, userID):  
        now = datetime.now()    
        if (now - timedelta(0.96) ) < self.login_target.d['last_update_own_posts']:            
            return False #update Like status not necessary  
        else:
            self.API.login()    
 
        ## amount of own posts        
        media_count = self.API.get_media_count(userID)
        
        myself_feed = self.API.get_user_feed(userID, 'All')    
               
        for nr, post in enumerate(myself_feed):
            mediaID = self.API.getMediaID(myself_feed, nr)
            like_count = self.API.get_like_count(myself_feed, nr)
            comment_count = self.API.get_comment_count(myself_feed, nr)
            upload_date = self.API.get_upload_timestamp(myself_feed, nr)
            location = self.API.get_location(myself_feed, nr)
            last_update = datetime.now()
            
            ## start counting at oldest post
            nr = media_count - nr
            
            if self.squser.insert_own_post(nr, mediaID, like_count, comment_count, upload_date, location,last_update) == False:
                self.squser.update_own_post_soll(mediaID, like_count, comment_count) ## update
       

        self.login_target.update_last_update_own_posts()
        return True # nötig für update_ist in Stats

    ## Friendship ##########################                  
                              
    def convert_to_dict(self, l):
        dic = {}
        for i in range( len(l) ):
           userID = l[i]["pk"]
           username = l[i]["username"]           
           dic[userID] = username
        return dic
           
    def define_reciprocals(self, followings, followers):
        reciprocals = {}
        reciprocals_set = followers.keys() & followings.keys()
        for userID in reciprocals_set:
            reciprocals[userID] = followings[userID]
        return reciprocals
    
    ## to do: check whether define_nonrecipticals and fans can be merged 
    def define_nonreciprocals(self, followings, followers):
        non_reciprocals = {}
        for userID in followings:
                if userID not in followers:
                    non_reciprocals[userID] = followings[userID]  
        return non_reciprocals

    def define_fans(self, followings, followers):
        fans = {}
        for userID in followers:
            if userID not in followings:
                fans[userID] = followers[userID]          
        return fans         
    
    def update_friendships(self,target_userID):
        now = datetime.now()
        if (now - timedelta(30) ) < self.login_target.d['last_update_friendship']:
            return False #Friendship-Update not yet necessary
        else:
            self.API.login()    
            
        all_follows = self.squser.fetch_follows()  
        
        print("\n__________ Big Friendship update __________ \n This will take a while. Lay back")                          
        followers_list = self.API.get_followers_feed(target_userID, 100) 
        following_list = self.API.get_following_feed(target_userID)
#
        print("Amount followers: ", len(followers_list))
        print("Amount following: ", len(following_list))
   
        followers = self.convert_to_dict(followers_list)
        followings = self.convert_to_dict(following_list)                    
        
        reciprocals = self.define_reciprocals(followings, followers)                 
        non_reciprocals = self.define_nonreciprocals(followings, followers)  
        fans = self.define_fans(followings, followers)        
               
        Log("\nAmount Reciprocals users: " + str(len(reciprocals)))
        Log("Amount of Nonreciprocal users: " + str(len(non_reciprocals)))
        Log("Amount of Fans: " + str(len(fans)))
        
        ## Update reciprocals, Non_reciprocals and fans: Check: There should be no old reciprocal date left
        self.squser.update_reciprocal(reciprocals, all_follows)
        self.squser.update_non_reciprocals(non_reciprocals, all_follows)
        self.squser.update_fans(fans, all_follows)
        self.squser.db.commit() 
                    
        ### remove all users who were fans
        for userID in all_follows:
            if all_follows[userID]['dateunfollow'] != None:
                continue
            if userID not in reciprocals:
                if userID not in non_reciprocals:
                    if userID not in fans:                        
                        self.squser.update_friendship(userID,None, None) 
                    
        self.squser.db.commit()  
        self.login_target.update_last_update_friendship()
        #self.export_friendship(followers, followings, 'before_')    
        #self.export_calc_friendship(reciprocals, non_reciprocals, fans)
        
    # inserts preexisting followers            
    def update_friendships_recent(self,target_userID, recent):
        now = datetime.now()        
        if (now - timedelta(1) ) < self.login_target.d['last_update_friendship_recent']:
            return False #Friendship-Update not yet necessary
        else:
            self.API.login()    
        
        print("\n__________ Small Friendship update __________\n This will take a while. Lay back")   
                
        if recent == 'All':
            recent = 20000
        
        followers = self.API.get_followers_feed(target_userID,recent) 
        following = self.API.get_following_feed(target_userID)

        print("Amount followers: ", len(followers))
        print("Amount following: ", len(following))
        
        now = datetime.now()
        for i in range(len(followers)):
            userID = followers[i]["pk"]
            username = followers[i]["username"] 
            try: 
                self.squser.update_reciprocal(userID,now)
                #userID, username, datefollow, dateunfollow, reciprocal, origin,date_engage                
            except Exception:# (userID, reciprocal, dateunfollow)               
                self.squser.insert_follows(userID, username, None, None, now, 'Fan', None)
   
        now = datetime.now()
        for i in range(len(following)):
            userID = following[i]["pk"]
            username = following[i]["username"] 
            try: 
                self.squser.insert_follows(userID, username, now, None, None, 'Private_follow', None)      
                #userID, username, datefollow, dateunfollow, reciprocal, origin,date_engage               
            except Exception:# (userID, reciprocal, dateunfollow)  
                continue
                print("was this a private move? ", username)
                    
        self.squser.db.commit() 
        self.login_target.update_last_update_friendship_recent()        
  
    def updateDB(self):       
        self.stats.daily_stats()
        self.login.close()
        self.login_target.close()
        self.squser.close()



#username_target = 'pixelline'
#Optimization(username_target)    