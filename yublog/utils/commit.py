from yublog.extensions import db


def commit(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        db.session.commit()

    return wrapper


@commit
def add(model):
    db.session.add(model)


@commit
def delete(model):
    db.session.delete(model)
