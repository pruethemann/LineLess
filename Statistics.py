# -*- coding: utf-8 -*-
from Instagram import Instagram
import xlsxwriter, os
from datetime import datetime, timedelta
from Lineless_optimization import Optimization
import numpy as np
from Log import Log
import time


class Statistics(object):       
    all_follows = {}
    likes = {}
    squser = ''
    stats = {}
    global_efficiency = {}
    followers = 0    
    API = ''
    

    top_likers = {}
    top_commenters = {}
    likeless_followers = {}
    commentless_followers = {}
    ghost_followers = {}
    shy_fans = {}
    likes_own_posts = {}
    own_posts = {} ## to do: remove in Optimizsation
    
    
    def __init__(self,username, squser, all_follows, all_likes, followings, API):  
        ## First check whether new data needs to be imported:
        Optimization(username)      
        
        # Save all data from Lineliness
        self.squser = squser
        self.all_follows = all_follows             
        self.likes = all_likes     
        
        self.API = API
        
        start_time =  time.time()
        ### To do: save all_follows in API
        self.followers = self.API.get_followers(all_follows)
        
        
           
        ## Calculate efficiency and export it        
        self.calc_efficiency()
        self.daily_stats() # print statistics 

        
        ## Calculate Engagement
        start_time  = time.time()
        self.likes_own_posts = self.squser.fetch_liked()  
        elapsed_time = time.time() - start_time  
        print("Time Likes ", elapsed_time/60)         
        self.own_posts = self.squser.fetch_own_posts()
        self.update_ist_counts() ##place after optimizsaiton
        self.top_likers = self.get_top_likers()  
        
        self.top_commenters = self.get_top_commenters()        
        self.likeless_followers = self.get_likeless_followers(self.top_likers, self.followers)
        self.commentless_followers = self.get_commentless_followers(self.top_commenters, self.followers)
        self.ghost_followers = self.get_ghostfollowers(self.likeless_followers, self.commentless_followers)
        self.shy_fans = self.get_shy_fans(self.top_likers, self.top_commenters, self.followers)
        elapsed_time = time.time() - start_time  
        print("Time Assembly ", elapsed_time/60)         
        
        start_time =  time.time()
        self.export_statistics(followings, all_follows, username)  
        elapsed_time = time.time() - start_time 
        print("Time Export ", elapsed_time/60)   
    
    ## rate users according number of likes        
    def get_top_likers(self):  
        top_likers = {}       
        for mediaID in self.likes_own_posts:
            for user in range(len(self.likes_own_posts[mediaID])):
                userID = self.likes_own_posts[mediaID][user][0]
                username = self.likes_own_posts[mediaID][user][1]
                is_private = self.likes_own_posts[mediaID][user][2]
                post_nr = self.own_posts[mediaID]['post_nr']
                if userID not in top_likers:
                    liker = {}
                    liker['username'] = username
                    liker['count'] = 1
                    liker['first_post'] = post_nr
                    liker['last_post'] =  post_nr 
                    liker['is_private'] = is_private                     
                    top_likers[userID] = liker
                else:
                    liker = top_likers[userID]
                    liker['count'] += 1
                    ## find first and last post
                    if post_nr < liker['first_post']:
                        liker['first_post'] = post_nr
                    if post_nr > liker['last_post']:
                        liker['last_post'] = post_nr
                 
                    top_likers[userID] = liker 

        return top_likers
    
                       
    ## rate users according number of comments         
    def get_top_commenters(self):
        posts = self.squser.fetch_commented()       
        top_commenters = {}       
        for mediaID in posts:
            for user in range( len(posts[mediaID]) ):
                userID = posts[mediaID][user][0]
                username = posts[mediaID][user][1]
