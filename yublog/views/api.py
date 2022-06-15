from flask import jsonify, request

from yublog.utils import commit
from yublog.views import api_bp
from yublog.models import View


@api_bp.route("/view/<typ>/<int:id>", methods=["GET"])
def views(typ, id):
    view = View.query.filter_by(type=typ, relationship_id=id).first()
    if not view:
        view = View(type=typ, count=0, relationship_id=id)

    if request.cookies.get(f"{typ}_{id}"):
        return jsonify(count=view.count)
    
    view.count += 1
    commit.add(view)
    resp = jsonify(count=view.count)
    resp.set_cookie(f"{typ}_{id}", "1", max_age=1 * 24 * 60 * 60)
    return resp
