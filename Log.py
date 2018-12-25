# -*- coding: utf-8 -*-
"""
Created on Sun Mar 18 15:15:53 2018

@author: pixelline
To do: recognize dic and save them
"""
import os
from datetime import datetime
   
class Log(object):
    
    ### Initate with a string and if availbe with list or dic
    def __init__(self,string, container = None):  
        here = os.path.dirname(os.path.realpath(__file__)) 
        subdir = os.path.dirname(here)
        filename = os.path.join(subdir, 'Log', 'Logfile.txt')     
        errormessage = self.write_container(container)        
        self.log(string + errormessage, filename)

         
    def log(self, string, filename):
        print(string)
        
        now = datetime.now()
        time_stemp = str(now.day) + '.' + str(now.month) + '.' + str(now.year) + ' ' +str( now.hour) + ':' + str(now.minute) + ':' + str(now.second) + ' '
        with open(filename, "a") as logfile:
            logfile.write(time_stemp + string + '\n')
        logfile.close()
        
    def write_container(self, container):

        if container == None:
            return ""
        
        string = "\n"
        if type(container) == tuple or type(container) == list:        
            for i in container:
                string += str(i) + '\n'

        elif type(container) == dict:
            for i in container:
                string += container[i] + "  " + i + '\n'
        else:
            string = "Error message is either dict nor list"
        
        return string
        
#Log()
        