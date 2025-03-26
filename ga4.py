import pycountry
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import json
from urllib.parse import urlencode
from datetime import datetime, timedelta
import pytz
from geopy.geocoders import Nominatim

def GA4_1(question: str):
    match = re.search(
        r'What is the total number of ducks across players on page number (\d+)', question)
    page_number = match.group(1)
    url = "https://stats.espncricinfo.com/stats/engine/stats/index.html?class=2;page=" + page_number + ";template=results;type=batting"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table", {"class": "engineTable"})
    stats_table = None
    for table in tables:
        if table.find("th", string="Player"):
            stats_table = table
            break
    if not stats_table:
        print("Could not find the batting stats table on the page.")
    headers = [th.get_text(strip=True)for th in stats_table.find_all("th")]
    # print(headers)
    rows=stats_table.find_all("tr",{"class":"data1"})
    sum_ducks = 0
    for row in rows:
        cells=row.find_all("td")
        if len(cells)>12:
            duck_count = cells[12].get_text(strip=True)
            if duck_count.isdigit():  # Check if it's a number
                sum_ducks += int(duck_count)
    # print(sum_ducks)
    return sum_ducks

# question = "What is the total number of ducks across players on page number 6"
# print(GA4_1(question))


def GA4_2(question):
    match = re.search(
        r'Filter all titles with a rating between (\d+) and (\d+).', question)
    min_rating, max_rating = match.group(1), match.group(2)
    url = "https://www.imdb.com/search/title/?user_rating=" + \
        min_rating + "," + max_rating + ""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return json.dumps({"error": "Failed to fetch data from IMDb"}, indent=2)

    soup = BeautifulSoup(response.text, "html.parser")
    movies = []
    movie_items = soup.select(".ipc-metadata-list-summary-item")
    items=movie_items[:25]
    for item in items:
        link = item.select_one(".ipc-title-link-wrapper")
        movie_id = re.search(
            r"(tt\d+)", link["href"]).group(1) if link and link.get("href") else None

        # Extract title
        title_elem = item.select_one(".ipc-title__text")
        title = title_elem.text.strip() if title_elem else None

        year_elem = item.select_one(".dli-title-metadata-item")
        year = year_elem.text.strip() if year_elem else None

        rating_elem = item.select_one(".ipc-rating-star--rating")
        rating = rating_elem.text.strip() if rating_elem else None

        movies.append({
            "id": movie_id,
            "title": title,
            "year": year,
            "rating": rating
        })

    return movies


# # Example usage
# question = """Your Task
# Source: Utilize IMDb's advanced web search at https: // www.imdb.com/search/title / to access movie data.
# Filter: Filter all titles with a rating between 3 and 6.
# Format: For up to the first 25 titles, extract the necessary details: ID, title, year, and rating. The ID of the movie is the part of the URL after tt in the href attribute. For example, tt10078772. Organize the data into a JSON structure as follows:

# [
#     {"id": "tt1234567", "title": "Movie 1", "year": "2021", "rating": "5.8"},
#     {"id": "tt7654321", "title": "Movie 2", "year": "2019", "rating": "6.2"},
#     // ... more titles
# ]
# Submit: Submit the JSON data in the text box below.
# Impact
# By completing this assignment, you'll simulate a key component of a streaming service's content acquisition strategy. Your work will enable StreamFlix to make informed decisions about which titles to license, ensuring that their catalog remains both diverse and aligned with subscriber preferences. This, in turn, contributes to improved customer satisfaction and retention, driving the company's growth and success in a competitive market.

# What is the JSON data?"""
# print(GA4_2(question))

def GA4_4(question):
    match = re.search(r"What is the JSON weather forecast description for (\w+)?", question)
    required_city = match.group(1)
    print(required_city)
    # required_city = "Karachi"
    location_url = 'https://locator-service.api.bbci.co.uk/locations?' + urlencode({
    'api_key': 'AGbFAKx58hyjQScCXIYrxuEwJh2W2cmv',
    's': required_city,
    'stack': 'aws',
    'locale': 'en',
    'filter': 'international',
    'place-types': 'settlement,airport,district',
    'order': 'importance',
    'a': 'true',
    'format': 'json'
    })
    result = requests.get(location_url).json()
    url= 'https://www.bbc.com/weather/'+result['response']['results']['results'][0]['id']
    time_zone=result['response']['results']['results'][0]['timezone']
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    daily_summary = soup.find('div', attrs={'class': 'wr-day-summary'})
    daily_summary_list = re.findall('[a-zA-Z][^A-Z]*', daily_summary.text)
    daily_high_values = soup.find_all(
        'span', attrs={'class': 'wr-day-temperature__high-value'})
    daily_low_values = soup.find_all(
        'span', attrs={'class': 'wr-day-temperature__low-value'})
    # local_time = datetime.today()
    local_time = datetime.now(pytz.timezone(time_zone))-timedelta(days=1)
    datelist = pd.date_range(local_time, periods=len(daily_high_values)+1).tolist()
    datelist = [datelist[i].date().strftime('%Y-%m-%d')
                for i in range(len(datelist))]
    zipped_1 = zip(datelist, daily_summary_list)
    df_1 = pd.DataFrame(list(zipped_1), columns=['Date', 'Summary'])
    json_data = df_1.set_index('Date')['Summary'].to_json()
    # print(json_data)
    return json_data

# question = "What is the JSON weather forecast description for Karachi?"
# print(GA4_4(question))


def get_country_code(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        # Returns the ISO 3166-1 Alpha-2 code (e.g., "VN" for Vietnam)
        return country.alpha_2
    except LookupError:
        return None  # Returns None if the country name is not found

def GA4_5(question):
    match1 = re.search(
        r"What is the minimum latitude of the bounding box of the city ([A-Za-z\s]+) in", question)
    match2 = re.search(
        r"the country ([A-Za-z\s]+) on the Nominatim API", question)
    if not match1 or not match2:
        return "Invalid question format"
    city = match1.group(1).strip()
    country = match2.group(1).strip()
    locator = Nominatim(user_agent="myGeocoder")
    country_code = get_country_code(country)
    location = locator.geocode(city, country_codes=country_code)
    # print(location.raw, location.point, location.longitude, location.latitude, location.altitude, location.address) 
    result=location.raw["boundingbox"][0]
    # print(result)
    return result


# q = "What is the minimum latitude of the bounding box of the city Ho Chi Minh City in the country Vietnam on the Nominatim API? Value of the minimum latitude"
# print(GA4_5(q))
