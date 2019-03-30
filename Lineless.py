# -*- coding: utf-8 -*-

"""
    #########################################################
    ###                                                   ###
    ###             Git - I am coming                     ###
    ###                                                   ###    
    #########################################################

Highlights:
    - increase likes per user from 3 to 4-5
    - func: calculateDuration
    - Port to Git
    - Update-friendship_recent Totaler neuer Approach
    - Delete orphan functions
    - fix big friendship
    - Inseret a function to delete every entry in a column
    - Bug fix: Bei Programmabsturz / Zu viele Follows Likes: wird Queue nicht überschrieben. Bereits gelikte media wurden nochmal geliket (Ältester bekannter bug)
    - bug fix: if less than 500 folowers in DB the script crashes because of the resolution in the engagment algorithm    
    - Bug fix: Continue if date_engage == private
    - Bug fix: Crash in Modul Commenter falls user gar keine Kommentare hat
    
To do: (short time):
    - Ladebalken für Loading
    - Separate Statistics from Lineless
    - Fix export: including Overview
    - Finalize comments stats
    - renaming API to usr in Instagram 
    - save all follows in usr and not Lineless
    - check time saving
    - Handle user management


To do (long term):
    - If a user deleted himself and I am following him it messes up statistics. Usually fakes.
    - ignore dried out users or hashtags for 30 days
    - Fix bug if Stats folder doesn't exist -> crash
 - fix that there are two connections to userDB (Vaccum bug)
- Engage module is still buggy and not straightforward
- import all likes into a dict
- fix infinte recurion if no tags or users fullfil criteria
- Queue update: consider expected like time and at least 60 s since last one
- optimize friendship update again. import shy fans over recent update. 
- Before you follow them. check whether they are already followers. otherwise ignore. They are already good fans
- dried out bool: Optizime time handling. import all in the first pic
- to do: if a user is dried out: save it in DB. Maybe date in the futur?
- To do: overwrite username during engagment to have the newest username
- To do: calculate time duration efficiencys
- To do: check in get_user_feed: there is a tag for status: Active
- To do: check last post for users otherwise ignore
- Optimize SQL handling accoring to: http://www.sqlitetutorial.net/sqlite-python/update/
"""

from random import randint
from datetime import datetime, timedelta
from Session_user import Session_user
from Session_login import Session_login
from Statistics import Statistics
import time, math
import sys
from urllib.request import urlopen
from Log import Log
from Metrics import Metrics
from Instagram import Instagram

class Lineless(object):       
    squser = ''
    sqlogin = ''
    all_follows = {}
    all_likes = {}    
    non_reciprocal = []
    engage = []
    followings = {} # All users I am currently following
    following_count = 0
    stats = ''
    queue = []
    username = '' 
    metrics = ''
    request_counter = ''
    API = ''
   
    def __init__(self,username):  
        start_time = time.time()  
        Log("\n Version: 81.0")
        
        self.username = username
        
        ## Connect to SQL database
        self.sqlogin = Session_login(username)
        self.squser = Session_user(username)    
        
      #  self.whitelisting()

        ## Import Queue
        self.queue = self.squser.fetch_queue()     

        ## Import all_follows and likes
        self.all_follows = self.squser.fetch_follows() #get all users ever followed                              

        self.all_likes = self.squser.fetch_likes()
        
        ## Can we for other rounds or are we at the limit with the follows and likes
        self.set_following_limit(username)
        
        pwd = self.sqlogin.d['pwd']      
        self.API = Instagram(username, pwd, self.sqlogin)
        
        ## Define non_reciprocals and followers to engage
        self.non_reciprocal = self.API.get_nonreciprocal(self.all_follows,1.5) #get all non_reciprocal users
      
        self.followings = self.API.get_followings(self.all_follows)
        self.following_count = len(self.followings)     
        Log("Number Followings: " + str(self.following_count))
        
        ## Do the statistics
        self.stats = Statistics(username, self.squser, self.all_follows, self.all_likes, self.followings, self.API)  
        self.engage = self.API.get_engagement(self.stats.followers, self.all_follows, 30) #get all users who need some attention    

        ## Login to IG in case works need to be done 

        if self.sqlogin.get_limits() > 0 and pwd != None: 
            
            self.API.login()    
            
            self.update_daily_stats()
            
            self.metrics = Metrics() ## initiate Metrics
            
#            self.extract_usernames()   
            
            self.magic_script()         

            self.API.logout()
        elif pwd == None:
            Log("Passiv Lineless successful")
        else:
            Log("You haven't waited long enough to play the game again")           
    
        self.updateDB()

        elapsed_time = time.time() - start_time 
        Log("\n Script end. Duration: " + str( round(elapsed_time/60,2 ) ) )
        
    def update_daily_stats(self):
        userID = self.sqlogin.d['userID']
        myself = self.API.getUserInfo(userID)
        follower_count =  myself["follower_count"]
        following_count = myself["following_count"]
        self.squser.insert_daily_stats(follower_count,following_count)

    def set_following_limit(self, username):
        now = datetime.now()
        if (now - timedelta(0.04) ) > self.sqlogin.d['last_update']:  # Erstversand
             self.sqlogin.set_limits(randint(90,105))
        Log("You can follow " + str( self.sqlogin.get_limits() ) + " other people.")        
         
   ## to do: delete after intialisation 
    def add_queue(self, userID, username, origin, mediaID = None, caption = None, metrics = None):
        now = datetime.now() 
        temp = {}
        ## Add user
        if mediaID == None:
            temp['user'] = [userID, username, origin, now, metrics]
        else: ## Add Like
            temp['media'] = [userID, username, origin, mediaID, caption, now]
        self.queue.append(temp)
        self.squser.insert_queues(self.queue)
        
    def add_queue_user(self, userID, username, origin, metrics):
        now = datetime.now() 
        user = {}
        user['user'] = [userID, username, origin, now, metrics]
        self.queue.append(user)
        self.squser.insert_queues(self.queue)      
        
    def add_queue_media(self, userID, username, origin, mediaID, caption):
        now = datetime.now() 
        media = {}
        media['media'] = [userID, username, origin, mediaID, caption, now]
        self.queue.append(media)
        self.squser.insert_queues(self.queue)          
    
    def pop_queue(self):
        if len( self.queue ) == 0:
            return False
        
        while True:
            item = self.queue[0]
            now = datetime.now()
            if 'media' in item:
                if (now - timedelta(0.02) ) < item['media'][5]: # wait at least 5 min
                    return False #wait longer         
            else:
                if (now - timedelta(0.02) ) < item['user'][3]: # wait at least 5 min
                    return False #wait longer         
            
            del self.queue[0]  
                     
            for t in item:
                userID = item[t][0]
                username = item[t][1]
                origin = item[t][2]
                
                if t == 'media':                                 
                    mediaID = item[t][3]                
                    caption = item[t][4]
                    if self.API.like(mediaID, userID, self.squser, origin, caption) == False:  
                        self.updateDB()
                        sys.exit()
                    Log("   Like: " + str(username)  )                          
                else: # user  
                    metrics = item[t][4]

                    if self.API.follow(userID, username, self.squser, origin, self.all_follows, metrics) == False:
                        self.updateDB() ## Exit Program
                        sys.exit()
                    self.sqlogin.update_limits(1)   
                    self.unfollow()     
                    # Repeat if queue is tFleisoo long
                    if len( self.queue ) > 500:
                        self.pop_queue()                    
                    return True
    
    # after 3 years. Here it is!                            
    def magic_script(self):  
        counter = 0
        
        while(self.sqlogin.get_limits() > 0 and counter < 100):
            random = randint(1, 4)   
                    
            if random == 1:
            ### Engage via Likes
                (userID, limit) = self.get_user('liker')   
                self.media_liker_module(userID, limit)          
            
            elif random == 2:
                ### Engage via Tags
                (tag, limit) = self.get_tag()          
                self.tag_module(tag, limit)                 
                            
            elif random == 3:                    
                ### Engage via Comments
                (userID, limit) = self.get_user('commenter')    
                self.commenter_module(userID, limit)
                
            elif random == 4:                    
                ### Engage via Comments
                self.engage_module(8)                
    
            else:   
                ### Engange old followers
                  
                self.metrics_module(2) 
                
            counter+=1;       

    # Calculates limit based on exp function: y = a * exp(b* x) + c
    def calculate_limits(self, efficiency_diff):
        self.sqlogin.fetch_login(self.username)               
      
        if efficiency_diff < 0:
            return 0
        
        print("Current Efficiency Diff: ", efficiency_diff)
        # Randbedingung (0,0)     (1,50)   (0.2/30)
        a = -50.5 # = -c
        b = -4.5
        limit = a * math.exp(b * efficiency_diff) - a
               
        if self.sqlogin.d['follows_left'] >= limit:
            return limit
        else:
            return self.sqlogin.d['follows_left']
        
    def tag_module(self,tag, limit):
        if tag == None or limit == 0:
            return False
        
        Log("\n__________ Tag Module __________")        
        tag_feed = self.API.getTagFeed(tag,1)
        following_count = 0
        self.squser.update_last_update(tag, 'Tag')         
        x = randint(0, 2)   # random starting post from 1 to 3 

        while following_count < limit:
            if x >= len(tag_feed) or following_count >= limit:
                break        
            
            userID = self.API.getUserID(tag_feed,x)  

            if not self.API.is_followed(userID,self.all_follows, self.queue): #post not liked and user never followed
                metrics = self.check_followbility(userID)
                if metrics == False:
                    x += 1
                    continue   
                                
                Log("Tag: " + tag + " Post Nr. " + str(x+1) + " / " + str( len(tag_feed)) )
                user_feed = self.API.get_user_feed(userID,2)
                origin = '# ' + tag 
                amount_likes = randint(4, 5)
                following_count += self.likePosts(user_feed,amount_likes, origin, 0, 150, metrics)   
                x += randint(1, 3) #choose next random post
            else:
