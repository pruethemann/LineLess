# -*- coding: utf-8 -*-
from InstagramAPI import InstagramAPI
from random import uniform
import time
from datetime import datetime, timedelta
from Log import Log
import sys

class Instagram(object):    
    API = ''
    username = ''
    pwd = ''
    requests = []
    likes = []
    follows = []
    daily_likes = 0 #likes count int the last 24 hours
    daily_follows = 0 
    sqlogin = "" ### To do: used for get the limits. This is not beautiful
    
    
    def __init__(self, username, pwd, sqlogin):
        self.username = username
        self.pwd = pwd
        self.sqlogin = sqlogin
        
    def login(self):
        if self.API == '':  
            try:
                API = InstagramAPI(self.username, self.pwd)
                API.login()
                self.add_request()        
                self.API = API
            except Exception:
                Log("Login failed. Be careful man. otherwise you get banned")
                self.API =  False    
        else:
            return True
        
    def logout(self):
        if not self.API == '':  
            self.API.logout()
        
    def add_request(self):
        now = datetime.now()  
        
        for r in self.requests:       
            if (now - timedelta(1/1440) ) > r:  ##î Request ist älter als 1 min und kann gelöscht werden
                self.requests.remove(r)
        
       
        x = len(self.requests)     
        if x > 50:
            print("Amount of requests in the last minute: ", x)
        if x > 150: ### more than 190 requests are critical. 200 per Minute is absolute max
            Log("ATTENTION. Maxiumum requests reached. Please wait.")
            self.wait("idle break")
            ## check that enough time passed
            self.add_request()
        else:
            ### add new timestamp        
            self.requests.append(now) 
            
    def add_likes(self):
        now = datetime.now()         
        for l in self.likes:       
            if (now - timedelta(1/24) ) > l:  ## Likes count in the last 1 hour
                self.likes.remove(l)        
      
        #print("Likes in the last 1 hour: " , len(self.likes)  )
        if len(self.likes) > 290: ### more than 290 likes are critical. 300 - 350 likes are allowed per hour
            Log("ATTENTION. Maxiumum like count reached in the last hour. Please wait.")
            self.wait("extreme")
            ## check that enough time passed
            self.add_likes()
        else:
            ### add new timestamp        
            self.likes.append(now)              
            
    def add_follows(self):
        now = datetime.now()         
        for f in self.follows:       
            if (now - timedelta(1/24) ) > f:  ## Likes count in the last 1 hour
                self.follows.remove(f)
        
      #  print("Follows in the last 1 hour: " , len(self.follows))  
        if len(self.follows) > 90: ### more than 80 follows are critical. 80 - 160 follows/unfollows per hour are allowed
            Log("ATTENTION. Maxiumum follow count reached in the last hour. Please wait.")
            self.wait("extreme")
            ## check that enough time passed
            self.add_follows()    
        else:
            self.follows.append(now)         ### add new timestamp


    def getTagFeed(self,tag,next_max):
        feed = []
        next_max_id = ''
        for n in range(next_max):
            self.add_request()
            self.API.getHashtagFeed(tag,next_max_id) 
            temp = self.API.LastJson
            for post in temp["items"]:
                feed.append(post)
            self.wait('short', "getTagFeed")
            try:
                next_max_id = temp["next_max_id"]     
            except Exception:
                 Log("error next_max. Tag: " + tag)                   
        return feed
    
    # new user_feed: what a mistery
    def get_user_feed(self,userID,next_max):
        feed = []
        next_max_id = ''
        if next_max == 'All':
            next_max = 1000
            Log("All posts of user " + str( userID ) + " will be imported. This may take a while ..")
            
        while len(feed) < next_max:
            self.add_request()
            self.API.getUserFeed(str(userID),next_max_id) 
            userFeed = self.API.LastJson
            if 'items' in userFeed:
                for post in userFeed["items"]:
                    feed.append(post)
            else:
                return [] #user is private
            self.wait('short breath', "getUserFeed")
            try:
                next_max_id = userFeed["next_max_id"]     
            except Exception:
                break
        if next_max > 2:
            print(len(feed), " posts have been imported.")  
        if len(feed) == 0:
            return []
        return feed    
        
    def discriminate_comments(self,comments, min_length):
        #Combine all comments, to one comment. the more comments the higher the rating
        comment = ''
        for commenter in comments:
            comment += " " + commenter['comment']
           
        usernames = self.usernames_from_text(comment)
        comment_length = len(comment)
        for username in usernames:
            comment_length -= len(username)  
                
        if comment_length >= min_length:      
            return True 
        else:
            return False
    
    
    def get_media_commenters(self,mediaID):
        media_commenters = {}
        next_max_id = ''
        while True:
            self.add_request()
            self.API.getMediaComments(mediaID, next_max_id)       
            feed = self.API.LastJson      
            
            for i in range( len(feed["comments"]) ):
                commenter = {}
                userID = feed["comments"][i]["user"]["pk"]
                commenter['username'] = feed["comments"][i]["user"]["username"]
                commenter['comment'] = feed["comments"][i]["text"]
                commenter['is_private'] = feed["comments"][i]["user"]["is_private"]        
                if userID not in media_commenters:
                    media_commenters[userID] = []           
                media_commenters[userID].append(commenter)        
                self.wait('short breath', "getMedia_commenters while extending") 
    
            if 'next_max_id' in feed: #Delete: Wow this works. it's a miracle. I am wondering why it works to import all the likers or it doesnt?
                next_max_id = feed["next_max_id"]    
            else:
                break
    
        return media_commenters
      
    
    def get_media_likers(self,mediaID): 
        self.add_request()
        self.API.getMediaLikers(mediaID)
        feed = self.API.LastJson
        media_likers = {}
        for i in range(len(feed['users'])):
            liker = {}
            userID = feed["users"][i]["pk"]
            liker['username'] = feed["users"][i]["username"]  
            liker['is_private'] = feed["users"][i]["is_private"]         
            media_likers[userID] = liker
    
        self.wait("short", "get_media_likers")
        return media_likers
    
    
    #returns full list of all userids who were liking a post    
    
        
    
    def get_followers_feed(self,userID, minCount):    
        followers = []
        next_max_id = ''
        # to DO: Fix if big_list not necessary
    
        while len(followers) < minCount:
            self.add_request()
            self.API.getUserFollowers(userID, next_max_id)
            temp = self.API.LastJson
            for item in temp["users"]:
                followers.append(item)
            Log(str( len(followers) ) + " Followers loaded.")
            self.wait('short', "getFollowersfeed")
    
            if not temp['big_list']:
                break
            next_max_id = temp["next_max_id"]
            
        if len(followers) > 200:
             print("Amount imported followers: ", len(followers))
             
        followers = self.convert_to_dict(followers)
    
        return followers   
    
    def convert_to_dict(self, l):
            dic = {}
            for i in range( len(l) ):
               userID = l[i]["pk"]
               username = l[i]["username"]           
               dic[userID] = username
            return dic      
    
    # I have no clue how this works, but it's working.
    def get_following_feed(self,userID):    
        following = []
        next_max_id = ''
        while True:
            self.add_request()
            self.API.getUserFollowings(userID, next_max_id)
            temp = self.API.LastJson
            for item in temp["users"]:
                following.append(item)
            print(len(following), " Following loaded.")            
            self.wait('short', "getFollowingFeed")
            if not temp['big_list']:
                break
            next_max_id = temp["next_max_id"]
            
        if len(following) > 200:
             print("Amount imported followings: ", len(following))
        return following
    
          
    def follow(self,userID,username,sqluser,origin,all_follows, metrics):
        now = datetime.now()  
        self.add_request()
        self.add_follows()       
                 
        try:
            if self.API.follow(userID):
                sqluser.insert_follows(userID, username, now, None, None, origin, now, metrics)
     
                #add now follower data to cache To do: add follower and following_count
                follower = {}
                follower['username'] = username  
                follower['datefollow'] = now           
                follower['dateunfollow'] = None
                follower['reciprocal'] = None           
                follower['origin'] = origin                
                follower['date_engage'] = now        
                follower['whitelist'] = False
                all_follows[userID] = follower  
              
                self.wait("middle", "FOLLOW")                           
                Log("   User: " + username + " (" + str( userID ) + ") followed ")
                self.daily_follows +=1
                #print("Daily Follows: ", self.daily_follows)
                if self.daily_follows > 290:
                    Log("ATTENTION. Daily FOLLOW counts reached. " +  str(self.daily_follows))
                    return False ## Programm wird beendet
                    
                limit = self.sqlogin.get_limits() 
                print("Limit: ", limit)
                
                if limit < 0:
                    Log("Script stopped. " + str(self.daily_follows))
                    sys.exit()
            else:
                print("User ", userID, " hasn't been followed for unknown reasons")
                    
        except Exception as inst:
            Log("Something is wrong with. Follow Module " + str( userID ) + " " + str(username), inst.args)   
            print(inst.args)
            print(type(inst.args))                      
        
    def like(self,mediaID,userID,sqluser,origin,caption):
     #   print("media " , mediaID, " userID ", userID, " origin ", origin )
        self.add_request()
        self.add_likes()
        if self.API.like(mediaID):
            sqluser.insert_likes(mediaID, userID,origin,caption)
            self.daily_likes +=1
            #print("Daily Likes: ", self.daily_likes)
            if self.daily_likes > 1450:
                Log("ATTENTION. Daily like counts reached. " + str(self.daily_likes))
                print("ich werde ausgelöst")
                return False
        self.wait("middle", "Like")
        
    
    def unfollow(self,userID,sql):
        self.add_request()
        self.add_follows()
        if self.API.unfollow(userID):  ### Falls user entfolgt wird und alles gut get
            sql.update_unfollow(userID) 
        else: ## user hat sich selbst gelöscht
            sql.update_unfollow(userID) ### To do: Als gelöscht eintragen
        self.wait("middle", "Unfollow")

            
    def checkFriendship(self,userID):
        self.add_request()
        self.API.userFriendship(userID)
        self.wait("short breath", "checkFriendship")
        return self.API.LastJson      
    
    def getUserInfo(self,userID):
        self.add_request()
        self.API.getUsernameInfo(userID)
        user = self.API.LastJson
        self.wait("short breath")
        try:
            return user["user"]
        except Exception as inst:
            print("Something wrong with user: ", userID, " Message: ", user)
            print(inst.args)
    
    def get_media_count(self,userID):
        self.add_request()
        self.API.getUsernameInfo(userID)
        user = self.API.LastJson
        return user["user"]["media_count"]
    
    #Combinine those
    def get_userID(self,username):
        self.add_request()
        self.API.searchUsername(username) # user_name to user_id
        try:
            return self.API.LastJson["user"]["pk"]
        except Exception:
            Log('Error get userID: ' + username, self.API.LastJson) #user exisitiert nicht
            return False
        
    def get_user_tags(self,userID):
        self.add_request()
        self.API.getUserTags(userID)
        return self.API.LastJson
    
    def getUserID_API(self,mediaID):
        self.add_request()
        self.API.mediaInfo(mediaID)
        post = self.API.LastJson # last response JSON
        userID = post["items"][0] #["pk"]
        return userID
    
    
    #################################################
    #               No API requests                 #    
    #################################################
    
    ### returns List of all users who deserve to be liked again. Order according to last_engaged
    def get_engagement(self,followers, all_follows, duration):
        engage = []
        old =  datetime(1989,1,1)      
        now = datetime.now()  
        
        for userID in followers:
            date_engage = all_follows[userID]['date_engage']
            if date_engage == None: # Real fans or Bot bastards like me
                engage.append([old, userID]) 
            elif date_engage == 'private':
                continue # can't do anything in this case
            elif (now - timedelta(duration) ) > date_engage:
                engage.append([date_engage, userID]) 
            else:
                continue  # engange < 30 days
                
        engage.sort()         
        return engage
    
        
    def is_followed(self,userID,all_follows, queue):
        # check whether followed in the passed
        if userID in all_follows:
            return True
        # check whether followed in the futur
        for user in queue:
            if 'media' in user:
                if userID == user['media'][0]:
                    return True
        return False
    
    def get_nonreciprocal(self,all_follows,duration):
        non_reciprocal = []
        for userID in all_follows:
            if all_follows[userID]['dateunfollow'] == 'white':
                continue #white lists werden ignoriert
            if all_follows[userID]['dateunfollow'] == None and all_follows[userID]['reciprocal'] == None and all_follows[userID]['datefollow'] != None: #never unfollowed so far and non_reciprocal  
                now = datetime.now()
                if (now - timedelta(duration) ) > all_follows[userID]['datefollow']:  # Erstversand
                    non_reciprocal.append(userID)                
        return non_reciprocal #only userID of potential non_reciprocal users 1. never been unfollowed 2. proven to be nonreciprocal 3.followed longer ago than certain duration
    
    
    #def get_following_count(all_follows):
    #   following_count = 0
    #   for userID in all_follows:
    #        if all_follows[userID]['dateunfollow'] == None and all_follows[userID]['datefollow'] != None: 
    #            following_count += 1              
    #   return following_count 
    
    def get_followings(self,all_follows):
       followings = {}
       for userID in all_follows:
            if all_follows[userID]['dateunfollow'] == None and all_follows[userID]['datefollow'] != None: 
                followings[userID] = all_follows[userID]['username']               
       return followings 
    
          
    def get_followers(self,all_follows):
       followers = {}
       for userID in all_follows:
            if all_follows[userID]['reciprocal'] != None: 
                followers[userID] =  all_follows[userID]['username']  
       return followers
    
    def getUserID(self,feed,i):
        try:
            return feed[i]["user"]["pk"]  
        except Exception:
            Log("User either deleted himself or blocked me " + str(feed) )
            return False
    
    def getMediaInfo(self,mediaID,API):
        API.mediaInfo(mediaID)
        post = API.LastJson
        return post[0]
    
    def getMediaID(self,feed,i):
        mediaID = feed[i]["pk"] 
        return mediaID       
            
    def isLiked(self,feed,i):
        return feed[i]["has_liked"] 
    
    def get_like_count(self,feed,i):
        return feed[i]["like_count"]
    
    def get_comment_count(self,feed,i):
        return feed[i]["comment_count"]
    
    def get_location(self,feed,i):
        return feed[i]["taken_at"]
    
    def get_upload_timestamp(self,feed,i):
        return feed[i]["device_timestamp"]
    
    def get_caption(self,feed,i):
        try:
            return feed[i]["caption"]["text"]
        except Exception:
            return None
    
    def getUsername(self,feed,i):
        return feed[i]["user"]["username"]
        
    def get_tags(self,feed,i):
        text = feed[i]["caption"]
        if text == None:
            return None ## no caption
        text = text["text"] 
        not_included = ['!', '$','%','^', '&', '*', '+', '.', ' ', '#','\n']
        tags = []
        tag = ''
        read = False
        for l in text:
            if l in not_included and read == True:
                tags.append(tag)
                read = False
                tag = ''
            if read == True:
                tag += l   
            if l == '#':
                read = True        
        return tags
    
    
    def usernames_from_text(self,feed,i = None):
        if i == None:
            text = feed
        else:
            text = feed[i]["caption"]["text"]
            
        not_included = ['!', '$','%','^', '&', '*', '+', ' ', '#','@','\n']
        usernames = []
        username = ''
        read = False
        for l in text:
            if l in not_included and read == True:
                usernames.append(username)
                read = False
                username = ''
            if read == True:
                username += l   
            if l == '@':
                read = True        
        return usernames
    
    def set_daily_stats(self,daily_likes, daily_follows):
        self.daily_likes = daily_likes
        self.daily_follows = daily_follows
    
    
    def wait(self,a,origin=None):
    
        if a == 'short breath':
            t = uniform(0.12,2.2)
        elif a == 'short':
            t = uniform(3.5,7)
        elif a == 'middle':
            t = uniform(5,13)
        elif a == 'long':
            t = uniform(12,30)
        elif a == 'extreme':
            t = uniform(30,60)
            print("wait extreme ", t)  
        elif a == "idle break:":
            t = uniform(30,45)
        else:
            t = uniform(1,3)
            print("Yo no how to type!!")
    
    #    print("Wait: ", round(t,2) , " from: ", origin)
        time.sleep(t)   