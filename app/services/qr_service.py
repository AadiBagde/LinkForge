import qrcode
from io import BytesIO
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def generate_qr(url: str) -> bytes:
    """
    Generate a QR code for a URL.
    
    Args:
        url: URL to encode in QR code
        
    Returns:
        PNG image bytes of the QR code
    """
    try:
        qr = qrcode.make(url)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        
        logger.debug(f"QR code generated for URL: {url}")
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise