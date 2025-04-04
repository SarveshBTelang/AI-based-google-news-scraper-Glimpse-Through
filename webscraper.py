import concurrent.futures
import requests
from bs4 import BeautifulSoup
import pandas as pd
from deep_translator import GoogleTranslator
from utils import get_final_url, encode_special_characters, convert_time_to_datetime

region_code = '&gl=US&ceid=US:en'

def ScrapData(topic="technology", news_medium="", domain="https://news.google.com/", count=10, region=region_code, isenglish=True, isdefault=False):
    """Main web scraping function with parallelized tasks"""
    # Prepare the query and URL.
    query = news_medium if isdefault else f"{news_medium} {topic}"
    query_encoded = encode_special_characters(query)
    url = domain + "search?q=" + query_encoded + region

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('article')[:count]

    def process_article(article):
        """Extracts fields from a single article."""
        # Extract and adjust the link.
        a_tag = article.find('a')
        link = a_tag['href'].replace("./", domain) if a_tag else ""
        
        # Extract images.
        images = article.find_all('img')
        if images:
            if len(images) > 1:
                medium_src, thumb_src = images[0]['src'], images[1]['src']
            else:
                medium_src = thumb_src = images[0]['src']
        else:
            medium_src = thumb_src = ""
        
        # Process the thumbnail URL.
        thumbnail = get_final_url(domain + thumb_src.lstrip("./")) if thumb_src else ""
        
        # Extract text parts.
        text_parts = article.get_text(separator='\n').split('\n')
        title = text_parts[2] if len(text_parts) > 2 else ''
        source = text_parts[0] if text_parts else ''
        time_str = text_parts[3] if len(text_parts) > 3 else ''
        author = text_parts[4].split('By ')[-1] if len(text_parts) > 4 else ''
        
        return {
            'Title': title,
            'Source': source,
            'Time': time_str,
            'Author': author,
            'Link': link,
            'Medium': medium_src,
            'Thumbnail': thumbnail
        }

    # Process articles concurrently.
    rows = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_article, article) for article in articles]
        for future in concurrent.futures.as_completed(futures):
            try:
                row = future.result()
                rows.append(row)
            except Exception as e:
                print("Error processing article:", e)

    news_df = pd.DataFrame(rows)

    # If the "Time" column needs translation, process concurrently.
    if not isenglish:
        translator = GoogleTranslator(source='auto', target='en')
        def translate_time(time_str):
            try:
                return translator.translate(time_str)
            except Exception as e:
                # Return the original string if translation fails.
                return time_str
        with concurrent.futures.ThreadPoolExecutor() as translator_executor:
            translated_times = list(translator_executor.map(translate_time, news_df['Time']))
        news_df['Time'] = translated_times

    # Parallelize conversion of the Time column to datetime objects.
    with concurrent.futures.ThreadPoolExecutor() as datetime_executor:
        datetimes = list(datetime_executor.map(convert_time_to_datetime, news_df['Time']))
    news_df['datetime'] = datetimes

    news_df_sorted = news_df.sort_values(by='datetime', ascending=False).reset_index(drop=True)
    return news_df_sorted