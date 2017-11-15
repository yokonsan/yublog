from flask import render_template, redirect, url_for, g
from flask_login import login_required, current_user

from .. import db
from ..models import *
from . import admin
from .forms import *


@admin.route('/')
@login_required
def index():
    pass

@admin.route('/login/')
def login():
    pass

@admin.route('/write/')
@login_required
def write():
    pass

@admin.route('/draft/')
@login_required
def draft():
    pass


