import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
from deep_translator import GoogleTranslator
from utils import get_final_url, encode_special_characters, convert_time_to_datetime

region_code= '&gl=US&ceid=US:en'

def ScrapData(topic="technology", news_medium="", domain="https://news.google.com/", count=10, region=region_code, isenglish=True, isdefault=False):
    """Main web scraping function wrt. selected category and filters"""
    if isdefault:
        query = news_medium
    else:
        query = news_medium + " " + topic
    query_encoded = encode_special_characters(query)
    url = domain + "search?q=" + query_encoded + region

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    articles = soup.find_all('article')[:count]
    links = [article.find('a')['href'].replace("./", domain) for article in articles]

    mediums, thumbnails = [], []

    for article in articles:
        images = article.find_all('img')
        if len(images) > 1:
            medium, thumbnail = images[0]['src'], images[1]['src']
        else:
            medium = thumbnail = images[0]['src']

        mediums.append(medium)
        initial_link = domain + thumbnail.lstrip("./")
        thumbnails.append(get_final_url(initial_link))

    news_text = [article.get_text(separator='\n') for article in articles]
    news_text_split = [text.split('\n') for text in news_text]

    news_df = pd.DataFrame({
        'Title': [text[2] for text in news_text_split],
        'Source': [text[0] for text in news_text_split],
        'Time': [text[3] if len(text) > 3 else '' for text in news_text_split],
        'Author': [text[4].split('By ')[-1] if len(text) > 4 else '' for text in news_text_split],
        'Link': links,
        'Medium': mediums,
        'Thumbnail': thumbnails
    })

    if not isenglish:
        translator = GoogleTranslator(source='auto', target='en')
        news_df['Time'] = news_df['Time'].apply(lambda x: translator.translate(x))

    news_df['datetime'] = news_df['Time'].apply(convert_time_to_datetime)
    news_df_sorted = news_df.sort_values(by='datetime', ascending=False).reset_index(drop=True)

    return news_df_sorted