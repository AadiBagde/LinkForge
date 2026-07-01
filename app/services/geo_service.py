import requests
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def get_location(ip: str) -> tuple[str | None, str | None]:
    """
    Get geolocation for an IP address.
    
    Args:
        ip: IP address to geolocate
        
    Returns:
        Tuple of (country, city) or (None, None) on failure
    """
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        data = response.json()

        if data.get("status") != "success":
            logger.warning(f"Geolocation API error for {ip}: {data.get('message')}")
            return None, None

        country = data.get("country")
        city = data.get("city")

        logger.debug(f"Geolocation resolved for {ip}: {country}, {city}")
        return country, city

    except requests.Timeout:
        logger.warning(f"Geolocation request timeout for {ip}")
        return None, None
    except requests.RequestException as e:
        logger.warning(f"Geolocation API error for {ip}: {str(e)}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error in geolocation for {ip}: {str(e)}")
        return None, None