import requests


def get_location(ip: str):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()

        country = data.get("country")
        city = data.get("city")

        return country, city

    except Exception:
        return None, None