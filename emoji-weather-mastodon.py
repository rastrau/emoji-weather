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

    def set_basemap(self, emojimap, lakes=True):
        emojimap[1] = "🇫🇷"
        emojimap[12] = "🇩🇪"
        emojimap[24] = "🇦🇹"
        emojimap[84] = "🇮🇹"
        if lakes:
            emojimap[10] = "🔵"
            emojimap[62] = "🔵"
        return

    def emojify_weather(self):
        for key, w in self.weather.items():
            self.weather[key] = config.emojis.get(w.lower(), "❔")
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
        self.set_basemap(self.temperature, lakes=False)
        return (
            round(p20, 1),
            round(p40, 1),
            round(p60, 1),
            round(p80, 1),
            round(p100, 1),
        )

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
        self.set_basemap(self.winddirection, lakes=False)
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
            weather_tweet = weather_tweet = "%s %s – Wᴇᴀᴛʜᴇʀ\n\n" % (
                meteomap.timestamp.strftime("%d. %b"),
                timespan[1:],
            )
        else:
            weather_tweet = "%s %s – Wᴇᴀᴛʜᴇʀ\n\n" % (
                timespan,
                meteomap.timestamp.strftime("%d. %b"),
            )
        for i in range(1, 85):
            emoji = self.weather.get(i, "▫️")
            weather_tweet += emoji
            if i > 0 and i % 12 == 0:
                weather_tweet += "\n"
        return weather_tweet

    def compile_temperature_text(self, timespan):
        temp_p20, temp_p40, temp_p60, temp_p80, temp_p100 = self.emojify_temperature()

        if timespan.startswith("-"):
            temperature_tweet = "%s %s – Tᴇᴍᴘ\n\n" % (
                meteomap.timestamp.strftime("%d. %b"),
                timespan[1:],
            )
        else:
            temperature_tweet = "%s %s – Tᴇᴍᴘ\n\n" % (
                timespan,
                meteomap.timestamp.strftime("%d. %b"),
            )
        for i in range(1, 85):
            emoji = self.temperature.get(i, "▫️")
            temperature_tweet += emoji
            if i > 0 and i % 12 == 0:
                temperature_tweet += "\n"
        temperature_tweet += "\n"
        temperature_tweet += "🟥 %s–%s °C\n" % (temp_p80, temp_p100)
        temperature_tweet += "🟧 %s–%s\n" % (temp_p60, temp_p80)
        temperature_tweet += "🟨 %s–%s\n" % (temp_p40, temp_p60)
        temperature_tweet += "🟩 %s–%s\n" % (temp_p20, temp_p40)
        temperature_tweet += "🟦 <%s\n" % temp_p20

        # Emphasise very cold and very hot temperature situations
        if temp_p20 < -5:
            temperature_tweet = self._coldify_emoji_temperature(temperature_tweet)
        if temp_p80 > 27:
            temperature_tweet = self._warmify_emoji_temperature(temperature_tweet)
        return temperature_tweet

    def _coldify_emoji_temperature(self, temperature_tweet):
        temperature_tweet = temperature_tweet.replace("🟦", "🥶")
        temperature_tweet = temperature_tweet.replace("🟩", "🟦")
        temperature_tweet = temperature_tweet.replace("🟨", "🟩")
        temperature_tweet = temperature_tweet.replace("🟧", "🟨")
        temperature_tweet = temperature_tweet.replace("🟥", "🟧")
        return temperature_tweet

    def _warmify_emoji_temperature(self, temperature_tweet):
        temperature_tweet = temperature_tweet.replace("🟥", "🥵")
        temperature_tweet = temperature_tweet.replace("🟧", "🟥")
        temperature_tweet = temperature_tweet.replace("🟨", "🟧")
        temperature_tweet = temperature_tweet.replace("🟩", "🟨")
        temperature_tweet = temperature_tweet.replace("🟦", "🟩")
        return temperature_tweet

    def compile_winddirection_text(self, timespan):
        self.emojify_winddirection()
        if timespan.startswith("-"):
            winddirection_tweet = "%s %s – Wɪɴᴅ Dɪʀᴇᴄᴛɪᴏɴ\n\n" % (
                meteomap.timestamp.strftime("%d. %b"),
                timespan[1:],
            )
        else:
            winddirection_tweet = "%s %s – Wɪɴᴅ Dɪʀᴇᴄᴛɪᴏɴ\n\n" % (
                timespan,
                meteomap.timestamp.strftime("%d. %b"),
            )
        for i in range(1, 85):
            emoji = self.winddirection.get(i, "▫️")
            winddirection_tweet += emoji
            if i > 0 and i % 12 == 0:
                winddirection_tweet += "\n"
        return winddirection_tweet

    def compile_windspeed_text(self, timespan):
        (
            windspeed_p25,
            windspeed_p50,
            windspeed_p75,
            windspeed_p100,
        ) = self.emojify_windspeed()

        if timespan.startswith("-"):
            windspeed_tweet = "%s %s – Wɪɴᴅ Sᴘᴇᴇᴅ\n\n" % (
                meteomap.timestamp.strftime("%d. %b"),
                timespan[1:],
            )
        else:
            windspeed_tweet = "%s %s – Wɪɴᴅ Sᴘᴇᴇᴅ\n\n" % (
                timespan,
                meteomap.timestamp.strftime("%d. %b"),
            )
        for i in range(1, 85):
            emoji = self.windspeed.get(i, "▫️")
            windspeed_tweet += emoji
            if i > 0 and i % 12 == 0:
                windspeed_tweet += "\n"
        windspeed_tweet += "\n"
        windspeed_tweet += "⬛ %s–%s m/s\n" % (windspeed_p75, windspeed_p100)
        windspeed_tweet += "◼️ %s–%s\n" % (windspeed_p50, windspeed_p75)
        windspeed_tweet += "◾ %s–%s\n" % (windspeed_p25, windspeed_p50)
        windspeed_tweet += "▪️ <%s\n" % windspeed_p25
        return windspeed_tweet


