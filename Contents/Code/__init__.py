# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

#Plugin
from Code.Classes import veedios
from Code.Classes import appconfig

####################################################################################################

VIDEO_PREFIX = "/video/" + appconfig.project

NAME = appconfig.app_title

#Constants referencing artwork in Contents/Resources/
ART           = 'art-default.jpg'
ICON          = 'icon-default.png'
BROWSE_ICON   = 'browse-icon.png'
SEARCH_ICON   = 'search-icon.png'
NEXT_ICON     = 'next-icon.png'

####################################################################################################

def Start():
    
    #Make this plugin show up in the 'Video' section
    Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, appconfig.app_title, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    #Set some defaults
    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    
    # Set the default cache time
    HTTP.CacheTime = CACHE_1HOUR


#### User created functions below

def VideoMainMenu():

    # Container acting sort of like a folder
    # http://dev.plexapp.com/docs/Objects.html#MediaContainer
    dir = MediaContainer(viewGroup="InfoList")
    
    # Test Categories to determine if this is a single or multi-level template
    fetcher = veedios.Fetcher()
    catCount = fetcher.get_category_count()

    # Add directory items
    # http://dev.plexapp.com/docs/Objects.html#DirectoryItem
    # http://dev.plexapp.com/docs/Objects.html#function-objects
    if catCount == 1:
        #Single level template.  Jump straight to the videos.
        dir.Append(
            Function(
                DirectoryItem(
                    VideoList,
                    L('VideoListTitle2'),
                    subtitle=appconfig.app_subtitle,
                    summary=appconfig.app_summary,
                    thumb=R(ICON),
                    art=R(ART)
                )
            )
        )
    else:
        #Multi level template.  Start at the category list.
        dir.Append(
            Function(
                DirectoryItem(
                    CategoryList,
                    L('CategoryListTitle'),
                    subtitle=appconfig.app_subtitle,
                    summary=appconfig.app_summary,
                    thumb=R(ICON),
                    art=R(ART)
                )
            )
        )
    
    dir.Append(
        Function(
            DirectoryItem(
                TagList,
                L('TagListTitle'),
                subtitle=L('TagListSubtitle'),
                summary='',
                thumb=R(BROWSE_ICON),
                art=R(ART)
            )
        )
    )
  
    # Search - http://dev.plexapp.com/docs/Objects.html#InputDirectoryItem
    dir.Append(
        Function(
            InputDirectoryItem(
                SearchResults,
                L('SearchTitle'),
                L('SearchInputMessage'),
                L('SearchSummary'),
                thumb=R(SEARCH_ICON),
                art=R(ART)
            )
        )
    )

    return dir
    
def CategoryList(sender):
    fetcher = veedios.Fetcher()
    categories = fetcher.fetch_categories()

    dir = MediaContainer(title2=L('CategoryListTitle2'))     
    for cat in categories['categories']:     
        dir.Append(Function(DirectoryItem(SubcategoryList, title=str(cat).upper(), thumb=R(BROWSE_ICON)), selectedCategory=str(cat)))

    return dir
    
def SubcategoryList(sender, selectedCategory):
    fetcher = veedios.Fetcher()
    category_feeds = fetcher.get_feeds_for_category(selectedCategory)

    dir = MediaContainer(title2=L('CategoryListTitle3'))     
    for feed in category_feeds['feeds']:
        feedKey = category_feeds['feeds'][feed]["key"] 
        dir.Append(Function(DirectoryItem(VideoList, title=str(feed).upper(), thumb=R(BROWSE_ICON)), feedKey=feedKey, start=0, pageSize=10))

    return dir
    
def VideoList(sender, feedKey=None, start=0, pageSize=10):
    fetcher = veedios.Fetcher()
    feedDetails = fetcher.fetch_feeditems(feedKey, start, pageSize)
    dir = FeedEntriesToListitems(L('VideoListTitle2'), feedDetails["entries"], False)
    
    if feedDetails['pagination'] and feedDetails['pagination']['hasmore'] == True:
        dir.Append(Function(DirectoryItem(VideoList, title=L('NextPage'), thumb=R(NEXT_ICON)), feedKey=None, start=feedDetails['pagination']['nextstart'], pageSize=10))

    return dir

def TagList(sender, selectedTag=None, start=0, pageSize=10):
    fetcher = veedios.Fetcher()
    tags = fetcher.fetch_tags()

    dir = MediaContainer(title2=L('TagListTitle2'))     
    for tag in tags:     
        dir.Append(Function(DirectoryItem(SearchResults, title=str(tag['tag']).upper(), thumb=R(BROWSE_ICON)), query=tag['tag'], start=0, pageSize=10))

    return dir

# "search" example - http://dev.plexapp.com/docs/Objects.html#InputDirectoryItem
# query will contain the string that the user entered
def SearchResults(sender, query=None, start=0, pageSize=10):
    fetcher = veedios.Fetcher()
    feedDetails = fetcher.fetch_search_results(query, start, pageSize)
    
    if len(feedDetails['results']['feedentryresults']) > 0:
        dir = FeedEntriesToListitems("Search Results", feedDetails['results']['feedentryresults'], True)
        
        pagination = feedDetails['results']['feedentryresultspagination']
        if pagination and pagination['hasmore'] == True:
            dir.Append(Function(DirectoryItem(SearchResults, title=L('NextPage'), thumb=R(NEXT_ICON)), query=query, start=pagination['nextstart'], pageSize=10))

        return dir
    else:
        return MessageContainer(L('SearchErrorTitle'), "\n" + L('SearchErrorMessage') + ' ' + query)

def FeedEntriesToListitems(pageTitle, feedEntries, isSearch):
    dir = MediaContainer(title2=pageTitle)

    for entry in feedEntries:
        if isSearch == False:
            entryExtras = entry["extras"]
        else:
            entryJSON = JSON.ObjectFromString(entry["feedentry"])
            entryExtras = entryJSON["extras"]  

        if 'title' in entryExtras:
            episode_title = entryExtras['title'].strip()
        else:
            episode_title = None

        if 'summary' in entryExtras:
            episode_summary = entryExtras['summary'].strip()
        else:
            episode_summary = None

        if 'duration' in entryExtras:
            episode_duration = entryExtras['duration']
        else:
            episode_duration = None

        if 'thumbnail' in entryExtras:
            episode_thumbnail = entryExtras['thumbnail']
        else:
            episode_thumbnail = None
        
        # Track down the right media path for this platform
        if appconfig.video_type == 'media_path':
            #This app uses the old format
            if 'media_path' in entryExtras:
                episode_media_path = entryExtras['media_path']
            else:
                episode_media_path = None
        else:
            if 'media_ext' in entryExtras:
                mediaExtJSON = JSON.ObjectFromString(entryExtras['media_ext'])
                #Grab the url for the media type of interest
                for obj in mediaExtJSON:
                    if obj['type'] == appconfig.video_type:
                        episode_media_path = obj['url'];
                        break;
            else:
                episode_media_path = None

        if 'updated' in entryExtras:
            episode_date = Datetime.ParseDate(entryExtras['updated']).strftime('%a %b %d, %Y')
        else:
            episode_date = None

        dir.Append(Function(VideoItem(PlayVideo, title=episode_title, subtitle=episode_date, summary=episode_summary, duration=episode_duration, thumb=episode_thumbnail, art=episode_thumbnail), url=episode_media_path))
    
    return dir

def PlayVideo(sender, url):
    fetcher = veedios.Fetcher()
    fetcher.track(url)
    
    return Redirect(url)