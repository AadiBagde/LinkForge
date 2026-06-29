import qrcode
from io import BytesIO


def generate_qr(url: str):

    qr = qrcode.make(url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    return buffer.getvalue()