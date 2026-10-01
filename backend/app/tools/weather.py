from langchain_core.tools import tool
import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@tool
async def get_weather(location: str) -> str:
    """
    Get the current weather for a city or location.

    Use this tool when the user asks about:
    - current weather
    - current temperature
    - rain
    - humidity
    - wind
    - weather conditions
    - today's weather

    Examples:
    - weather in Nagpur
    - what's the weather in Mumbai?
    - is it raining in Delhi?
    - temperature in London
    """

    location = location.strip()

    if not location:
        return "Error: Please provide a city or location."

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:

            # -------------------------------------------------
            # Step 1: Convert location name -> coordinates
            # -------------------------------------------------
            geocoding_response = await client.get(
                GEOCODING_URL,
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )

            geocoding_response.raise_for_status()

            geocoding_data = geocoding_response.json()

            results = geocoding_data.get("results")

            if not results:
                return (
                    f"Error: Could not find the location '{location}'. "
                    "Please provide a valid city or location."
                )

            place = results[0]

            latitude = place["latitude"]
            longitude = place["longitude"]

            place_name = place.get("name", location)
            country = place.get("country", "")
            timezone = place.get("timezone", "auto")

            # -------------------------------------------------
            # Step 2: Get current weather
            # -------------------------------------------------
            weather_response = await client.get(
                WEATHER_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,"
                        "relative_humidity_2m,"
                        "apparent_temperature,"
                        "precipitation,"
                        "weather_code,"
                        "wind_speed_10m"
                    ),
                    "timezone": timezone,
                },
            )

            weather_response.raise_for_status()

            weather_data = weather_response.json()

            current = weather_data.get("current")

            if not current:
                return (
                    f"Error: Weather information is unavailable "
                    f"for {place_name}."
                )

            temperature = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            feels_like = current.get("apparent_temperature")
            precipitation = current.get("precipitation")
            weather_code = current.get("weather_code")
            wind_speed = current.get("wind_speed_10m")

            condition = _weather_code_to_description(
                weather_code
            )

            return (
                f"Current weather in {place_name}, {country}:\n"
                f"Condition: {condition}\n"
                f"Temperature: {temperature}°C\n"
                f"Feels like: {feels_like}°C\n"
                f"Humidity: {humidity}%\n"
                f"Precipitation: {precipitation} mm\n"
                f"Wind speed: {wind_speed} km/h\n"
                f"Timezone: {timezone}"
            )

    except httpx.TimeoutException:
        return (
            "Error: The weather service took too long to respond."
        )

    except httpx.HTTPError as error:
        return (
            f"Error: Unable to retrieve weather information. "
            f"{error}"
        )

    except (KeyError, TypeError, ValueError) as error:
        return (
            f"Error: Invalid weather service response. "
            f"{error}"
        )


def _weather_code_to_description(
    weather_code: int | None,
) -> str:

    descriptions = {
        0: "Clear sky",

        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",

        45: "Fog",
        48: "Depositing rime fog",

        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",

        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",

        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",

        66: "Light freezing rain",
        67: "Heavy freezing rain",

        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",

        77: "Snow grains",

        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",

        85: "Slight snow showers",
        86: "Heavy snow showers",

        95: "Thunderstorm",

        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    return descriptions.get(
        weather_code,
        "Unknown weather condition",
    )