class MeteoDatum:
    def __init__(
        self,
        weather,
        temperature,
        humidity,
        clouds,
        windspeed,
        winddirection,
        precipitation_probability,
        timestamp,
    ):
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
    return (
        np.percentile(data, 20),
        np.percentile(data, 40),
        np.percentile(data, 60),
        np.percentile(data, 80),
        np.percentile(data, 100),
    )


def quartile(data):
    return (
        np.percentile(data, 25),
        np.percentile(data, 50),
        np.percentile(data, 75),
        np.percentile(data, 100),
    )


def kelvin_to_celsius(temperature):
    return temperature - 273.15


def find_forecast(data, target_time_local):
    # Find the current date in Swiss timezone
    utc_datetime = pytz.utc.localize(datetime.datetime.utcnow())
    swiss_datetime = utc_datetime.astimezone(pytz.timezone("Europe/Zurich"))
    swiss_date = datetime.datetime.strftime(swiss_datetime, "%Y-%m-%d")

    # Parse today's date and target_time_local as (Swiss) datetime
    # and convert to UTC datetime
    swiss_datetime = datetime.datetime.strptime(
        "%s %s" % (swiss_date, target_time_local), "%Y-%m-%d %H:%M"
    )
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
            target_index = i
    return target_index


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
    return MeteoDatum(
        weather,
        temperature,
        humidity,
        clouds,
        wind_speed,
        wind_direction,
        precipitation_probability,
        timestamp,
    )


def switch_light_to_dark_mode(text):
    text = text.replace("▫️", "🔄")
    text = text.replace("▪️", "▫️")
    text = text.replace("◾", "◽")
    text = text.replace("◼️", "◻️")
    text = text.replace("⬛", "⬜")
    text = text.replace("🔄", "▪️")
    return text


def make_linkedin_compatible(text):
    # Currently on Desktop (Edge browser), LinkedIn does not display
    # country flags. Also, the small whitespace emoji (▫️) is not
    # displayed with proper spacing. Both work fine in the mobile app,
    # however.
    text = text.replace("▫️", "⬜")
    text = text.replace("🇫🇷", "⬜")
    return text