#                print("User already followed: ", userID, " x:", x)
                x += 1 #check next user              
                    
    def media_liker_module(self,parent_userID, limit):
        if parent_userID == None or limit == 0:
            return False
        Log("\n__________ Media Liker Module __________")    
        self.squser.update_last_update(parent_userID, 'Liker')
        parent_feed = self.API.get_user_feed(parent_userID,1) 
        try:
            parentname = self.API.getUsername(parent_feed,0) 
        except Exception as inst: 
            Log(str(parent_userID) + " whats wrong wwith this feed. Fix and delete exception:", inst.args)
        following_count = 0   

        for i in range(len(parent_feed)):        
            if following_count >= limit:
                    break
                
            Log("Engage likers of " + parentname + " of Post Nr. " + str( i+1 ) + " / " + str( len(parent_feed)) )
            mediaID = self.API.getMediaID(parent_feed,i)
          
            likers = self.API.get_media_likers(mediaID) 
            
            ##╝ new metrics. Save all users who liked a particular mediaID
            tags = self.API.get_tags(parent_feed, i)
            location = self.API.get_location(parent_feed,i)
            self.metrics.import_meta(likers, str(mediaID), tags, str(location), 'Likers')
         
            
            ignore_count = 0
            
            for userID in likers:
                if following_count >= limit or ignore_count >= 500:
                    break
                
                ## check whether I already followed this person once
                is_private = likers[userID]['is_private']
                if not is_private and not self.API.is_followed(userID,self.all_follows, self.queue):  #user not private and never followed
                    ### is this person worth to follow according to metrics
                    metrics = self.check_followbility(userID)
                    if metrics == False:
                        continue                    
                    
                    user_feed = self.API.get_user_feed(userID,1)
                    origin = 'L ' + parentname + ' ' + str(mediaID)
                    amount_likes = randint(4,5)
                    following_count += self.likePosts(user_feed,amount_likes, origin, 10, 400, metrics)
                    
                else:
                    ignore_count +=1
                    if ignore_count >= 500:
                        Log(parentname + " is dried out")
                        break
               
    def commenter_module(self,parent_userID, limit):        
        if parent_userID == None or limit == 0:
            return False
        
        Log("\n__________ Commenter Module __________")                
        self.squser.update_last_update(parent_userID, 'Commenter')
        parent_feed = self.API.get_user_feed(parent_userID,1) 
        parentname = self.API.getUsername(parent_feed,0)               
        following_count = 0
        ignore_count = 0
        
        for i in range(len(parent_feed)):
            if following_count >= limit or ignore_count >= 30:
                    break
           
            mediaID = self.API.getMediaID(parent_feed,i) 
            mediaID = str(mediaID) #▲ to do: really?
            commenters = self.API.get_media_commenters(mediaID)   
            
            ##╝ new metrics. Save all users who liked a particular mediaID
            tags = self.API.get_tags(parent_feed, i)
            location = self.API.get_location(parent_feed,i)
            self.metrics.import_meta(commenters, str(mediaID), tags, str(location), 'Commenters')            
            
            
            for userID in commenters:
                if following_count >= limit:
                    break
                
                comments = commenters[userID] #list of all comments of this User. mostly only one
                if not self.API.is_followed(userID,self.all_follows, self.queue) and self.API.discriminate_comments(comments, 10):
                    metrics = self.check_followbility(userID)
                    if metrics == False:
                        continue   
                    
                    Log("Engage Commenters of " + parentname + " of Post Nr. " + str( i+1 ) +  " / " + str( len(parent_feed)) )
                    user_feed = self.API.get_user_feed(userID,1)
                    origin = 'C ' + parentname + ' ' + str(mediaID)
                    amount_likes = randint(4,5)
                    following_count += self.likePosts(user_feed,amount_likes, origin, 10, 1500, metrics)

                else:
                    ignore_count += 1
                    if ignore_count >= 30:
                        Log(parentname + " is dried out")
                        break

    def metrics_module(self, limit):        
        if limit <= 0:
            return False  
        
        Log("\n__________ Metrics Module __________")            
        metrics_feed = self.metrics.get_user(0,5)
        following_count = 0  
        
        for userID in metrics_feed:        
            if following_count >= limit:
                    break
                
            ## check whether I already followed this person once
            if not self.API.is_followed(userID,self.all_follows, self.queue): 
                ### is this person worth to follow according to metrics
                metrics = self.check_followbility(userID,True)
                user_feed = self.API.get_user_feed(userID,1)
                origin = 'ML ' + str(metrics_feed[userID])
                amount_likes = randint(4,5)
                following_count += self.likePosts(user_feed,amount_likes, origin, 0, 5000, metrics)                     
                    
                   
    def engage_module(self,amount):
            Log("\n__________ Engage Module __________")
            
            ######## 1. Engage shy fans ##########################       
            Log("Engage shy fans:")
            engage_count = 0 
            follow_count = 0
            for userID in self.stats.shy_fans:
                if engage_count >= amount/2: #half of the engagements for shy fans the rest for followers Delete
                    break
                ## ignore bots and private users
                if self.stats.shy_fans[userID]['count'] < 3 or self.stats.shy_fans[userID]['is_private'] == True: 
                      continue                   
                
                ## prefer user I never showed attention
                if not self.API.is_followed(userID, self.all_follows, self.queue):
                    user_feed = self.API.get_user_feed(userID,1)
                    if len(user_feed) == 0: #user is either private, deleted himself or blocked me. Anyway, we don't care
                        continue                    
                    
                    count = str( self.stats.shy_fans[userID]['count'] )
