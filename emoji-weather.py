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

def find_forecast(data, offset_hours):
    target_datetime = pytz.utc.localize(datetime.datetime.utcnow()) + \
        datetime.timedelta(hours=offset_hours)
    target_index = 0
    min_offset = sys.maxint
    for i, item in enumerate(data["list"]):
        offset = get_utc_datetime(item["dt_txt"]) - target_datetime
        offset = abs(offset.total_seconds() / 3600)
        if offset < min_offset:
            min_offset = offset
            index = i
    return index

def parse_meteodata(json_data):
    index = find_forecast(json_data, offset_hours = OFFSET_HOURS)
    
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
    
    OPENWEATHERMAP_API_KEY = os.environ.get('OPEN_WEATHER_API_KEY')
    TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
    TWITTER_API_KEY_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')

    OFFSET_HOURS = 3
    URL = "https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid=%s" % OPENWEATHERMAP_API_KEY

    meteomap = MeteoMap()

    for i in range(1, 85):
        (lat, lon) = config.locations.get(i, (None, None))
        if lat:
            time.sleep(0.2)
            this_url = URL.replace("{lat}", str(lat)).replace("{lon}", str(lon))
            print "Querying %s (%s)..." % (this_url, i)
            response = requests.get(this_url)
            
            meteodatum = parse_meteodata(response.json())
            meteomap.add_datum(i, meteodatum)

    meteomap.emojify_weather()
    temp_p20, temp_p40, temp_p60, temp_p80, temp_p100 = meteomap.emojify_temperature()


    forecast_time = int(meteomap.timestamp.strftime('%H')) + float(meteomap.timestamp.strftime('%M')) / 60
    if 0 < forecast_time <= 11:
        timespan = "Morning "
    elif 11 < forecast_time <= 13:
        timespan = "Noon "
    elif 13 < forecast_time <= 16:
        timespan = "Afternoon "
    elif 16 < forecast_time:
        timespan = "Evening "
    else:
        timespan = ""


    forecast = u"%s %s%s – Wᴇᴀᴛʜᴇʀ Fᴏʀᴇᴄᴀsᴛ\n\n" % (meteomap.timestamp.strftime('%d. %b'), 
                                                timespan, 
                                                meteomap.timestamp.strftime('%H:%M'))
    for i in range(1,85):
        emoji = meteomap.weather.get(i, u"⬜")
        forecast += emoji
        if i > 0 and i % 12 == 0:
            forecast += u"\n"

    temperature = u"%s %s%s – Tᴇᴍᴘ\n\n" % (meteomap.timestamp.strftime('%d. %b'), 
                                        timespan, 
                                        meteomap.timestamp.strftime('%H:%M'))
    for i in range(1,85):
        emoji = meteomap.temperature.get(i, u"⬜")
        temperature += emoji
        if i > 0 and i % 12 == 0:
            temperature += u"\n"

    temperature += u"\n"
    temperature += u"°C\n"
    temperature += u"🟥 %s–%s\n" % (temp_p80, temp_p100)
    temperature += u"🟧 %s–%s\n" % (temp_p60, temp_p80)
    temperature += u"🟨 %s–%s\n" % (temp_p40, temp_p60)
    temperature += u"🟩 %s–%s\n" % (temp_p20, temp_p40)
    temperature += u"🟦 <%s\n" % temp_p20


    if testing:
        with codecs.open("test.txt", "w", "utf8") as f:
            f.write(forecast)
            f.write("--------------------------------------------\n")
            f.write(temperature)
    else:
        t = Twitter(auth=OAuth(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, 
                            TWITTER_API_KEY, TWITTER_API_KEY_SECRET))
        
        tweet = t.statuses.update(status=forecast.encode('utf8'))
        tweet = t.statuses.update(status=temperature.encode('utf8'))
        # tweet = t.statuses.update(status=temperature.encode('utf8'), in_reply_to_status_id = tweet["id_str"])
        # tweet = t.statuses.update(status=winddirection.encode('utf8'), in_reply_to_status_id = tweet["id_str"])

