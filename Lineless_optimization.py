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
    login_target = '' ##pixelline
    username_host = ''
    pwd = ''
   
    def __init__(self,username_target):  
        start_time = time.time()  
        
        ## Connect to SQL-DB HOST:
        username_host = 'underfcuk'
        self.login_host = Session_login(self.username_host)     
#        pwd = self.login_host.d['pwd'] ### To do: Fix this shit
        pwd = "atleastitried"  ## to do fix: get the right user handling
        print("pwd under ", pwd)
        
        ### To do: creating new API is not necessary
        self.API = Instagram(username_host, pwd, None)
        self.API.login()
        
        ## Connect to SQL db TARGET:         
        self.login_target = Session_login(username_target)
        self.squser = Session_user(username_target)
        userID_target = self.login_target.d['userID']         
        
        ### Import all own posts:
        self.import_own_posts(userID_target)                     

        ### Import all likes and comments and create XLS stats
        self.update_engagement(userID_target)  

        ##  : update Friendship
        self.update_friendships(userID_target)                               
        
        self.update_friendship_recent(userID_target, 200)
           
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
        if not self.olderThan(0.96, self.login_target.d['last_update_own_posts']):
            return False       
 
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
           
    def define_reciprocals(self, followings, followers):
        reciprocals = {}
        reciprocals_set = followers.keys() & followings.keys()
        for userID in reciprocals_set:
            reciprocals[userID] = followings[userID]
        Log("\nAmount Reciprocals users: " + str(len(reciprocals)))
        return reciprocals
    
    ## to do: check whether define_nonrecipticals and fans can be merged 
    def define_nonreciprocals(self, followings, followers):
        non_reciprocals = {}
        for userID in followings:
                if userID not in followers:
                    non_reciprocals[userID] = followings[userID]  
        Log("Amount of Nonreciprocal users: " + str(len(non_reciprocals)))
        return non_reciprocals

    def define_fans(self, followings, followers):
        fans = {}
        for userID in followers:
            if userID not in followings:
                fans[userID] = followers[userID] 
        Log("Amount of Fans: " + str(len(fans)))        
        return fans         
          
    def update_friendship_recent(self, target_userID, follower_amount):
        if not self.olderThan(0.95, self.login_target.d['last_update_friendship_recent']):
            return False                
        
        Log("\n__________ Small Friendship update __________ \n This will take a while. Lay back")                          
        followers = self.API.get_followers_feed(target_userID, follower_amount) ## To do: change to all    

        ## Update only the status of the last 200 Followers
        for userID in followers:
            try:    ## update reciprocal
               self.squser.update_follower(userID)
            except Exception as inst:                                   ## insert falls private follow
                self.squser.insert_follows(userID, followers[userID], datetime.now(), None, None, "Fan", datetime.now(), None) 
                
        self.squser.db.commit()  
        self.login_target.update_last_update_friendship_recent()                        
    
    def update_friendships(self,target_userID):
        if not self.olderThan(30, self.login_target.d['last_update_friendship']):
            return False
            
        all_follows = self.squser.fetch_follows()  
        
        Log("\n__________ Big Friendship update __________ \n This will take a while. Lay back")                          
        followers = self.API.get_followers_feed(target_userID, 15000) ## To do: change to all
        followings = self.API.get_following_feed(target_userID)                 
        
        ## Create dics of reciprocals, non_reciprocals and fans
        reciprocals = self.define_reciprocals(followings, followers)                 
        non_reciprocals = self.define_nonreciprocals(followings, followers)  
        fans = self.define_fans(followings, followers)        
        
        ## Update reciprocals, Non_reciprocals and fans: Check: There should be no old reciprocal date left
        self.squser.update_reciprocal(reciprocals)  
        self.squser.update_non_reciprocals(non_reciprocals)
        self.squser.update_fans(fans, all_follows)
        self.squser.db.commit() 

                    
        ### remove all users who were fans
        for userID in all_follows:
                if userID not in reciprocals:
                    if userID not in non_reciprocals:
                        if userID not in fans:   
                            ## All those user are not following and I am not following them To do: Solve more elegant. remove u
                            self.squser.update_dateunfollow(userID, all_follows)  ## 
                            sql_task = "UPDATE Follows SET reciprocal = ?, u = ?  WHERE userID = ?"
                            self.squser.c.execute(sql_task, (None, None, userID))   
                    
         
        ## Update dates of last update date in Login
        self.squser.db.commit() 
        self.login_target.update_last_update_friendship()
        self.login_target.update_last_update_friendship_recent()
        #self.export_friendship(followers, followings, 'before_')    
        #self.export_calc_friendship(reciprocals, non_reciprocals, fans)
             
  
    def updateDB(self):       
        self.stats.daily_stats()
        self.login.close()
        self.login_target.close()
        self.squser.close()
        

    def olderThan(self, duration, last_occurence):
        now = datetime.now()
        if (now - timedelta(duration) ) < last_occurence:
            return False #Friendship-Update not yet necessary
        else:
            self.API.login()   
            return True