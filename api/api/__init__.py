# -*- encoding: utf-8 -*-
from flask_jwt_extended import get_jwt_identity
from models.system import User

from config import settings
from functools import wraps


def filter_by_username(object):
    username = get_jwt_identity()
    user_id = User.find_by_email(username).id
    return object.query.filter(object.user_id == user_id)


def demo_check(f):
    """Checks if the platform is in demo mode"""
    @wraps(f)
    def decorator(*args, **kwargs):
        if settings.DEMO_MODE:
            return {"success": False, "message": "Demo mode"}, 400
        return f(*args, **kwargs)

    return decorator
