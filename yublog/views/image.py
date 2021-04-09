import re
import os

from flask import render_template, send_from_directory, request, flash, redirect, url_for
from flask.globals import current_app
from flask_login import login_required

from yublog.extensions import db
from yublog.models import Image
from yublog.views import image_bp
from yublog.views.utils.image_utils import IMAGE_MIMES, asyncio_saver


@image_bp.route('/')
@image_bp.route('/index')
def index():
    paths = Image.query.with_entities(Image.path).distinct().all()
    # print(Image.query.with_entities(Image.path).distinct())
    # print(f'paths: {paths}')
    paths = [p[0] for p in paths]
    return render_template('image/index.html', paths=paths, title='图片')



@image_bp.route('/<path>/', methods=['GET', 'POST'])
def get_path_images(path):
    if request.method == 'POST':
        img_name = request.form.get('key', None)
        file = request.files['file']
        filename = file.filename
        img_stream = file.stream.read()
        if img_name:
            filename = re.sub(r'[\/\\\:\*\?"<>|]', r'_', img_name)
        if file.mimetype in IMAGE_MIMES:
            asyncio_saver(
                os.path.join(current_app.config['IMAGE_UPLOAD_PATH'], path),
                filename, img_stream)
            
            up_img = Image(path=path, filename=filename)
            db.session.add(up_img)
            db.session.commit()
            flash('Upload image {0} successful'.format(filename))

        flash('Upload image fail')
        return redirect(url_for('image.get_path_images', path=path))

    images = Image.query.filter_by(path=path).order_by(Image.id).all()
    # print(f'images: {images}')
    return render_template('image/path.html', path=path, images=images, title='图片路径')


@image_bp.route('/<path>/<filename>')
@login_required
def get_image(path, filename):
    return send_from_directory('static', 'upload/image/{path}/{filename}'.format(path=path, filename=filename))


