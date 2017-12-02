from flask import render_template

from . import main
from app import db


@main.errorhandler(404)
def page_not_found(error):
    return render_template('error/404.html', title='404'), 404

@main.errorhandler(500)
def internal_server_error(error):
    db.session.rollback()
    db.session.commit()
    return render_template('error/500.html', title='500'), 500
