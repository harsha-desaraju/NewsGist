## Contains the utility functions for post processing the text from the news article.

import os
import json
import nltk
import torch
import subprocess
import numpy as np
from textwrap import TextWrapper
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import word_tokenize
from transformers import (
    pipeline, 
    AutoTokenizer, 
    AutoModelForSequenceClassification
)
from scrape import ( 
    fetchData, 
    getNewsFromStatePage, 
    getTextFromArticle
)


def _summarizer(texts):
    """
        A model for summarization.
    """

    device = 0 if torch.cuda.is_available() else -1

    tokenizer_kwargs = {'truncation': True}

    summarizer = pipeline(
        "summarization", 
        model = "sshleifer/distilbart-cnn-12-6",
        device = device
    )
    return summarizer(texts, **tokenizer_kwargs)





def newsSummarizer(news):
    """
        Given a dictionary of headline as key and
        article as value, it returns a dictionary
        with headline as key and summary as value
    """

    news = list(news.items())
    news_articles = [tup[1] for tup in news]
    summary_results = _summarizer(news_articles)
    news_summary = {news[i][0]:summary_results[i]['summary_text'] for i in range(len(news))}

    return news_summary




def _classifier(news_summary):

    ## ------- To be replaced with actual model later -------

    device = 0 if torch.cuda.is_available() else -1

    categories = ['politics', 'sports', 'finance', 'business', 'entertainment', 'incident', 'technology', 'other']

    tokenizer = AutoTokenizer.from_pretrained("AyoubChLin/DistilBart_cnn_zeroShot")
    model = AutoModelForSequenceClassification.from_pretrained("AyoubChLin/DistilBart_cnn_zeroShot")
    classifier = pipeline(
        "zero-shot-classification",
        model=model,
        tokenizer=tokenizer,
        device = device
    )
    return classifier(news_summary, candidate_labels=categories)




def newsCategorizer(news):
  """
    Takes a dictionary of headline and news
    summary and returns a dictionary of headline
    and the category it belongs to.
  """

  news = list(news.items())
  news_summary = [tup[1] for tup in news]
  category_results = _classifier(news_summary)
  news_category = {news[i][0]:category_results[i]['labels'][0] for i in range(len(news))}

  return news_category

    



def formatOutput(news_summary):
    """
        Returns the formatted ouput
    """
    output_str = ""
    for headline in news_summary:
        output_str += headline
        output_str += '\n'
        output_str += TextWrapper(width=40).fill(news_summary[headline])
        output_str += '\n\n'

    return output_str
        



def extractTagsFromQuery(query):
    """
        Returns the location tag and category tag
        from the given query
    """
    query = query.lower()

    locations = ['maharashtra', 'delhi', 'karnataka', 'tamil-nadu', 'telangana', 
                 'uttar-pradesh', 'west-bengal', 'gujarat', 'madhya-pradesh', 'bihar', 
                 'chandigarh', 'rajasthan', 'arunachal-pradesh', 'andhra-pradesh', 
                 'assam', 'chhattisgarh', 'goa', 'haryana', 'himachal-pradesh', 
                 'jammu-kashmir', 'jharkhand', 'kerala', 'manipur', 'meghalaya', 
                 'mizoram', 'nagaland', 'odisha', 'punjab', 'sikkim', 'tripura', 
                 'uttarakhand', 'andaman-nicobar-islands', 'dadra-nagar-haveli', 
                 'daman-diu', 'lakshadweep', 'india']
    
    categories = ['politics', 'sports', 'finance', 'business', 'entertainment', 'incident', 'technology', 'other']

    # Get the location
    location = None
    for loc in locations:
        if loc.split('-')[0] in query:
            location = loc

    # Get the category tag
    stemmer = PorterStemmer()
    stemmed_categories = [stemmer.stem(word) for word in categories]
    stemmed_query = [stemmer.stem(word) for word in word_tokenize(query)]

    category = None
    for i, cat in enumerate(stemmed_categories):
        if cat in stemmed_query:
            category = categories[i]

    return location, category

    


def getNews(query):
    """
        Takes the query as input and returns 
        that type of news from that locality.
    """

    location, category = extractTagsFromQuery(query)

    ## ------- Currently supported only for state -------
    ## ------- Also need to add combinations with category -------

    url = f"https://timesofindia.indiatimes.com/india/{location}"

    html_doc = fetchData(url, article=False)

    top_news, all_news = getNewsFromStatePage(html_doc)


    ## If cateogory is not specified, give top news
    if category is None:
        news = top_news
    ## Else give all news to be filtered by category
    else:
        news = all_news

    # Get headline article dictionary
    news = {key: getTextFromArticle(fetchData(news[key], True)) for key in news}
    news_summary = newsSummarizer(news)

    if category is None:
        return formatOutput(news_summary)
    else:
        categories = newsCategorizer(news_summary)
        output = {}
        for headline in news_summary:
            if categories[headline] == category:
                output[headline] = news_summary[headline]
        return formatOutput(output)


def init():
    cwd = os.getcwd()

    # Create a directory for storing html files
    if not 'html_files' in os.listdir(cwd):
        subprocess.run(["mkdir", "html_files"])

    # Create a json file as cache file
    if not 'cache.json' in os.listdir(cwd):
        subprocess.run(["touch", "cache.json"])
    
        with open('cache.json', 'w') as f:
            json.dump({}, f)

    # Download the summarization model
    pipeline("summarization")

    # Download the zero-shot classification model
    AutoTokenizer.from_pretrained("AyoubChLin/DistilBart_cnn_zeroShot")
    AutoModelForSequenceClassification.from_pretrained("AyoubChLin/DistilBart_cnn_zeroShot")

    # Download punkt
    nltk.download('punkt')

    # Print the log message
    print(f"Done with initialization!")



# Run the init function
init()

    