#                    print("user ", userID, " has NEVER been followed")
                    metrics = self.get_userinfo(userID)
                    like_counts = self.likePosts(user_feed, 2, 'shy_fan_' + count , 0, 5000, metrics)  
                    if like_counts >= 3:
                        username = self.API.getUsername(user_feed, 0)
                        print("userID 1: ", userID, " username ", username)
                        if not self.API.follow(userID, username, self.squser, 'shy_fan_' + count, self.all_follows):
                            self.updateDB()
                            sys.exit()
                        follow_count +=1                            
                        self.unfollow()
                        follow_count +=1                               
                        engage_count +=1      
                        
                elif self.API.is_followed(userID,{}, self.queue):
#                    print("Delete. this befindet sich in queue und muss nicht angeregt werden ", userID)
                    continue
                        
                # Otherwise only consider to be engage if not liked in the last 30 Days   
                else: 
                    try:
                        date_engage = self.all_follows[userID]['date_engage']
                    except Exception: 
                        Log("to do: delete, userid: " + userID)
                        
                    if date_engage == None or date_engage == 'private':
                        date_engage = self.all_follows[userID]['datefollow'] #private follows. Date of engagement is unknown
                        if date_engage == None or date_engage == 'private':
                            continue # to do: consider Fans
                    
                    now = datetime.now() 
                    # if not engaged in the last 30 days and not already sheduled in queue
                    if (now - timedelta(30) ) > date_engage and not self.API.is_followed(userID, {}, self.queue):
