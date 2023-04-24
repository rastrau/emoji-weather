# -*- coding: utf-8 -*-
# Python 3.9
# Environment: emoji-weather
import os
import requests
import datetime
import pytz
import time
import math
import codecs
import numpy as np
import Config
from mastodon import Mastodon
from linkedin_api.clients.restli.client import RestliClient
import json


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

    def set_basemap(self, emojimap, lakes = True):
        emojimap[1] = u"🇫🇷"
        emojimap[12] = u"🇩🇪"
        emojimap[24] = u"🇦🇹"
        emojimap[84] = u"🇮🇹"
        if lakes:
            emojimap[10] = u"🔵"
            emojimap[62] = u"🔵"
        return

    def emojify_weather(self):
        for key, w in self.weather.items():
            self.weather[key] = config.emojis.get(w.lower(), u"❔")
        self.set_basemap(self.weather)
        return

    def emojify_temperature(self):
        temperatures = list(self.temperature.values())
        p20, p40, p60, p80, p100 = quintile(temperatures)

        for key, w in self.temperature.items():
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
        self.set_basemap(self.temperature, lakes = False)
        return round(p20, 1), round(p40, 1), round(p60, 1), round(p80, 1), round(p100, 1)
    
    def emojify_winddirection(self):
        for key, d in self.winddirection.items():
            if (d >= 337.5 and d <= 360) or (d >= 0 and d < 22.5):
                self.winddirection[key] = config.winddirections["north"]
            elif d >= 22.5 and d < 67.5:
                self.winddirection[key] = config.winddirections["northeast"]
            elif d >= 67.5 and d < 112.5:
                self.winddirection[key] = config.winddirections["east"]
            elif d >= 112.5 and d < 157.5:
                self.winddirection[key] = config.winddirections["southeast"]
            elif d >= 157.5 and d < 202.5:
                self.winddirection[key] = config.winddirections["south"]
            elif d >= 202.5 and d < 247.5:
                self.winddirection[key] = config.winddirections["southwest"]
            elif d >= 247.5 and d < 292.5:
                self.winddirection[key] = config.winddirections["west"]
            elif d >= 292.5 and d < 337.5:
                self.winddirection[key] = config.winddirections["northwest"]
            else:
                self.winddirection[key] = config.winddirections["none"]
        self.set_basemap(self.winddirection, lakes = False)
        return

    def emojify_windspeed(self):
        windspeed = list(self.windspeed.values())
        p25, p50, p75, p100 = quartile(windspeed)
        
        for key, w in self.windspeed.items():
            if w <= p25:
                self.windspeed[key] = config.quartiles[1]
            elif w <= p50:
                self.windspeed[key] = config.quartiles[2]
            elif w <= p75:
                self.windspeed[key] = config.quartiles[3]
            else:
                self.windspeed[key] = config.quartiles[4]
        self.set_basemap(self.windspeed)
        return round(p25, 1), round(p50, 1), round(p75, 1), round(p100, 1)

    def compile_weather_text(self, timespan):
        self.emojify_weather()
        if timespan.startswith("-"):
            weather_tweet = weather_tweet = u"%s %s – Wᴇᴀᴛʜᴇʀ\n\n" % (meteomap.timestamp.strftime("%d. %b"),
                                                                               timespan[1:])
        else:
            weather_tweet = u"%s %s – Wᴇᴀᴛʜᴇʀ\n\n" % (timespan,
                                                               meteomap.timestamp.strftime("%d. %b"))
        for i in range(1,85):
            emoji = self.weather.get(i, u"▫️")
            weather_tweet += emoji
            if i > 0 and i % 12 == 0:
                weather_tweet += u"\n"
        return weather_tweet

    def compile_temperature_text(self, timespan):
        temp_p20, temp_p40, temp_p60, temp_p80, temp_p100 = self.emojify_temperature()
                
        if timespan.startswith("-"):
            temperature_tweet = u"%s %s – Tᴇᴍᴘ\n\n" % (meteomap.timestamp.strftime("%d. %b"), 
                                                       timespan[1:])
        else:
            temperature_tweet = u"%s %s – Tᴇᴍᴘ\n\n" % (timespan,
                                                       meteomap.timestamp.strftime("%d. %b"))
        for i in range(1,85):
            emoji = self.temperature.get(i, u"▫️")
            temperature_tweet += emoji
            if i > 0 and i % 12 == 0:
                temperature_tweet += u"\n"
        temperature_tweet += u"\n"
        temperature_tweet += u"🟥 %s–%s °C\n" % (temp_p80, temp_p100)
        temperature_tweet += u"🟧 %s–%s\n" % (temp_p60, temp_p80)
        temperature_tweet += u"🟨 %s–%s\n" % (temp_p40, temp_p60)
        temperature_tweet += u"🟩 %s–%s\n" % (temp_p20, temp_p40)
        temperature_tweet += u"🟦 <%s\n" % temp_p20
        
        # Emphasise very cold and very hot temperature situations        
        if temp_p20 < -5:
            temperature_tweet = self._coldify_emoji_temperature(temperature_tweet)
        if temp_p80 > 27:
            temperature_tweet = self._warmify_emoji_temperature(temperature_tweet)
        return temperature_tweet

    def _coldify_emoji_temperature(self, temperature_tweet):
        temperature_tweet = temperature_tweet.replace(u"🟦", u"🥶")
        temperature_tweet = temperature_tweet.replace(u"🟩", u"🟦")
        temperature_tweet = temperature_tweet.replace(u"🟨", u"🟩")
        temperature_tweet = temperature_tweet.replace(u"🟧", u"🟨")
        temperature_tweet = temperature_tweet.replace(u"🟥", u"🟧")
        return temperature_tweet

    def _warmify_emoji_temperature(self, temperature_tweet):
        temperature_tweet = temperature_tweet.replace(u"🟥", u"🥵")
        temperature_tweet = temperature_tweet.replace(u"🟧", u"🟥")
        temperature_tweet = temperature_tweet.replace(u"🟨", u"🟧")
        temperature_tweet = temperature_tweet.replace(u"🟩", u"🟨")
        temperature_tweet = temperature_tweet.replace(u"🟦", u"🟩")
        return temperature_tweet

    def compile_winddirection_text(self, timespan):
        self.emojify_winddirection()
        if timespan.startswith("-"):
            winddirection_tweet = u"%s %s – Wɪɴᴅ Dɪʀᴇᴄᴛɪᴏɴ\n\n" % (meteomap.timestamp.strftime("%d. %b"),
                                                                  timespan[1:])
        else:
            winddirection_tweet = u"%s %s – Wɪɴᴅ Dɪʀᴇᴄᴛɪᴏɴ\n\n" % (timespan,
                                                                  meteomap.timestamp.strftime("%d. %b"))
        for i in range(1,85):
            emoji = self.winddirection.get(i, u"▫️")
            winddirection_tweet += emoji
            if i > 0 and i % 12 == 0:
                winddirection_tweet += u"\n"            
        return winddirection_tweet

    def compile_windspeed_text(self, timespan):
        windspeed_p25, windspeed_p50, windspeed_p75, windspeed_p100 = self.emojify_windspeed()

        if timespan.startswith("-"):
            windspeed_tweet = u"%s %s – Wɪɴᴅ Sᴘᴇᴇᴅ\n\n" % (meteomap.timestamp.strftime("%d. %b"),
                                                          timespan[1:])
        else:
            windspeed_tweet = u"%s %s – Wɪɴᴅ Sᴘᴇᴇᴅ\n\n" % (timespan,
                                                          meteomap.timestamp.strftime("%d. %b"))
        for i in range(1,85):
            emoji = self.windspeed.get(i, u"▫️")
            windspeed_tweet += emoji
            if i > 0 and i % 12 == 0:
                windspeed_tweet += u"\n"
        windspeed_tweet += u"\n"
        windspeed_tweet += u"⬛ %s–%s m/s\n" % (windspeed_p75, windspeed_p100)
        windspeed_tweet += u"◼️ %s–%s\n" % (windspeed_p50, windspeed_p75)
        windspeed_tweet += u"◾ %s–%s\n" % (windspeed_p25, windspeed_p50)
        windspeed_tweet += u"▪️ <%s\n" % windspeed_p25
        return windspeed_tweet

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
    timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    return pytz.utc.localize(timestamp)

