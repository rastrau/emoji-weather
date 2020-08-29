# -*- coding: utf-8 -*-
import os
import requests
import datetime
import pytz
import time
import sys
import codecs
import numpy as np
from twitter import *
import Config



class MeteoMap:
    def __init__(self):
        self.weather = dict()
        self.temperature = dict()
        self.humidity = dict()
        self.clouds = dict()
        self.windspeed = dict()
        self.winddirection = dict()
        self.precipitation_probability = dict()
        self.timestamp = None

    def add_datum(self, index, MeteoDatum):
        self.weather[index] = MeteoDatum.weather
        self.temperature[index] = MeteoDatum.temperature
        self.humidity[index] = MeteoDatum.humidity
        self.clouds[index] = MeteoDatum.clouds
        self.windspeed[index] = MeteoDatum.windspeed
        self.winddirection[index] = MeteoDatum.winddirection
        self.precipitation_probability[index] = MeteoDatum.precipitation_probability
        self.timestamp = MeteoDatum.timestamp

    def set_basemap(self, emojimap):
        emojimap[1] = u"🇫🇷"
        emojimap[12] = u"🇩🇪"
        emojimap[24] = u"🇦🇹"
        emojimap[84] = u"🇮🇹"
        emojimap[10] = u"🔵"
        emojimap[62] = u"🔵"
        return

    def emojify_weather(self):
        for key, w in self.weather.iteritems():
            self.weather[key] = config.emojis.get(w.lower(), u"❔")
        self.set_basemap(self.weather)
        return

    def emojify_temperature(self):
        temperatures = self.temperature.values()
        p20, p40, p60, p80, p100 = quintile(temperatures)

        for key, w in self.temperature.iteritems():
            if w <= p20:
                self.temperature[key] = config.quintiles[1]
            elif w <= p40:
                self.temperature[key] = config.quintiles[2]
            elif w <= p60:
                self.temperature[key] = config.quintiles[3]
            elif w <= p80:
                self.temperature[key] = config.quintiles[4]
            else:
                self.temperature[key] = config.quintiles[5]
        self.set_basemap(self.temperature)
        return round(p20, 1), round(p40, 1), round(p60, 1), round(p80, 1), round(p100, 1)

    def compile_weather_tweet(self, timespan):
        self.emojify_weather()
        weather_tweet = u"%s %s – Wᴇᴀᴛʜᴇʀ Fᴏʀᴇᴄᴀsᴛ\n\n" % (timespan,
                                                          meteomap.timestamp.strftime('%d. %b'))
        for i in range(1,85):
            emoji = self.weather.get(i, u"⬜")
            weather_tweet += emoji
            if i > 0 and i % 12 == 0:
                weather_tweet += u"\n"
        return weather_tweet

    def compile_temperature_tweet(self, timespan):
        temp_p20, temp_p40, temp_p60, temp_p80, temp_p100 = self.emojify_temperature()
        temperature_tweet = u"%s %s – Tᴇᴍᴘ\n\n" % (timespan,
                                                   self.timestamp.strftime('%d. %b'))
        for i in range(1,85):
            emoji = self.temperature.get(i, u"⬜")
            temperature_tweet += emoji
            if i > 0 and i % 12 == 0:
                temperature_tweet += u"\n"
        temperature_tweet += u"\n"
        temperature_tweet += u"°C\n"
        temperature_tweet += u"🟥 %s–%s\n" % (temp_p80, temp_p100)
        temperature_tweet += u"🟧 %s–%s\n" % (temp_p60, temp_p80)
        temperature_tweet += u"🟨 %s–%s\n" % (temp_p40, temp_p60)
        temperature_tweet += u"🟩 %s–%s\n" % (temp_p20, temp_p40)
        temperature_tweet += u"🟦 <%s\n" % temp_p20
        return temperature_tweet



class MeteoDatum:
    def __init__(self, weather, temperature, humidity, clouds, windspeed, winddirection, precipitation_probability, timestamp):
        self.weather = weather
        self.temperature = kelvin_to_celsius(temperature)
        self.humidity = humidity
        self.clouds = clouds
        self.windspeed = windspeed
        self.winddirection = winddirection
        self.precipitation_probability = precipitation_probability
        self.timestamp = get_swiss_datetime(timestamp)



def get_utc_datetime(timestamp):
    timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return pytz.utc.localize(timestamp)

def get_swiss_datetime(timestamp):
    timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    utc_timestamp = pytz.utc.localize(timestamp)
    swiss_timezone = pytz.timezone("Europe/Zurich")
    return utc_timestamp.astimezone(swiss_timezone)

def quintile(data):
    return np.percentile(data, 20), np.percentile(data, 40), np.percentile(data, 60), \
        np.percentile(data, 80), np.percentile(data, 100)

def kelvin_to_celsius(temperature):
    return temperature - 273.15

