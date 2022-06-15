import re
import os

from flask import (
    render_template,
    send_from_directory,
    request,
    redirect,
    url_for
)
from flask.globals import current_app
from flask_login import login_required
from loguru import logger

from yublog import cache_operate, CacheType, CacheKey
from yublog.forms import AddImagePathForm
from yublog.models import Image, ImagePath
from yublog.views import image_bp
from yublog.utils import image, commit

PATH_SUB = r'[./\\\'"]'
IMAGE_SUB = r'[/\\\':*?"<>|]'


@image_bp.route("/")
@image_bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    _paths = cache_operate.getset(
        CacheType.IMAGE,
        CacheKey.IMAGE_PATH,
        lambda: ImagePath.query.all()
    )
    paths = {p.path for p in _paths}

    form = AddImagePathForm()
    if form.validate_on_submit():
        path = re.sub(PATH_SUB, r"_", form.path_name.data)
        if path and path not in paths:
            commit.add(ImagePath(path=path))
            image.mkdir(os.path.join(
                current_app.config["IMAGE_UPLOAD_PATH"], path
            ))
            cache_operate.clean(CacheType.IMAGE, CacheKey.IMAGE_PATH)
            logger.info("Add image path successful.")
        else:
            logger.info("Add image path fail.")

        return redirect(url_for("image.index"))
    return render_template(
        "image/index.html", 
        title="图片",
        form=form,
        paths=paths,
    )


@image_bp.route("/<path>/", methods=["GET", "POST"])
@login_required
def get_path_images(path):
    images = cache_operate.getset(
        CacheType.IMAGE,
        f"{path}:{CacheKey.IMAGES}",
        lambda: Image.query.filter_by(path=path).order_by(Image.id).all()
    )
    filenames = {i.filename for i in images}
    if request.method == "POST":
        img_name = request.form.get("key")
        file = request.files["file"]
        filename = file.filename \
            if not img_name else re.sub(IMAGE_SUB, r"_", img_name)

        if filename not in filenames and file.mimetype in image.IMAGE_MIMES:
            image.saver(
                os.path.join(current_app.config["IMAGE_UPLOAD_PATH"], path),
                filename,
                file.stream.read()
            )
            
            _path = cache_operate.getset(
                CacheType.IMAGE,
                path,
                lambda: ImagePath.query.filter_by(path=path).first()
            )
            commit.add(Image(path=path, filename=filename, image_path=_path))
            logger.info(f"Upload image {filename} successful")
        else:
            logger.info("Upload image fail")
        return redirect(url_for("image.get_path_images", path=path))

    return render_template(
        "image/path.html",
        title="图片路径",
        path=path,
        images=images,
    )


@image_bp.route("/<path>/<filename>")
def get_image(path, filename):
    return send_from_directory(
        "static",
        f"upload/image/{path}/{filename}"
    )


@image_bp.route("/delete", methods=["GET", "POST"])
@login_required
def delete_img():
    _image = Image.query.get_or_404(request.get_json()["id"])
    cur_img_path = _image.path
    filename = _image.filename

    commit.delete(_image)
    image.remove(
        os.path.join(current_app.config["IMAGE_UPLOAD_PATH"], cur_img_path), 
        filename
    )
    logger.info("Delete image successful")
    cache_operate.clean(CacheType.IMAGE, f"{cur_img_path}:{CacheKey.IMAGES}")
    return redirect(url_for("image.get_path_images", path=cur_img_path))


@image_bp.route("/rename", methods=["GET", "POST"])
@login_required
def rename_img():
    new_name = re.sub(IMAGE_SUB, r"_", request.get_json()["newName"])
    _image = Image.query.get_or_404(request.get_json()["id"])
    cur_img_path = _image.path

    images = cache_operate.getset(
        CacheType.IMAGE,
        f"{cur_img_path}:{CacheKey.IMAGES}",
        lambda: Image.query.filter_by(path=cur_img_path).order_by(Image.id).all()
    )
    filenames = {i.filename for i in images}
    if new_name in filenames:
        return redirect(url_for("image.get_path_images", path=cur_img_path))

    old_name = _image.filename
    _image.filename = new_name
    commit.add(_image)

    image.rename(
        os.path.join(current_app.config["IMAGE_UPLOAD_PATH"], cur_img_path),
        old_name,
        new_name
    )
    cache_operate.clean(CacheType.IMAGE, f"{cur_img_path}:{CacheKey.IMAGES}")
    logger.info(f"Rename image {new_name} successful")
    return redirect(url_for("image.get_path_images", path=cur_img_path))
