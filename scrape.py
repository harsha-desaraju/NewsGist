## Contains all the needs functions for scraping a webpage and extracting
## the text from the webpage. There are specific functions for specific
## type of pages.


import json
import time
import requests
from bs4 import BeautifulSoup




def fetchData(url, article):
    '''
        Gets the data from the url. If the file is 
        already downloaded, it will see if its an
        article. If its not an article and the 
        file has been downloaded more than an hour 
        ago, it will download again.
    '''
    base_url = "https://timesofindia.indiatimes.com/"
    if not base_url in url:
        url = base_url+url


    # Read the cache file
    with open("cache.json", "r") as f:
        cache = json.load(f)

    download = False
    # Check if the file is in the cache
    if url in cache:
        # See if its an article 
        if not cache[url]['article']:
            # Check the time it was downloaded
            # if time exceeds 1 hour download again
            delta = time.time() - int(cache[url]['time'])
            hours = delta/3600
            if hours >= 1:
                download = True
    else:
        download = True

    file_name = url[36:]
    file_name = file_name.replace('/','_')
    
    if download:
        r = requests.get(url)
        with open(f"html_files/{file_name}.html", 'w', encoding='utf-8') as f:
            f.write(r.text)
        html_doc = r.text

        cache[url] = {
            "article": article,
            "time": time.time()
        }

        with open("cache.json",'w') as f:
            json.dump(cache, f)


    else:
        with open(f"html_files/{file_name}.html", 'r', encoding='utf-8') as f:
            html_doc = f.read()

    return html_doc





def getNewsFromIndiaPage(html_doc):
    url = "https://timesofindia.indiatimes.com/india"

    soup = BeautifulSoup(html_doc, 'html.parser')
    lst = soup.select("div.iN5CR")

    headline_link = {}

    for s in lst:
        link = s.find_all("a")[0].get("href")
        headline = s.select('div.WavNE')[0].get_text()
        # filter for the /india news only
        if url in link:   
            headline_link[headline] = link
    
    return headline_link




def getNewsFromStatePage(html_doc):
    '''
        Given the html text of the web page of a state, it
        returns two dictionaries. Each dictionary has headline
        as key and it's link as value. The first dictionary is
        the top news and the second one is for all the news.
    '''

    soup = BeautifulSoup(html_doc, 'html.parser')

    # Select all news articles
    # all_top - List of all news and top news
    all_top = soup.find_all("div",  id="c_articlelist_stories_1")

    # Extract the top news
    top_news = {}
    top_news_raw = all_top[1].select('li')
    for news in top_news_raw:
        link = news.select('a')[0].get('href')
        # ------- check which one works the best -------
        # headline = news.select('a')[0].get_text()
        headline = news.select('a')[0].get('title')
        top_news[headline] = link


    # Extract all the news
    all_news = {}
    all_news_raw = json.loads(all_top[0].string, strict=False)
    all_news_raw = all_news_raw["itemListElement"]
    for news in all_news_raw:
        link = news['url']
        headline = news['name']
        all_news[headline] = link

    return top_news, all_news





def getTextFromArticle(html_doc):
    '''
        Takes html text of an article as input and returns the
        text inside the articel as output
    '''

    soup = BeautifulSoup(html_doc, 'html.parser')
    tag = soup.select('script')[-2]
    json_dct = json.loads(tag.contents[0])

    return json_dct['articleBody']