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


def mkdir(path):
    os.mkdir(path)


def image_saver(filename, img_stream):
    with open(filename, 'wb') as w:
        w.write(img_stream)
    return True


def image_remove(path, filename):
    os.remove(os.path.join(path, filename))


def image_rename(path, old_name, new_name):
    os.rename(os.path.join(path, old_name), os.path.join(path, new_name))


def asyncio_saver(path, name, img_stream):
    t = Thread(target=image_saver, args=(os.path.join(path, name), img_stream))
    t.start()
    return t