def get_swiss_datetime(timestamp):
    timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    utc_timestamp = pytz.utc.localize(timestamp)
    swiss_timezone = pytz.timezone("Europe/Zurich")
    return utc_timestamp.astimezone(swiss_timezone)

def quintile(data):
    return np.percentile(data, 20), np.percentile(data, 40), np.percentile(data, 60), \
        np.percentile(data, 80), np.percentile(data, 100)

def quartile(data):
    return np.percentile(data, 25), np.percentile(data, 50), np.percentile(data, 75), \
        np.percentile(data, 100)

def kelvin_to_celsius(temperature):
    return temperature - 273.15

def find_forecast(data, target_time_local):
    # Find the current date in Swiss timezone
    utc_datetime = pytz.utc.localize(datetime.datetime.utcnow())
    swiss_datetime = utc_datetime.astimezone(pytz.timezone("Europe/Zurich"))
    swiss_date = datetime.datetime.strftime(swiss_datetime, "%Y-%m-%d")

    # Parse today's date and target_time_local as (Swiss) datetime
    # and convert to UTC datetime
    swiss_datetime = datetime.datetime.strptime("%s %s" % (swiss_date, target_time_local), "%Y-%m-%d %H:%M")
    swiss_timezone = pytz.timezone("Europe/Zurich")
    swiss_datetime = swiss_timezone.localize(swiss_datetime)
    target_utc_datetime = swiss_datetime.astimezone(pytz.utc)

    target_index = 0
    min_offset = math.inf
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
    wind_speed = item["wind"]["speed"]
    wind_direction = item["wind"]["deg"]
    precipitation_probability = item["pop"]
    timestamp = item["dt_txt"]
    return MeteoDatum(weather, temperature, humidity, clouds, wind_speed, 
                      wind_direction, precipitation_probability, timestamp)

