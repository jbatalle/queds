from flask_jwt_extended import get_jwt_identity

from config import settings
from functools import wraps

blacklist = set() # jwt blacklist


def add_token_to_blacklist(jti):
    blacklist.add(jti)


def is_token_blacklisted(jti):
    return jti in blacklist


def filter_by_username(object):
    user_id = get_jwt_identity()
    return object.query.filter(object.user_id == user_id)


def demo_check(f):
    """Checks if the platform is in demo mode"""
    @wraps(f)
    def decorator(*args, **kwargs):
        if settings.DEMO_MODE:
            return {"success": False, "message": "Demo mode"}, 400
        return f(*args, **kwargs)

    return decorator
