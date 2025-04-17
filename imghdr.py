"""
Minimal imghdr module implementation for python-telegram-bot compatibility.
"""

def what(file, h=None):
    """
    Tests the image data contained in the file named by file, and returns a
    string describing the image type.
    """
    f = None
    try:
        if h is None:
            if isinstance(file, str):
                f = open(file, 'rb')
                h = f.read(32)
            else:
                location = file.tell()
                h = file.read(32)
                file.seek(location)
        if not h:
            return None

        if h.startswith(b'\xff\xd8'):
            return 'jpeg'
        if h.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        if h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
            return 'gif'
        if h.startswith(b'BM'):
            return 'bmp'
        if h.startswith(b'MM\x00\x2a') or h.startswith(b'II\x2a\x00'):
            return 'tiff'
        if h.startswith(b'RIFF') and h[8:12] == b'WEBP':
            return 'webp'
        return None
    finally:
        if f:
            f.close() 