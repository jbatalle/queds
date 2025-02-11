from flask import request
from datetime import datetime, timezone, timedelta
from flask_restx import Resource, fields, Namespace
from models.system import Account, Entity, User
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from api import demo_check

namespace = Namespace("users")

signup_model = namespace.model('SignUpModel', {
    "email": fields.String(required=True, min_length=4, max_length=64),
    "password": fields.String(required=True, min_length=4, max_length=16),
    "password_confirmation": fields.String(required=True, min_length=4, max_length=16)
})

login_model = namespace.model('LoginModel', {
    "email": fields.String(required=True, min_length=4, max_length=64, default="demo@queds.com"),
    "password": fields.String(required=True, min_length=4, max_length=16, default="supersecret")
})

user_edit_model = namespace.model('UserEditModel', {
    "userID": fields.String(required=True, min_length=1, max_length=32),
    "username": fields.String(required=True, min_length=2, max_length=32),
    "email": fields.String(required=True, min_length=4, max_length=64)
})


@namespace.route('/register')
class Register(Resource):
    """
       Creates a new user
    """

    @namespace.expect(signup_model, validate=True)
    @demo_check
    def post(self):

        req_data = request.get_json()
        _email = req_data.get("email")
        _password = req_data.get("password")
        _password2 = req_data.get("password_confirmation")

        if _password != _password2:
            return {"success": False, "message": "Different password."}, 400

        user_exists = User.get_by_email(_email)
        if user_exists:
            return {"success": False, "message": "Email already taken."}, 400

        new_user = User(email=_email, password=_password)
        new_user.save()

        return {"success": True,
                "userID": new_user.id,
                "message": "The user was successfully registered."}, 200


@namespace.route('/login')
class Login(Resource):
    """
       Login user
    """

    @namespace.expect(login_model, validate=True)
    def post(self):

        req_data = request.get_json()
        _email = req_data.get("email")
        _password = req_data.get("password")

        user_exists = User.get_by_email(_email)

        if not user_exists:
            return {"success": False, "message": "This email does not exist."}, 400

        if not user_exists.check_password(_password):
            return {"success": False, "message": "Wrong credentials."}, 400

        expires = timedelta(minutes=60*24*7)
        access_token = create_access_token(identity=user_exists.id, expires_delta=expires)
        refresh_token = create_refresh_token(identity=user_exists.id)

        # TODO: get base currency from model

        return {"success": True,
                "token": access_token,
                "base_currency": "EUR"
                }, 200


@namespace.route('/edit')
class EditUser(Resource):
    """
       Edits User's username or password
    """

    @namespace.expect(user_edit_model)
    @demo_check
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        req_data = request.get_json()

        _new_username = req_data.get("username")
        _new_email = req_data.get("email")

        return {"success": "notImplemented"}, 400

        if _new_username:
            self.update_username(_new_username)

        if _new_email:
            self.update_email(_new_email)

        self.save()

        return {"success": True}, 200


@namespace.route('/logout')
class LogoutUser(Resource):
    """
       Logs out User
    """

    @jwt_required()
    def post(self):
        # TODO: remove token; for the moment the cookie is remove from front but not disabled
        return {"success": True}, 200

        _jwt_token = request.headers["authorization"]

        jwt_block = JWTTokenBlocklist(jwt_token=_jwt_token, created_at=datetime.now(timezone.utc))
        jwt_block.save()

        self.set_jwt_auth_active(False)
        self.save()

        return {"success": True}, 200