if __name__ == "__main__":
    run_mode = os.environ.get("RUN_MODE")
    print("Run mode: %s" % run_mode)
    # run_mode can be:
    # - "operational" →    for running the bots operationally using GitHub Actions
    # - "remote testing" → for test-running using GitHub Actions; will toot through
    #                      @meteo_test_45618761@tooting.ch
    # - undefined
    #   (equates to
    #   "local") →         for test-running on the local machine (needs 'Secrets.py')
    #                      and will toot through @meteo_test_45618761@tooting.ch as
    #                      well as saving the toots to disk

    # Set constants depending on the run_mode
    if run_mode == "operational":
        print("Configuring run mode '%s'" % run_mode)
        TARGET_TIME_LOCAL = os.environ.get("TARGET_TIME_LOCAL")
        TARGET_TIME_HUMAN = os.environ.get("TARGET_TIME_HUMAN")
        OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")
        LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        LINKEDIN_PERSONAL_URN_ID = os.environ.get("LINKEDIN_PERSONAL_URN_ID")
        MASTO_DARK_WEATHER = os.environ.get("MASTO_DARK_WEATHER")
        MASTO_DARK_WIND = os.environ.get("MASTO_DARK_WIND")
        MASTO_LIGHT_WEATHER = os.environ.get("MASTO_LIGHT_WEATHER")
        MASTO_LIGHT_WIND = os.environ.get("MASTO_LIGHT_WIND")
    elif run_mode == "remote testing":
        print("Configuring run mode '%s'" % run_mode)
        TARGET_TIME_LOCAL = "09:00"
        TARGET_TIME_HUMAN = "Morning"
        OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")
        LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        LINKEDIN_PERSONAL_URN_ID = os.environ.get("LINKEDIN_PERSONAL_URN_ID")
        MASTO_DARK_WEATHER = os.environ.get("MASTO_TEST_TOKEN")
        MASTO_DARK_WIND = MASTO_DARK_WEATHER
        MASTO_LIGHT_WEATHER = MASTO_DARK_WEATHER
        MASTO_LIGHT_WIND = MASTO_DARK_WEATHER
    else:
        import Secrets

        print("→ Configuring run mode 'local testing'")
        run_mode = "local testing"
        secrets = Secrets.Secrets()
        TARGET_TIME_LOCAL = "20:00"
        TARGET_TIME_HUMAN = "Evening"  # can be, e.g. "Morning",
        # "Afternoon", or "Evening"
        OPENWEATHERMAP_API_KEY = secrets.OPENWEATHERMAP_API_KEY
        MASTO_DARK_WEATHER = secrets.MASTO_TEST_TOKEN
        MASTO_DARK_WIND = MASTO_DARK_WEATHER
        MASTO_LIGHT_WEATHER = MASTO_DARK_WEATHER
        MASTO_LIGHT_WIND = MASTO_DARK_WEATHER
        LINKEDIN_ACCESS_TOKEN = secrets.LINKEDIN_ACCESS_TOKEN
        LINKEDIN_PERSONAL_URN_ID = secrets.LINKEDIN_PERSONAL_URN_ID

    config = Config.Config()
    OPENWEATHERMAP_URL = (
        "https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid=%s"
        % OPENWEATHERMAP_API_KEY
    )
    MASTODON_URL = "https://tooting.ch"
    masto_light_weather = Mastodon(
        api_base_url=MASTODON_URL, access_token=MASTO_LIGHT_WEATHER
    )
    masto_dark_weather = Mastodon(
        api_base_url=MASTODON_URL, access_token=MASTO_DARK_WEATHER
    )
    masto_light_wind = Mastodon(
        api_base_url=MASTODON_URL, access_token=MASTO_LIGHT_WIND
    )
    masto_dark_wind = Mastodon(api_base_url=MASTODON_URL, access_token=MASTO_DARK_WIND)

    LINKEDIN_API_VERSION = "202302"

    # Obtain weather information from API
    meteomap = MeteoMap()
    for i in range(1, 85):
        (lat, lon) = config.locations.get(i, (None, None))
        if lat:
            time.sleep(0.2)
            this_url = OPENWEATHERMAP_URL.replace("{lat}", str(lat)).replace(
                "{lon}", str(lon)
            )
            response = requests.get(this_url)
            meteodatum = parse_meteodata(response.json(), TARGET_TIME_LOCAL)
            meteomap.add_datum(i, meteodatum)

    # Compile forecast texts in light and dark modes
    print("\nCompiling weather forecast text...")
    weather_text_light = meteomap.compile_weather_text(TARGET_TIME_HUMAN)
    weather_text_dark = switch_light_to_dark_mode(weather_text_light)

    print("Compiling temperature forecast text...")
    temperature_text_light = meteomap.compile_temperature_text(TARGET_TIME_HUMAN)
    temperature_text_dark = switch_light_to_dark_mode(temperature_text_light)

    print("Compiling wind-direction forecast text...")
    winddirection_text_light = meteomap.compile_winddirection_text(TARGET_TIME_HUMAN)
    winddirection_text_dark = switch_light_to_dark_mode(winddirection_text_light)

    print("Compiling wind-speed forecast text...")
    windspeed_text_light = meteomap.compile_windspeed_text(TARGET_TIME_HUMAN)
    windspeed_text_dark = switch_light_to_dark_mode(windspeed_text_light)

    if run_mode == "local testing":
        # Write forecasts to a file
        with codecs.open("test-forecast-texts.txt", "w", "utf8") as f:
            for content in [
                "LIGHT MODE:",
                weather_text_light,
                temperature_text_light,
                winddirection_text_light,
                windspeed_text_light,
                "DARK MODE:",
                weather_text_dark,
                temperature_text_dark,
                winddirection_text_dark,
                windspeed_text_dark,
            ]:
                f.write(content)
                f.write("--------------------------------------------\n")

    # Broadcast to Mastodon using the operational or the test account,
    # depending on run_mode and configuration
    print("Broadcasting forecasts on Mastodon...")
    for content in [weather_text_light, temperature_text_light]:
        masto_light_weather.toot(content.encode("utf8"))
        time.sleep(2)
    for content in [winddirection_text_light, windspeed_text_light]:
        masto_light_wind.toot(content.encode("utf8"))
        time.sleep(2)
    for content in [weather_text_dark, temperature_text_dark]:
        masto_dark_weather.toot(content.encode("utf8"))
        time.sleep(2)
    for content in [winddirection_text_dark, windspeed_text_dark]:
        masto_dark_wind.toot(content.encode("utf8"))
        time.sleep(2)

    # Broadcast to LinkedIn using the operational account (currently,
    # there is no test account for LinkedIn)

    linkedin_broadcasting = False
    if linkedin_broadcasting:
        print("Broadcasting forecasts on LinkedIn...")
        # Instantiate LinkedIn API client
        restli_client = RestliClient()
        # Broadcast weather and temperature forecast on LinkedIn
        weather_text_light = make_linkedin_compatible(weather_text_light)
        posts_create_response = restli_client.create(
            resource_path="/posts",
            entity={
                "author": "urn:li:person:{LINKEDIN_PERSONAL_URN_ID}",
                "lifecycleState": "PUBLISHED",
                "visibility": "PUBLIC",
                "commentary": weather_text_light,
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
            },
            version_string=LINKEDIN_API_VERSION,
            access_token=LINKEDIN_ACCESS_TOKEN,
        )
        temperature_text_light = make_linkedin_compatible(
            temperature_text_light.strip()
        )
        posts_create_response = restli_client.create(
            resource_path="/posts",
            entity={
                "author": "urn:li:person:{LINKEDIN_PERSONAL_URN_ID}",
                "lifecycleState": "PUBLISHED",
                "visibility": "PUBLIC",
                "commentary": temperature_text_light,
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
            },
            version_string=LINKEDIN_API_VERSION,
            access_token=LINKEDIN_ACCESS_TOKEN,
        )

    if run_mode == "operational":
        # Save 'keep-alive' file in order to keep GitHub Action
        # running indefinitely
        with open("last-run.txt", "w") as f:
            utc_datetime = pytz.utc.localize(datetime.datetime.utcnow())
            swiss_datetime = utc_datetime.astimezone(pytz.timezone("Europe/Zurich"))
            f.write(str(swiss_datetime))
