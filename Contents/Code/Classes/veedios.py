"""veedios.py: Used to communicate with the Brilaps veedios.com web service."""

#__author__ = "Brilaps, LLC"
#__email__ = "code@brilaps.com"
#__copyright__ = "Copyright 2011, Brilaps, LLC"

import urllib
from Code.Classes.uuid import uuid1
from Code.Classes import appconfig

# PMS plugin framework
from PMS import *
from PMS.Objects import *

class Fetcher:

    def __init__(self):        
        self.app_base_url = "http://apps.veedios.com/app/"
        self.categories = self.fetch_categories()
        self.singleLevelDefaultCategoryTitle = "Videos"
        self.anonymous_identifier = self.get_anonymous_identifier()      
        
    def get_anonymous_identifier(self):
        if Data.Exists("anonynmous_unique_identifier") == True:
            uid = Data.Load("anonynmous_unique_identifier")
        else:
            uid = uuid1().__str__()
            Data.Save("anonynmous_unique_identifier", uid)
        
        return uid
        
    def track(self, url):
        values = {
                    'channel' : appconfig.channel,
                    'identifier' : self.anonymous_identifier,
                    'feedentrykey' :  '', # we will not have in plex (no custom videoitem props)
                    'feedentryurl': url # track/ support still needs to be added for this
                }
        
        #data = urllib.urlencode(values)
        #Behaves similarly to HTTP.Request(), but returns immediately & makes the request asynchronously. 
        rsp = HTTP.PreCache("%strack/" % self.app_base_url, values)
        # we don't need to no anything with the return

    def call_server(self, url):
        resp = JSON.ObjectFromURL(url)
        return resp
    
    def fetch_categories(self):
        resp = self.call_server(self.app_base_url + appconfig.project + "/categories/")
        return resp
        
    def get_category_count(self):
        return len(self.categories["categories"])
        
    def get_feeds_for_category(self, category):
        categoriesJSON = self.categories

        return categoriesJSON["categories"][category]

    def get_feed_keyinfo(self, categoryTitle, feedTitle=None):
        categoriesJSON = self.categories

        if feedTitle == None:
            keys = categoriesJSON["categories"][categoryTitle]["feeds"].keys()
            if len(keys) > 0:
                return (keys[0], categoriesJSON["categories"][categoryTitle]["feeds"][keys[0]]["key"])
            else:
                return ('', '') #Prob will not reach here anyway
        else:
            return (feedTitle, categoriesJSON["categories"][categoryTitle]["feeds"][feedTitle]["key"])

    def fetch_feeditems(self, feedKey, start, pageSize=None):
        #feedKey is None for single category templates
        if feedKey == None:
            feedInfo = self.get_feed_keyinfo(self.singleLevelDefaultCategoryTitle)
            feedKey = feedInfo[1]
                    
        if (pageSize == None):
            pageSize = self.pageSize
            
        try:
            params = urllib.urlencode({'key': feedKey, 'start': str(start), 'pagesize': str(pageSize)})
            resp = self.call_server(self.app_base_url + appconfig.project + "/?%s" % params)

            return resp
        except:
            return False
            
    def fetch_search_results(self, searchString, start, pageSize=None):
        if (pageSize == None):
            pageSize = self.pageSize

        try:
            params = urllib.urlencode({'s': searchString, 'start': str(start), 'pagesize': str(pageSize)})
            resp = self.call_server(self.app_base_url + appconfig.project + "/search/?%s" % params)

            return resp
        except:
            return False
            
    def fetch_tags(self):
        resp = self.call_server(self.app_base_url + appconfig.project + "/tags/")
        return resp["tags"]