def find_forecast(data, target_time_local):
    # Find the current date in Swiss timezone
    utc_datetime = pytz.utc.localize(datetime.datetime.utcnow())
    swiss_datetime = utc_datetime.astimezone(pytz.timezone("Europe/Zurich"))
    swiss_date = datetime.datetime.strftime(swiss_datetime, '%Y-%m-%d')

    # Parse today's date and target_time_local as (Swiss) datetime
    # and convert to UTC datetime
    swiss_datetime = datetime.datetime.strptime("%s %s" % (swiss_date, target_time_local), '%Y-%m-%d %H:%M')
    swiss_timezone = pytz.timezone("Europe/Zurich")
    swiss_datetime = swiss_timezone.localize(swiss_datetime)
    target_utc_datetime = swiss_datetime.astimezone(pytz.utc)

    target_index = 0
    min_offset = sys.maxint
    for i, item in enumerate(data["list"]):
        offset = get_utc_datetime(item["dt_txt"]) - target_utc_datetime
        offset = abs(offset.total_seconds() / 3600)
        if offset < min_offset:
            min_offset = offset
            index = i
    return index

def parse_meteodata(json_data, target_time_local):
    index = find_forecast(json_data, target_time_local)
    
    item = json_data["list"][index]
    weather = item["weather"][0]["description"]
    temperature = item["main"]["temp"]
    humidity = item["main"]["humidity"]
    clouds = item["clouds"]["all"]
    windspeed = item["wind"]["speed"]
    winddirection = item["wind"]["deg"]
    precipitation_probability = item["pop"]
    timestamp = item["dt_txt"]
    return MeteoDatum(weather, temperature, humidity, clouds, windspeed, winddirection, precipitation_probability, timestamp)



if __name__ == "__main__":

    testing = False

    config = Config.Config()
<<<<<<< Updated upstream
    
    OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')
    TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
    TWITTER_API_KEY_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
=======
>>>>>>> Stashed changes

    if not testing:    
        OPENWEATHERMAP_API_KEY = os.environ.get('OPEN_WEATHER_API_KEY')
        TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
        TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
        TWITTER_API_KEY_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
        TARGET_TIMES_LOCAL = os.environ.get('TARGET_TIMES_LOCAL')
        TARGET_TIMES_HUMAN = os.environ.get('TARGET_TIMES_HUMAN')
    else:
        OPENWEATHERMAP_API_KEY = "" # redacted
        TARGET_TIMES_LOCAL = "09:00,15:00,20:00"
        TARGET_TIMES_HUMAN = "Morning,Afternoon,Evening"

    URL = "https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid=%s" % OPENWEATHERMAP_API_KEY

    TARGET_TIMES_LOCAL = TARGET_TIMES_LOCAL.split(",")
    TARGET_TIMES_HUMAN = TARGET_TIMES_HUMAN.split(",")
    
    weather_tweets = []
    temperature_tweets = []

    for j in range(0, len(TARGET_TIMES_LOCAL)):
        meteomap = MeteoMap()
        for i in range(1, 85):
            (lat, lon) = config.locations.get(i, (None, None))
            if lat:
                time.sleep(0.2)
                this_url = URL.replace("{lat}", str(lat)).replace("{lon}", str(lon))
                print "Querying %s (%s)..." % (this_url, i)
                response = requests.get(this_url)

                print "Parsing API result for time %s (%s)..." % (TARGET_TIMES_LOCAL[j], TARGET_TIMES_HUMAN[j])            
                meteodatum = parse_meteodata(response.json(), TARGET_TIMES_LOCAL[j])
                meteomap.add_datum(i, meteodatum)
        
        print "\nCompiling weather tweet(s)..."
        weather_tweets.append(meteomap.compile_weather_tweet(TARGET_TIMES_HUMAN[j]))
        print "Compiling temperature tweet(s)..."
        temperature_tweets.append(meteomap.compile_temperature_tweet(TARGET_TIMES_HUMAN[j]))


    if testing:
        with codecs.open("test.txt", "w", "utf8") as f:
            for weather_tweet in weather_tweets:
                f.write(weather_tweet)
                f.write("--------------------------------------------\n")
            for temperature_tweet in temperature_tweets:
                f.write(temperature_tweet)
                f.write("--------------------------------------------\n")                
    else:
        t = Twitter(auth=OAuth(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, 
                            TWITTER_API_KEY, TWITTER_API_KEY_SECRET))
        
        for weather_tweet in weather_tweets:
            tweet = t.statuses.update(status = weather_tweet.encode('utf8'))
        
        for temperature_tweet in temperature_tweets:
            tweet = t.statuses.update(status = temperature_tweet.encode('utf8'))
            
            # tweet = t.statuses.update(status=temperature.encode('utf8'), in_reply_to_status_id = tweet["id_str"])
            # tweet = t.statuses.update(status=winddirection.encode('utf8'), in_reply_to_status_id = tweet["id_str"])

