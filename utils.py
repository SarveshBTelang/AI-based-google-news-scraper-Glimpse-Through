import re
import json
from datetime import datetime, timedelta
from dateutil import parser
import requests

def get(path:str):
    """Loading .json lottie-files"""
    with open(path,"r") as p:
        return json.load(p)

def get_final_url(url):
    """This returns the final resolved URL"""
    response = requests.get(url, allow_redirects=True)
    return response.url

def encode_special_characters(text):
    """Adding special characters to the scraping url"""
    encoded_text = ''
    special_characters = {'&': '%26', '=': '%3D', '+': '%2B', ' ': '%20'}
    for char in text.lower():
        encoded_text += special_characters.get(char, char)
    return encoded_text

def is_valid_date_format(date_str):
    """Updated pattern to include both full and abbreviated month names"""
    pattern = r"^(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}$"
    return bool(re.fullmatch(pattern, date_str))

def remove_ordinal_suffix(date_str):
    """Remove ordinal suffix from day (st, nd, rd, th) in date strings like 'January 1st'."""
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

def add_year_to_month(input_str):
    """Normalizing the datetime format for sorting"""
    current_month = datetime.now().month
    month_str, day_str = input_str.split()
    month_number = datetime.strptime(month_str, "%b").month  # Convert to month number
    current_year = datetime.now().year
    year = current_year if month_number <= current_month else current_year - 1
    return f"{month_str} {day_str}, {year}"

def convert_time_to_datetime(time_str):
    """Analyzing and processing the datetime pattern"""
    now = datetime.now()
    
    if 'hour' in time_str:
        hours_ago = int(time_str.split(' ')[0])
        return now - timedelta(hours=hours_ago)
    elif 'minute' in time_str:
        minutes_ago = int(time_str.split(' ')[0])
        return now - timedelta(minutes=minutes_ago)
    elif 'Yesterday' in time_str:
        return now - timedelta(days=1)
    elif 'Today' in time_str:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif 'days' in time_str:
        days_ago = int(time_str.split(' ')[0])
        return now - timedelta(days=days_ago)
    
    try:
        time_str = remove_ordinal_suffix(time_str)
        if is_valid_date_format(time_str):
            time_str = add_year_to_month(time_str)
        return parser.parse(time_str)
    except:
        return None

def group_sentences(word_list):
    "Grouping sentences for logging"
    result = []
    temp_sentence = []

    for word in word_list:
        if word[:-1].isdigit() and word.endswith('.'):
            if temp_sentence:
                result.append(" ".join(temp_sentence))  
            temp_sentence = [word]  
        else:
            temp_sentence.append(word)

    if temp_sentence:
        result.append(" ".join(temp_sentence))

    return result