#                comment = posts[post_nr][user][2]                
                is_private = posts[mediaID][user][2]
                post_nr = self.own_posts[mediaID]['post_nr']   
                
                if userID not in top_commenters:
                    liker = {}
                    liker['username'] = username
                    liker['count'] = 1
                    liker['first_post'] = post_nr
                    liker['last_post'] =  post_nr 
                    liker['is_private'] = is_private                     
                    top_commenters[userID] = liker
                else:
                    liker = top_commenters[userID]
                    liker['count'] += 1
                    if post_nr < liker['first_post']:
                        liker['first_post'] = post_nr
                    if post_nr > liker['last_post']:
                        liker['last_post'] = post_nr             
                    top_commenters[userID] = liker                                                   
        return top_commenters    
    
    
    
    ## Update ist counts of likes and comments       
    def update_ist_counts(self):       
        myself = self.squser.fetch_own_posts()
        
        for mediaID in myself:
            like_count_soll = myself[mediaID]["like_count_soll"]
            try:
                like_count_ist = len( self.likes_own_posts[mediaID] )
            except Exception:   ### in case mediaID has no likes yet or likes haven't been imported yet
                like_count_ist = 0
            comment_count = 0  ## to do: implent comments
            undersampling = like_count_soll - like_count_ist
            self.squser.update_own_post_ist(mediaID, like_count_ist, comment_count, undersampling)
    

    # Predict followers who did not like
    def get_likeless_followers(self, top_likers, followers):
        likeless_followers = {}
        for userID in followers:
            if userID in top_likers:
                continue
            likeless_followers[userID] = followers[userID]
        return likeless_followers
    
    # Predict followers who did not comment    
    def get_commentless_followers(self, top_commenters, followers):
        commentless_followers = {}
        for userID in followers:
            if userID in top_commenters:
                continue
            commentless_followers[userID] = followers[userID]
        return commentless_followers    

    # predict followers who never liked AND never commented
    def get_ghostfollowers(self,likeless_followers, commentless_followers):
        merge = likeless_followers.keys() & commentless_followers.keys()
        ghostfollowers = {}
        for userID in merge:
            ghostfollowers[userID] = likeless_followers[userID]
        return ghostfollowers

    # predict users who don't follow but either commented or liked    
    def get_shy_fans(self, top_likers, top_commenters, followers):
        shyfans = {}

        for userID in top_likers:  
            if userID not in followers:
                shyfans[userID] = top_likers[userID]    

        for userID in top_commenters:
            if userID not in followers:
                shyfans[userID] = top_commenters[userID]      
                
        return shyfans           

           
    def calc_efficiency(self):
        comments = {}
        liker = {}
        tags = {}
        counter = 0
        
        for userID in self.all_follows:
            origin = self.all_follows[userID]['origin']
            origin = origin.split()
            if userID in self.followers:
                is_following = 1
            else:
                is_following = 0
            

            if origin[0] == 'C':
                if origin[1] not in comments:                   
                    comments[origin[1]] = [is_following,1]
                else:
                    comments[origin[1]][0] += is_following
                    comments[origin[1]][1] += 1
                    
            elif origin[0] == 'L':
                if origin[1] not in liker:                   
                    liker[origin[1]] = [is_following,1]
                else:
                    liker[origin[1]][0] += is_following
                    liker[origin[1]][1] += 1
                
            elif origin[0] == '#':
                if origin[1] not in tags:                   
                    tags[origin[1]] = [is_following,1]
                else:
                    tags[origin[1]][0] += is_following
                    tags[origin[1]][1] += 1
            
            else:
                continue
                                          
        temp=[]
        for username in comments:
            temp.append([username,comments[username][0],comments[username][1],comments[username][0]/comments[username][1]] )                       
        self.stats['commenter'] = temp        
        
        temp=[]
        for username in liker:
            temp.append([username,liker[username][0],liker[username][1],liker[username][0]/liker[username][1]] )                       
        self.stats['liker'] = temp
        
        temp=[]
        for tag in tags:
            temp.append([ tag,tags[tag][0],tags[tag][1],tags[tag][0]/tags[tag][1] ] )                       
        self.stats['tags'] = temp
        
        
    def calc_efficiency_user(self):
        hashtag = {}
        liker = {}
        commenter = {}
        counter = 0
        
        for userID in self.all_follows:
            origin = self.all_follows[userID]['origin']
            origin = origin.split()
            if userID in self.followers:
                is_following = 1
            else:
                is_following = 0
            

            if origin[0] == 'C':
                if origin[1] not in comments:                   
                    comments[origin[1]] = [is_following,1]
                else:
                    comments[origin[1]][0] += is_following
                    comments[origin[1]][1] += 1
                    
            elif origin[0] == 'L':
                if origin[1] not in liker:                   
                    liker[origin[1]] = [is_following,1]
                else:
                    liker[origin[1]][0] += is_following
                    liker[origin[1]][1] += 1
                
            elif origin[0] == '#':
                if origin[1] not in tags:                   
                    tags[origin[1]] = [is_following,1]
                else:
                    tags[origin[1]][0] += is_following
                    tags[origin[1]][1] += 1
            
            else:
                continue
                                          
        temp=[]
        for username in comments:
            temp.append([username,comments[username][0],comments[username][1],comments[username][0]/comments[username][1]] )                       
        self.stats['commenter'] = temp        
        
        temp=[]
        for username in liker:
            temp.append([username,liker[username][0],liker[username][1],liker[username][0]/liker[username][1]] )                       
        self.stats['liker'] = temp
        
        temp=[]
        for tag in tags:
            temp.append([ tag,tags[tag][0],tags[tag][1],tags[tag][0]/tags[tag][1] ] )                       
        self.stats['tags'] = temp        
        
    
    def calc_efficiency_timeshift(self, all_follows): 
        res = 500
        timeshift = np.zeros( len(all_follows) )
        total = 0
        
        for userID in all_follows:
            
            origin = all_follows[userID]['origin'][0]
            if not( origin == 'L' or origin == 'C' or origin == '#' or origin == 's'): #only consider users from bot following activity
                continue            
            
            if userID in self.followers:
                if total-res <= 0 or total+res > len(all_follows):
                    continue
                for i in range(total-res, total+res):
                    timeshift[i] += 1
            total +=1
            
        return timeshift    
    
        
    def daily_stats(self):
        follows = self.squser.fetch_follows()        
        daily_follows = 0
        
        now = datetime.now()
        
        for user in follows:   
            if follows[user]['datefollow'] == None:
                continue
            if (now - timedelta(1) ) < follows[user]['datefollow']:  # Erstversand
                daily_follows += 1
        
        daily_likes = 0
        for media in self.likes:   
            if (now - timedelta(1) ) < self.likes[media]['date']:  # Erstversand
                daily_likes += 1                      
                
        self.API.set_daily_stats(daily_likes, daily_follows)
                
        Log("\nActivity in the last 24 hours:")        
        Log("    Followings: " + str(daily_follows)  )      
        Log("    Likes:      " + str(daily_likes) )
               

    def export_statistics(self, followings, all_follows, username_target):   
            now = datetime.now()
            here = os.path.dirname(os.path.realpath(__file__)) 
            subdir = os.path.dirname(here)
            filename = os.path.join(subdir, 'Stats', username_target, 'Stats_' + str(now.year) + '-' + str(now.month) + '-' + str(now.day) + '.xlsx')                
            workbook = xlsxwriter.Workbook(filename)
            
            bold = workbook.add_format({'bold': True})
            format = workbook.add_format()
            format.set_font_size(12)
            bold.set_font_size(12)       
            
            #1. Export Efficiency                 
            for module in self.stats:
                row = 0
                global_follows = 0           
                global_total_follows = 0   
                
                worksheet = workbook.add_worksheet('Efficiency_' + module)  
                worksheet.write(row, 0, 'username', bold)                
                worksheet.write(row, 1, '# Followers gained', bold)      
                worksheet.write(row, 2, '# Total engaged', bold)  
                worksheet.write(row, 3, 'Efficiency', bold)     
                             
                for item in self.stats[module]:   
                    username_or_tag = item[0]               
                    follows = item[1]
                    total_follows = item[2]
                    efficiency = item[3] 
                    
                    global_follows += follows
                    global_total_follows += total_follows
                                                  
                    row += 1 
                    worksheet.write(row, 0, username_or_tag,format)
                    worksheet.write(row, 1, follows,format)
                    worksheet.write(row, 2, total_follows,format)
                    worksheet.write(row, 3, round(efficiency,3),format)  
                    self.squser.update_stats(username_or_tag, module, follows, total_follows, efficiency)                    
                row += 2
                
                worksheet.write(row, 0, 'Total',bold)
                worksheet.write(row, 1, global_follows ,bold)
                worksheet.write(row, 2, global_total_follows ,bold)
                try:
                    efficiency = global_follows / global_total_follows
                except Exception:   
                    efficiency = 0 ### To do: optimize in case Lineless is not active yet random number in case no follows have been counted yet
                self.global_efficiency[module] = efficiency
                worksheet.write(row, 3, round(efficiency,3) ,bold)
                Log("Global efficiency " + module + ":" + str( round(efficiency,3) ) )
                worksheet.set_column('A:D', 15)
             
            
            # 2. Export Engagement Top_likers
            worksheet = workbook.add_worksheet('Top Likers')          
            for row, userID in enumerate(self.top_likers):
                # set title
                worksheet.write(0, 0, 'username',bold)
                worksheet.write(0, 1, 'userID',bold)
                worksheet.write(0, 2, 'Count',bold)
                worksheet.write(0, 3, 'First Post',bold) 
                worksheet.write(0, 4, 'Last Post',bold) 
                worksheet.write(0, 5, 'Private',bold) 
                
                # Inserting users
                worksheet.write(row+1, 1, userID,format)
                worksheet.write(row+1, 0, self.top_likers[userID]['username'],format)             
                worksheet.write(row+1, 2, self.top_likers[userID]['count'],format) 
                worksheet.write(row+1, 3, self.top_likers[userID]['first_post'],format)             
                worksheet.write(row+1, 4, self.top_likers[userID]['last_post'],format)            
                worksheet.write(row+1, 5, self.top_likers[userID]['is_private'],format) 
        
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 20)

            # 3. Export Engagement Top Commenters
            worksheet = workbook.add_worksheet('Top Commenters')          
            for row, userID in enumerate(self.top_commenters):
                # set title
                worksheet.write(0, 0, 'username',bold)
                worksheet.write(0, 1, 'userID',bold)
                worksheet.write(0, 2, 'Count',bold)
                worksheet.write(0, 3, 'First Post',bold) 
                worksheet.write(0, 4, 'Last Post',bold) 
                worksheet.write(0, 5, 'Private',bold) 
                
                # Inserting users
                worksheet.write(row+1, 1, userID,format)
                worksheet.write(row+1, 0, self.top_commenters[userID]['username'],format)             
                worksheet.write(row+1, 2, self.top_commenters[userID]['count'],format) 
                worksheet.write(row+1, 3, self.top_commenters[userID]['first_post'],format)             
                worksheet.write(row+1, 4, self.top_commenters[userID]['last_post'],format)            
                worksheet.write(row+1, 5, self.top_commenters[userID]['is_private'],format) 
        
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 20)                
                
            # 4. Export Shy fans: To do:  That's not really necessary. or is it?
            worksheet = workbook.add_worksheet('Shy Fans')          
            for row, userID in enumerate(self.shy_fans):
                # set title
                worksheet.write(0, 0, 'username',bold)
                worksheet.write(0, 1, 'userID',bold)
                worksheet.write(0, 2, 'Count',bold)
                worksheet.write(0, 3, 'First Post',bold) 
                worksheet.write(0, 4, 'Last Post',bold) 
                worksheet.write(0, 5, 'Private',bold) 
                
                # Inserting users
                worksheet.write(row+1, 1, userID,format)
                worksheet.write(row+1, 0, self.shy_fans[userID]['username'],format)             
                worksheet.write(row+1, 2, self.shy_fans[userID]['count'],format) 
                worksheet.write(row+1, 3, self.shy_fans[userID]['first_post'],format)             
                worksheet.write(row+1, 4, self.shy_fans[userID]['last_post'],format)            
                worksheet.write(row+1, 5, self.shy_fans[userID]['is_private'],format) 
        
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 20)                

            # 5. Export Ghost followers: To do:  That's not really necessary. or is it?
            worksheet = workbook.add_worksheet('Ghost Followers')          
            for row, userID in enumerate(self.ghost_followers):
                # set title
                worksheet.write(0, 0, 'username',bold)
                worksheet.write(0, 1, 'userID',bold)
                
                # Inserting users
                worksheet.write(row+1, 1, userID,format)        
                worksheet.write(row+1, 0, self.ghost_followers[userID],format)       
                
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 20)    
                
                
            # 6. Export reciprocals, non_reciprocals, fans 
            worksheet = workbook.add_worksheet('Followings')         
            worksheet.write(0, 0, 'UserID',bold)       
            for row, userID in enumerate(followings):
                worksheet.write(row+1, 0, userID,format)
            worksheet.set_column('A:A', 30)
            
            # 7. Timeshift
            timeshift = self.calc_efficiency_timeshift(all_follows)
            worksheet = workbook.add_worksheet('Timeshift')  
            
            for row,shift in enumerate(timeshift):
#                if shift == 0: What kind of bullshit is this
#                    break
                worksheet.write(row+1, 0, shift,format) 
                worksheet.write(row+1, 1, shift/1000,format)                
                       
            workbook.close()   
           
                    

# Delete tthe following:

#sqlogin = Session_login('pixelline')
#squser = Session_user('pixelline')               
#
#all_follows = squser.fetch_follows() #get all users ever followed
#all_likes = squser.fetch_likes()
#        
#
#stats = Statistics('pixelline', squser, all_follows, all_likes, [])     