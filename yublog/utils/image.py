import os

from yublog.utils.as_sync import as_sync

IMAGE_MIMES = [
    'image/x-icon',
    'image/svg+xml',
    'image/jpeg',
    'image/gif',
    'image/png',
    'image/webp'
]


@as_sync
def mkdir(path):
    os.mkdir(path)


@as_sync
def saver(path, name, img_stream):
    with open(os.path.join(path, name), 'wb') as w:
        w.write(img_stream)
    return True


@as_sync
def remove(path, filename):
    os.remove(os.path.join(path, filename))


@as_sync
def rename(path, old_name, new_name):
    os.rename(os.path.join(path, old_name), os.path.join(path, new_name))