#                        print("user ", userID, " has ALREADY been followed but hasnt been engaged in the last 30 days")
                        user_feed = self.API.get_user_feed(userID,1)
                        if len(user_feed) == 0: #user is either private, deleted himself or blocked me. Anyway, we don't care
                            continue   
                        metrics = self.get_userinfo(userID)
                        self.likePosts(user_feed,2,'engage',0,5000, metrics)
                        self.squser.update_engage(userID, now)  
                        engage_count +=1   

            ######## 2. Engage own followers ##########################  
            Log("Own followers are getting engaged")
            while True:
                if len(self.engage) == 0 or engage_count >= amount:
                    break
                userID = self.engage[0][1] #oldest piece of shit. But userid is in second box
                del self.engage[0]
                Log("User wird motiviert " + str( userID) )
                user_feed = self.API.get_user_feed(userID,1)
                if len(user_feed) > 0:
                    now = datetime.now()   
                    metrics = self.get_userinfo(userID)                    
                    self.likePosts(user_feed,randint(1,2),'engage',0,20000, metrics)
                    self.squser.update_engage(userID, now)
                    engage_count +=1
                else:
                    Log("this user is private and can't be engaged: " + str( userID ) )
                    self.squser.update_engage(userID, 'private')                    
              
                # to do optimize
            self.all_follows = self.squser.fetch_follows()        
            self.sqlogin.update_limits(follow_count)           
                  

    def get_tag(self):       
        follows_left = self.sqlogin.d['follows_left']
        if follows_left <= 0:
            return (None, 0) # stop the magic script  
        now = datetime.now()  
        tags = self.squser.fetch_tags() # get targeted Hashtags
                
        temp = []
        for tag in tags:
            last_update = tags[tag]['last_update']
            efficiency = tags[tag]['efficiency']               
            if (now - timedelta(1000) ) > last_update:    #newly inserted hashtags have the highest priority     
                Log('\n New Tag: ' + tag + "  efficiency: " + str( round(efficiency,2) ) + "  limit: " + str( 40 ) )                   
                limit = 40
                if follows_left < 40:
                    limit = follows_left               
                
                return (tag, 40)
         
            temp.append( [efficiency, last_update, tag] )
        
        ### otherwise return hashtag with highest efficiency if it hasn't been used the last 3 hours
        temp.sort(reverse=True)
        for tag in temp:
            efficiency = tag[0]
            last_update = tag[1]
            tag = tag[2]                      
            if (now - timedelta(2) ) > last_update: 
                limit = self.calculate_limits(efficiency - self.stats.global_efficiency['tags'])    
                Log('\n Known Tag: ' + tag + "  efficiency: " + str( round(efficiency,2) ) + "  limit: " + str( limit)   )                             
                if follows_left < limit:
                    limit = follows_left                
                return (tag, limit)
            
        Log("You run out of hashtags. How is that even possible?")
        return (None, 0) ## incase none of the hashtags fullfill the criteria

    def get_user(self, module):       
        now = datetime.now() 
        follows_left = self.sqlogin.d['follows_left']
        if follows_left <= 0:
            return (None, 0) # stop the magic script
        users = self.squser.fetch_users()
                
        temp = []
        for user in users:
            last_update = users[user]['last_update']
            efficiency = users[user][module[0:1].upper() + '_efficiency']   
       
            if (now - timedelta(1000) ) > last_update:    
                Log('\n New user: ' + str( user ) + "  efficiency: " + str( round(efficiency,2) ) + "  limit: " + str( 40 )  )
                limit = 40
                if follows_left < 40:
                    limit = follows_left
                return (user, limit) #newly inserted user have the highest priority
           
            temp.append( [efficiency, last_update, user] )
        
        ### otherwise return hashtag with highest efficiency if it hasn't been used the last 3 hours
        temp.sort(reverse=True)
        
        for user in temp: 
            efficiency = user[0]
            last_update = user[1]
            userID = user[2]               
            if (now - timedelta(2) ) > last_update: #not used for at least 2 days. denn bei neuen muss sich erst stat heraustellen
                limit = self.calculate_limits(efficiency - self.stats.global_efficiency[module])    
                Log('\n Known user: ' + str( user ) + "  efficiency: " + str( round(efficiency,2)) + "  limit: " + str( limit ) )                        
                if follows_left < limit:
                    limit = follows_left
                return (userID, limit)
            
        Log("You run out of users. How is that even possible? Just wait 3 hours")
        self.extract_usernames()        
        return (None, 0) ## incase none of the users fullfill the criteria    
                   
    # To do. clean spaghetti code   
    def checkLikes(self,feed,i,minLikes,maxLikes,queue):
        mediaID = self.API.getMediaID(feed,i)
        likecount = self.API.get_like_count(feed,i)
        if likecount >= minLikes and likecount <= maxLikes and not self.API.isLiked(feed,i):
            for e in queue:
                if 'media' in e:
                    if e['media'][3] == mediaID:
                        Log("This post is already in queue. just wait for it ;) " + str( mediaID ) )
                        return False                    
            return True
        return False
   
    def get_userinfo(self, userID):
        user = self.API.getUserInfo(userID)
        
        follower_count = user["follower_count"]  
        following_count = user["following_count"]  
        media_count = user["media_count"]  
        is_private = user["is_private"] 
        
        metrics = {}
        metrics['follower_count'] = follower_count
        metrics['following_count'] = following_count
        metrics['media_count'] = media_count 
        metrics['is_private'] = is_private         
        
        print("userID: ", userID, " follower: ", metrics['follower_count'], "  following: ", metrics['following_count'])
        
  
        self.API.wait('short breath', "get UserInfo Lineless")
        
        return metrics
        
   
    def check_followbility(self, userID, metrics = False):
        metrics = self.get_userinfo(userID)
        
        ## Save metrics in Metrics DB
        self.metrics.update_userinfo(userID, metrics)
        
        followings = metrics['following_count']
        followers = metrics['follower_count']
        is_private = metrics['is_private']
        
        ## For metrics module: Continue independt of criteria
        if metrics:
            return metrics
        
        ### Only consider people who fullfil the following criteria:
        # - not private
        # - Less than 3000 followings
        # - less than 6000 followers
        # - more than 20 followers
        # - more than 20 followings
        if not is_private and followings < 3000 and followers < 6000 and followers > 20 and followings > 20:
            return metrics
        else:
            return False
        
    #Decide how much to unfollow
    def define_unfollow_count(self):               
        correction = self.following_count - self.sqlogin.d['max_following']
        if correction >= 2:
            unfollow_count = randint(1,2)
        elif correction == 1:
            unfollow_count = 1
        else:
            unfollow_count = 0
        self.following_count = self.following_count + 1 - unfollow_count
        return unfollow_count
        
    # check whether we can unfollow        
    # to do: clean about the spaghetti with tomato sauce. combine the three modules
    def unfollow(self):
        amount = self.define_unfollow_count()
               
        if amount == 0: ## no unfollowing needed
            return False        
        unfollow_count = 0
                
        ######## 1. Remove non_reciprocals ##########################                           
        users = []            
        for userID in self.non_reciprocal:
            ## ignore whiteliste
            if userID in self.all_follows and self.all_follows[userID]['whitelist']:
#                print("Dieser User darf nicht entfernt werden to avoid Sisi-Bug ", userID)
                continue             
                        
            # check Friendship over API
            friendship = self.API.checkFriendship(userID)  
            users.append(userID)         
            try:    
                if friendship["followed_by"] == False:
                    self.API.unfollow(userID,self.squser)
                    unfollow_count += 1
                    Log("       Unfollow: " + str( userID ) + "  " + self.all_follows[userID]['username'] + "  (" + str( len(self.non_reciprocal) ) + " non_reciprocals left)")
                    # End after 1 or 2 unfollows
                    if unfollow_count >= amount:
                        for userID in users: #remove checked users from non_reciprocal list
                            self.non_reciprocal.remove(userID)
                        return True     
                    
                # user is reciprocal
                else:
                    now = datetime.now()
                    self.squser.update_reciprocal(userID,now)
                    
            # user deleted himself        
            except Exception as inst: 
                Log("Something went wrong with: Deleted user" + str( userID ), inst.args)
                self.squser.update_unfollow(userID) 
        
                
        ######## 2. Remove followings with NO activity ##########################               
        for userID in self.stats.likeless_followers:
            
            if unfollow_count >= amount:
                return True
            
            ## Check whether I am following this user
            if userID not in self.followings: 
                continue
            
            if userID in self.all_follows and self.all_follows[userID]['whitelist']:
