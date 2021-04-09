import os
from threading import Thread


IMAGE_MIMES = [
    'image/x-icon',
    'image/svg+xml',
    'image/jpeg',
    'image/gif',
    'image/png',
    'image/webp'
]


def image_saver(filename, img_stream):
    with open(filename, 'wb') as w:
        w.write(img_stream)
    return True


def asyncio_saver(path, name, img_stream):
    t = Thread(target=image_saver, args=(os.path.join(path, name), img_stream))
    t.start()
    return t
