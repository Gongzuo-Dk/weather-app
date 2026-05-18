import requests
from django.conf import settings
from datetime import datetime, timezone, timedelta

def get_coordinates(city):
    # Convert a city name to lat/lon coordinates using OpenWeather Geocoding API.
    # Returns a dict with lat, lon, and full city name.
    # Returns None if city not found or error occurs.

    api_key = settings.OPENWEATHER_API_KEY
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city,
        "limit": 1,
        "appid": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None
        
        return {
            "lat": data[0]["lat"],
            "lon": data[0]["lon"],
            "city_name": data[0]["name"],
            "country": data[0]["country"],
        }
    except requests.exceptions.RequestException:
        return None
    
def get_current_weather(city):
    coords = get_coordinates(city)
    if not coords:
        return None

    api_key = settings.OPENWEATHER_API_KEY
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "appid": api_key,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        city_offset = timezone(timedelta(seconds=data["timezone"]))

        return {
            "city": coords["city_name"],
            "country": coords["country"],
            "temperature": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "visibility": data.get("visibility", 0) // 1000,
            "description": data["weather"][0]["description"].capitalize(),
            "icon": data["weather"][0]["icon"].replace("n", "d"),
            "wind_speed": data["wind"]["speed"],
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"], tz=city_offset).strftime("%H:%M"),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"], tz=city_offset).strftime("%H:%M"),
        }

    except requests.exceptions.RequestException:
        return None
    
def get_forecast(city):
    # Fetch 5-day forecast for a city.
    # The API returns data every 3 hours — we extract one entry per day (midday reading).
    # Returns a list of daily forecast dicts.
    # Returns None if anything goes wrong.

    coords = get_coordinates(city)
    if not coords:
        return None
    
    api_key = settings.OPENWEATHER_API_KEY
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "appid": api_key,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        daily = {}
        for entry in data["list"]:
            date = entry["dt_txt"].split(" ")[0]  # "2024-05-13 12:00:00" → "2024-05-13"
            hour = entry["dt_txt"].split(" ")[1]  # → "12:00:00"

            # only take the midday reading for each day
            if hour == "12:00:00" and date not in daily:
                daily[date] = {
                    "date": date,
                    "temp_max": round(entry["main"]["temp_max"]),
                    "temp_min": round(entry["main"]["temp_min"]),
                    "description": entry["weather"][0]["description"].capitalize(),
                    "icon": entry["weather"][0]["icon"].replace("n", "d"),
                }

        return list(daily.values())

    except requests.exceptions.RequestException:
        return None
    
