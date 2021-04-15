import re
import os

from flask import render_template, send_from_directory, request, flash, redirect, url_for
from flask.globals import current_app
from flask_login import login_required

from yublog.extensions import db
from yublog.forms import AddImagePathForm
from yublog.models import Image, ImagePath
from yublog.views import image_bp
from yublog.views.utils.image_utils import IMAGE_MIMES, asyncio_saver, image_remove, image_rename, mkdir


@image_bp.route('/')
@image_bp.route('/index', methods=['GET', 'POST'])
def index():
    _paths = ImagePath.query.all()
    paths = [p.path for p in _paths]

    form = AddImagePathForm()
    if form.validate_on_submit():
        new_path = form.path_name.data
        # print(f'new_path: {new_path}')
        if new_path and new_path not in paths:
            _path = ImagePath(path=new_path)
            db.session.add(_path)
            db.session.commit()
            mkdir(os.path.join(current_app.config['IMAGE_UPLOAD_PATH'], new_path))
            flash('Add image path successful.')
        else:
            flash('Add image path fail.')
        return redirect(url_for('image.index'))

    return render_template('image/index.html', paths=paths, form=form, title='图片')


@image_bp.route('/<path>/', methods=['GET', 'POST'])
def get_path_images(path):
    images = Image.query.filter_by(path=path).order_by(Image.id).all()
    filenames = {i.filename for i in images}
    if request.method == 'POST':
        img_name = request.form.get('key', None)
        file = request.files['file']
        filename = file.filename if not img_name else re.sub(r'[\/\\\:\*\?"<>|]', r'_', img_name)
        img_stream = file.stream.read()
        print(f'file.mimetype : {file.mimetype }')
        if filename not in filenames and file.mimetype in IMAGE_MIMES:
            asyncio_saver(
                os.path.join(current_app.config['IMAGE_UPLOAD_PATH'], path),
                filename, img_stream)
            
            _path = ImagePath.query.filter_by(path=path).first()
            up_img = Image(path=path, filename=filename, image_path=_path)
            db.session.add(up_img)
            db.session.commit()
            flash('Upload image {0} successful'.format(filename))
        else:
            flash('Upload image fail')
        return redirect(url_for('image.get_path_images', path=path))

    images = Image.query.filter_by(path=path).order_by(Image.id).all()
    # print(f'images: {images}')
    return render_template('image/path.html', path=path, images=images, title='图片路径')


@image_bp.route('/<path>/<filename>')
@login_required
def get_image(path, filename):
    return send_from_directory('static', 'upload/image/{path}/{filename}'.format(path=path, filename=filename))


@image_bp.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_img():
    _id = request.get_json()['id']
    _image = Image.query.get_or_404(_id)
    cur_img_path = _image.path
    filename = _image.filename

    db.session.delete(_image)
    db.session.commit()

    image_remove(os.path.join(current_app.config['IMAGE_UPLOAD_PATH'], cur_img_path), filename)
    flash('Delete image {0} successful'.format(_id))
    return redirect(url_for('image.get_path_images', path=cur_img_path))


@image_bp.route('/rename', methods=['GET', 'POST'])
@login_required
def rename_img():
    _id = request.get_json()['id']
    new_name = request.get_json()['newName']
    new_name = re.sub(r'[\/\\\:\*\?"<>|]', r'_', new_name)
    _image = Image.query.get_or_404(_id)
    cur_img_path = _image.path
    # 判断图片名称是否存在
    images = Image.query.filter_by(path=cur_img_path).all()
    filenames = {i.filename for i in images}
    if new_name in filenames:
        return redirect(url_for('image.get_path_images', path=cur_img_path))

    old_name = _image.filename
    _image.filename = new_name
    db.session.add(_image)
    db.session.commit()

    image_rename(os.path.join(current_app.config['IMAGE_UPLOAD_PATH'], cur_img_path), old_name, new_name)
    flash('Rename image {0} successful'.format(new_name))
    return redirect(url_for('image.get_path_images', path=cur_img_path))