def switch_light_to_dark_mode(text):
    text = text.replace(u"▫️", u"🔄")
    text = text.replace(u"▪️", u"▫️")
    text = text.replace(u"◾", u"◽")
    text = text.replace(u"◼️", u"◻️")
    text = text.replace(u"⬛", u"⬜")
    text = text.replace(u"🔄", u"▪️")
    return text
    
if __name__ == "__main__":
    LINKEDIN_ACCESS_TOKEN = ""
    LINKEDIN_API_VERSION = "202302"

    restli_client = RestliClient()
    me_response = restli_client.get(resource_path="/me", access_token = LINKEDIN_ACCESS_TOKEN)
    print(f"Successfully fetched profile: {json.dumps(me_response.entity)}")
   

    run_mode = "local testing"

    # run_mode = os.environ.get("RUN_MODE")
    print("Run mode: %s" % run_mode)
    # run_mode can be:
    # - "operational" → for running the bots operationally using GitHub Actions
    # - "remote testing" → for test-running using GitHub Actions and tooting through @meteo_test_45618761@tooting.ch
    # - "local" → for test-running on the local machine (needs 'secrets.txt') and tooting through @meteo_test_45618761@tooting.ch as well as saving the toots to disk
    
    if run_mode == "operational":    
        print("Configuring run mode '%s'" % run_mode)
        TARGET_TIMES_LOCAL = os.environ.get("TARGET_TIMES_LOCAL")
        TARGET_TIMES_HUMAN = os.environ.get("TARGET_TIMES_HUMAN")
        OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY") 
        MASTO_DARK_WEATHER = os.environ.get("MASTO_DARK_WEATHER")
        MASTO_DARK_WIND = os.environ.get("MASTO_DARK_WIND")
        MASTO_LIGHT_WEATHER = os.environ.get("MASTO_LIGHT_WEATHER")
        MASTO_LIGHT_WIND = os.environ.get("MASTO_LIGHT_WIND")
    elif run_mode == "remote testing":
        print("Configuring run mode '%s'" % run_mode)
        TARGET_TIMES_LOCAL = "09:00"
        TARGET_TIMES_HUMAN = "Morning"
        OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY") 
        MASTO_DARK_WEATHER = os.environ.get("MASTO_DARK_WEATHER")
        MASTO_DARK_WIND = os.environ.get("MASTO_DARK_WIND")
        MASTO_LIGHT_WEATHER = os.environ.get("MASTO_LIGHT_WEATHER")
        MASTO_LIGHT_WIND = os.environ.get("MASTO_LIGHT_WIND")
    else:
        print("Configuring run mode '%s'" % run_mode)
        run_mode = "local testing"
        TARGET_TIMES_LOCAL = "20:00" # can be, e.g. "09:00,15:00,20:00"
        TARGET_TIMES_HUMAN = "Evening" # can be, e.g. "Morning,Afternoon,Evening"
        with open("secrets.txt", "r") as in_file:
            parameters = in_file.readlines()
        OPENWEATHERMAP_API_KEY = parameters[0].strip()
        MASTO_DARK_WEATHER = parameters[1].strip()
        MASTO_DARK_WIND = parameters[1].strip()
        MASTO_LIGHT_WEATHER = parameters[1].strip()
        MASTO_LIGHT_WIND = parameters[1].strip()
        
    TARGET_TIMES_LOCAL = TARGET_TIMES_LOCAL.split(",")
    TARGET_TIMES_HUMAN = TARGET_TIMES_HUMAN.split(",")
    
    config = Config.Config()   
    OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid=%s" % OPENWEATHERMAP_API_KEY
    MASTODON_URL = "https://tooting.ch"
    masto_light_weather = Mastodon(api_base_url = MASTODON_URL,
                                   access_token = MASTO_LIGHT_WEATHER)
    masto_dark_weather = Mastodon(api_base_url = MASTODON_URL,
                                  access_token = MASTO_DARK_WEATHER)
    masto_light_wind = Mastodon(api_base_url = MASTODON_URL,
                                access_token = MASTO_LIGHT_WIND)
    masto_dark_wind = Mastodon(api_base_url = MASTODON_URL,
                                  access_token = MASTO_DARK_WIND)

    weather_texts_light = []
    temperature_texts_light = []
    winddirection_texts_light = []
    windspeed_texts_light = []
    weather_texts_dark = []
    temperature_texts_dark = []
    winddirection_texts_dark = []
    windspeed_texts_dark = []

    for j in range(0, len(TARGET_TIMES_LOCAL)):
        meteomap = MeteoMap()
        for i in range(1, 85):
            (lat, lon) = config.locations.get(i, (None, None))
            if lat:
                time.sleep(0.2)
                this_url = OPENWEATHERMAP_URL.replace("{lat}", str(lat)).replace("{lon}", str(lon))
                # print("Querying %s (%s)..." % (this_url, i))
                response = requests.get(this_url)

                # print("Parsing API result for time %s (%s)..." % (TARGET_TIMES_LOCAL[j], TARGET_TIMES_HUMAN[j]))
                meteodatum = parse_meteodata(response.json(), TARGET_TIMES_LOCAL[j])
                meteomap.add_datum(i, meteodatum)
        
        print("\nCompiling weather toot(s)...")
        weather_toot_light = meteomap.compile_weather_text(TARGET_TIMES_HUMAN[j])
        weather_texts_light.append(weather_toot_light)
        weather_texts_dark.append(switch_light_to_dark_mode(weather_toot_light))
        
        print("Compiling temperature toot(s)...")
        temperature_toot_light = meteomap.compile_temperature_text(TARGET_TIMES_HUMAN[j])
        temperature_texts_light.append(temperature_toot_light)
        temperature_texts_dark.append(switch_light_to_dark_mode(temperature_toot_light))
        
        print("Compiling wind-direction toot(s)...")
        winddirection_toot_light = meteomap.compile_winddirection_text(TARGET_TIMES_HUMAN[j])
        winddirection_texts_light.append(winddirection_toot_light)
        winddirection_texts_dark.append(switch_light_to_dark_mode(winddirection_toot_light))
        
        print("Compiling wind-speed toot(s)...")
        windspeed_toot_light = meteomap.compile_windspeed_text(TARGET_TIMES_HUMAN[j])
        windspeed_texts_light.append(windspeed_toot_light)
        windspeed_texts_dark.append(switch_light_to_dark_mode(windspeed_toot_light))

    if run_mode == "local testing":
        
        with codecs.open("toots.txt", "w", "utf8") as f:
            f.write("LIGHT MODE:")
            f.write("--------------------------------------------\n")
            for weather_tweet in weather_texts_light:
                f.write(weather_tweet)
                f.write("--------------------------------------------\n")
            for temperature_tweet in temperature_texts_light:
                f.write(temperature_tweet)
                f.write("--------------------------------------------\n")                
            for winddirection_tweet in winddirection_texts_light:
                f.write(winddirection_tweet)
                f.write("--------------------------------------------\n")                
            for windspeed_tweet in windspeed_texts_light:
                f.write(windspeed_tweet)
                f.write("--------------------------------------------\n")         
            f.write("DARK MODE:")
            f.write("--------------------------------------------\n")
            for weather_tweet in weather_texts_dark:
                f.write(weather_tweet)
                f.write("--------------------------------------------\n")
            for temperature_tweet in temperature_texts_dark:
                f.write(temperature_tweet)
                f.write("--------------------------------------------\n")                
            for winddirection_tweet in winddirection_texts_dark:
                f.write(winddirection_tweet)
                f.write("--------------------------------------------\n")                
            for windspeed_tweet in windspeed_texts_dark:
                f.write(windspeed_tweet)
                f.write("--------------------------------------------\n")         

        posts_create_response = restli_client.create(
            resource_path = "/posts",
            entity={
                "author": f"urn:li:person:{me_response.entity['id']}",
                "lifecycleState": "PUBLISHED",
                "visibility": "PUBLIC",
                "commentary": weather_texts_light[0].encode("utf8"),
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
            },
            version_string = LINKEDIN_API_VERSION,
            access_token = LINKEDIN_ACCESS_TOKEN,
        )

        posts_create_response = restli_client.create(
            resource_path = "/posts",
            entity={
                "author": f"urn:li:person:{me_response.entity['id']}",
                "lifecycleState": "PUBLISHED",
                "visibility": "PUBLIC",
                "commentary": temperature_texts_light[0].encode("utf8"),
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
            },
            version_string = LINKEDIN_API_VERSION,
            access_token = LINKEDIN_ACCESS_TOKEN,
        )

        posts_create_response = restli_client.create(
            resource_path = "/posts",
            entity={
                "author": f"urn:li:person:{me_response.entity['id']}",
                "lifecycleState": "PUBLISHED",
                "visibility": "PUBLIC",
                "commentary": winddirection_texts_light[0].encode("utf8"),
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
            },
            version_string = LINKEDIN_API_VERSION,
            access_token = LINKEDIN_ACCESS_TOKEN,
        )

        posts_create_response = restli_client.create(
            resource_path = "/posts",
            entity={
                "author": f"urn:li:person:{me_response.entity['id']}",
                "lifecycleState": "PUBLISHED",
                "visibility": "PUBLIC",
                "commentary": windspeed_texts_light[0].encode("utf8"),
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
            },
            version_string = LINKEDIN_API_VERSION,
            access_token = LINKEDIN_ACCESS_TOKEN,
        )
                   
    for i in range(0, len(weather_texts_light)):
        print("Tooting weather...")
        
        masto_light_weather.toot(weather_texts_light[i].encode("utf8"))
        time.sleep(5)
        masto_light_weather.toot(temperature_texts_light[i].encode("utf8"))
        time.sleep(5)
        masto_light_wind.toot(winddirection_texts_light[i].encode("utf8")) 
        time.sleep(5)
        masto_light_wind.toot(windspeed_texts_light[i].encode("utf8")) 
        time.sleep(5)
        masto_dark_weather.toot(weather_texts_dark[i].encode("utf8")) 
        time.sleep(5)
        masto_dark_weather.toot(temperature_texts_dark[i].encode("utf8")) 
        time.sleep(5)
        masto_dark_wind.toot(winddirection_texts_dark[i].encode("utf8"))
        time.sleep(5)
        masto_dark_wind.toot(windspeed_texts_dark[i].encode("utf8"))
        
    if run_mode == "operational":
        with open("last-run.txt", "w") as f:
            utc_datetime = pytz.utc.localize(datetime.datetime.utcnow())
            swiss_datetime = utc_datetime.astimezone(
                pytz.timezone("Europe/Zurich"))
            f.write(str(swiss_datetime))
