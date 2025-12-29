# emoji-weather

## About
**A ~~[Twitter bot](https://twitter.com/tweteoswiss)~~ family of [Mastodon](https://joinmastodon.org) bots that broadcast weather and temperature forecasts for Switzerland using emojis. Broadcasts are sent according to the following schedule:**
- **in the morning (6:30 local time)**: forecasts for mid-morning
- **at noon (11:45)**: forecasts for mid-afternoon
- **in the afternoon (15:30)**: forecast for the evening

## Accounts

**Follow the following Fediverse accounts for receiving these forecasts:**

- **Weather and temperature forecasts**:
  - [**@meteo – dark mode**](https://tooting.ch/@meteo)
  - [**@meteo – light mode**](https://tooting.ch/@meteo_light)
- **Wind speed and wind direction forecasts**:
  - [**@meteoplus – dark mode**](https://tooting.ch/@meteoplus)
  - [**@meteoplus – light mode**](https://tooting.ch/@meteoplus_light)

## Previews

### Weather forecast

![](https://raw.githubusercontent.com/rastrau/emoji-weather/main/assets/mastodon-screenshots/emoji-weather-3-cropped.png)

### Temperature forecast

![](https://raw.githubusercontent.com/rastrau/emoji-weather/main/assets/mastodon-screenshots/emoji-temp-1.png)
![](https://raw.githubusercontent.com/rastrau/emoji-weather/main/assets/mastodon-screenshots/emoji-temp-3.png)

### Wind speed forecast

![](https://raw.githubusercontent.com/rastrau/emoji-weather/main/assets/mastodon-screenshots/emoji-windspeed-1.png)
![](https://raw.githubusercontent.com/rastrau/emoji-weather/main/assets/mastodon-screenshots/emoji-windspeed-3.png)

### Wind direction forecast

![](https://raw.githubusercontent.com/rastrau/emoji-weather/main/assets/mastodon-screenshots/emoji-winddir-5-cropped.png)

## Explanation of symbols

Temperature, wind speed, and wind direction forecasts are self-explanatory. The following symbols are used in the weather forecast:

- light thunderstorm: 🌩️
- thunderstorm: 🌩️
- thunderstorm with light rain: 🌩️
- thunderstorm with light drizzle: 🌩️
- thunderstorm with drizzle: 🌩️
- thunderstorm with heavy drizzle: ⛈️
- thunderstorm with rain: ⛈️
- thunderstorm with heavy rain: ⛈️
- heavy thunderstorm: ⚡
- ragged thunderstorm: ⚡
- light intensity drizzle: ⛅
- drizzle: 🌦️
- light rain: 🌦️
- heavy intensity drizzle: 🌦️
- light intensity drizzle rain: 🌦️
- drizzle rain: 🌧️
- heavy intensity drizzle rain: 🌧️
- moderate rain: 🌧️
- heavy intensity rain: 💧
- very heavy rain: 🐟
- extreme rain: 🐟
- heavy shower rain and drizzle: 💧
- shower rain and drizzle: 🌧️
- shower drizzle: 🌧️
- freezing rain: 🌧️
- light intensity shower rain: 🌦️
- shower rain: 🌦️
- heavy intensity shower rain: 🌧️
- ragged shower rain: 🌦️
- light snow: 🌨️
- sleet: 🌨️
- light shower sleet: 🌨️
- shower sleet: ❄️
- snow: ❄️
- heavy snow: ☃️
- light rain and snow: ❄️
- rain and snow: ❄️
- light shower snow: ❄️
- shower snow: ❄️
- heavy shower snow: ❄️
- mist: 🌫️
- smoke: 🌫️
- haze: 🌫️
- sand/ dust whirls: 🌫️
- fog: 🌫️
- sand: 🌫️
- dust: 🌫️
- volcanic ash: 🌫️
- squalls: 💨
- tornado: 🌪️
- clear sky: 😎
- few clouds: ☀️
- scattered clouds: 🌤️
- broken clouds: ⛅
- overcast clouds: ☁️

## Data sources
`emoji-weather` uses data from [OpenWeather](https://openweathermap.org). 

The map design is hand-crafted by me. It can be called a tile map, grid(ded) map, or cartogram. I like tile maps, you can see other examples I've made [here](https://github.com/ebp-group/Switzerland_Tilemap), [here](https://rastrau.shinyapps.io/covid-us), [here](https://rastrau.shinyapps.io/covid-eu), or [here](https://rastrau.shinyapps.io/covidmonitor/) (the latter three I've contributed to the [{geofacet}](https://hafen.github.io/geofacet/) package for R).

## More background
I published three blog posts (in German) that go into more detail regarding the map design, obtaining weather data, and running the emoji-weather bots:

- [Map design](https://digital.ebp.ch/2023/04/17/wettervorhersage-in-social-media-teil-1-visualisierung/)
- [Sampling locations, data, and programming](https://digital.ebp.ch/2023/04/20/wettervorhersage-in-social-media-teil-2-daten-und-programmierung/)
- [Automation and deployment](https://digital.ebp.ch/2023/04/26/wettervorhersage-in-social-media-teil-3-automatisierung-und-cloud-deployment/)

## Usage conditions and contributions
Please [get in touch](mailto:emoji-weather@ralphstraumann.ch) if you would like to use this code or want to share an idea or suggestion.

&mdash; [@rastrau@swiss.social](https://swiss.social/@rastrau) 

## Post-scriptum

I used to run this family of bots on Twitter, [**but**](https://twitter.com/TweteoSwiss/status/1600159101987672064).