#                print("Dieser User darf nicht entfernt werden to avoid Sisi-Bug ", userID)
                continue   

            ## Check whether I have engaged this person at least 20 days ago (Enough time to import stats)
            date_engage = self.all_follows[userID]['date_engage']
            now = datetime.now() 
            if date_engage != None and date_engage < (now - timedelta(20)):
                self.API.unfollow(userID,self.squser)
                # remove user from current following list
                del self.followings[userID]

                Log("       Unfollow: " + str( userID) + "  " + self.all_follows[userID]['username'] + "  (" + str( len(self.stats.likeless_followers)) + " no activity users left)")
                unfollow_count += 1  
                self.all_follows[userID]['dateunfollow'] = now

        ######## 3. Remove followings with LOW activity ##########################      
        print("attention: now it gets personal")        
        
        for userID in self.stats.top_likers:
            if userID in self.all_follows and self.all_follows[userID]['whitelist']:
#                print("Dieser User darf nicht entfernt werden to avoid Sisi-Bug ", userID)
                continue   
            
            if unfollow_count >= amount:
                return True
            
            ## unfollow people with less than 2 likes and they had more than 60 days time
            if not self.stats.top_likers[userID]['count'] <= 8:
                continue              
            
            ## Check whether I am following this user
            if userID not in self.followings: 
                continue

            ## Check whether I have engaged this person at least 20 days ago 
            date_engage = self.all_follows[userID]['date_engage']
            now = datetime.now() 
            if date_engage != None and date_engage != 'private' and date_engage < (now - timedelta(20)):
                self.API.unfollow(userID,self.squser)
                # remove user from current following list
                del self.followings[userID]

                Log("       Unfollow: " +str( userID) + "  " + self.all_follows[userID]['username'] + "  (" + str( len(self.stats.likeless_followers)) + " low activity users left)")
                unfollow_count += 1  
                self.all_follows[userID]['dateunfollow'] = now
                        
    def likePosts(self,feed, amount, origin, minLikes, maxLikes, metrics):
        userID = self.API.getUserID(feed,0)
        x = randint(0, 2) # chose first random post from 1 to 3  
        post_like_count = 0
        while post_like_count < amount:
            if x >= len(feed):
                return False
            if self.checkLikes(feed,x,minLikes,maxLikes,self.queue):
                mediaID = self.API.getMediaID(feed,x)
                caption = self.API.get_caption(feed, x)
                if post_like_count < 2 or origin == 'engage': #user who only get engaged are not allowed to be added to queue
                    if self.API.like(mediaID,userID,self.squser, origin, caption) == False:
                        self.updateDB()
                        sys.exit()
                    Log("   Like: " + self.API.getUsername(feed,x) + "Nr: " + str( x+1) )
                else: #add to queue                        
                    self.add_queue_media(userID, self.API.getUsername(feed,x), origin, mediaID, caption)
                    
                post_like_count += 1
                x += randint(1,4)
            else:
                x += 1
        
        if post_like_count >= amount and origin != 'engage':                   
            username = self.API.getUsername(feed, 0)
            self.add_queue_user(userID, username, origin, metrics)
        else:
            return 0
        self.API.wait('short breath', "after LikePostsfunction")
        self.pop_queue()
        return 1
                
    # never used, but oldest code
    def comment(self,):
        self.API.tagFeed("loffel") # get media list by tag #cat
        media_id = self.API.LastJson # last response JSON
        print(len(media_id))            
        tst = media_id["ranked_items"][0]["pk"]
        print(tst)
        self.API.comment(tst,"Nice pic") # like first media
        user = self.API.getUserFollowers(media_id["ranked_items"][0]["user"]["pk"]) # get first media owner followers
        print(user)
           
    def extract_usernames(self):
        Log("Extract Usernames")
        #userID = self.API.get_userID('streetlife_award')
        userID = self.API.get_userID('hubs_united')        
        feed = self.API.get_user_feed(userID, 2)
        new_users = []
        for i in range(len(feed)):
            usernames = self.API.usernames_from_text(feed,i)
            new_users.append(usernames)
        
        for p in new_users:
            for username in p:
                userID = self.API.get_userID(username)
                if userID == 0:
                    continue
                self.squser.insert_user(userID,username)       
        self.squser.db.commit()
    
    def updateDB(self):       
        self.squser.insert_queues(self.queue)   
        self.stats.daily_stats()
        self.sqlogin.close()
        self.squser.close()
        if self.metrics != '':
            self.metrics.close()
        


    def check_internet(self, counter):
        try:
            urlopen('http://216.58.192.142', timeout=1)
            return True
#        except urllib.error as err: 
        except Exception:
            self.API.wait('short breath')
            counter+=1
            print("counter: ", counter)
            if counter < 100:
                self.check_internet(counter)
            else:
                return False
            
    def whitelisting(self):     
        white = ["ribudeinfroind","k____emma","haesch_di_taeg","timelessstyle50","frolein_j","nathxlie.k","missismagic_hair_mua","emilyroseirene","bernardo_uzeda","ta.n.ya","fran.zi.s","shotsbyjai","matilda_tws","papilloneffect","sa_jj_ad.askari","joytheangel","labangelina","lemonsoda_scrub","onatepauli","keshiawaters","dwiar55","jioparaiso","andre.alyt","pamisaaa","xx_v.e.r.o_xx","astridpalca","jkornprobst","stinerus","isKetch_zh","lin_fapou","nathalie_von_arx","putpurriii","ellle.7","circus_perfomers","elegantraveler","luca_82_ch","sebastiensatta","expl0_photo","7sevengirl","susassight","marian.good","franziskajann","kontal.kontil","gk_photoroom","rusjaandri","swiss_pepe","kellermarri","sarahrahelalena","tobiasweinhold","suprmeme_ch","lessielessie","jasy_k","bluegirl911","sharpfisch_artwork","wglove26","_vali.k","marina___marinchen","tardigradar","bettywooh","rischaswiss","wiwienne_yang","almazurich","minii_mandy","karesperanza","polaua","sushj92","sisizwae","jmfluna","kurusu_jp","philipmattinson","estherpamies_","maisathome","thegorgeousnothings1"]
        
        for username in white:
            self.squser.set_white(username)

usr = 'pixelline'
#usr = 'underfcuk'
#usr = 'mania4ania' ## Time to initiate new users
#usr = 'dress.the.stress' ## and here comes the second

Lineless(usr) 
#try:
#    Lineless(usr) 
#except Exception as inst:
#    Log("Lineless crashed ", inst.args)

