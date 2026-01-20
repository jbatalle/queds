import logging
import time
from flask_restx import Resource, fields, Namespace
from models.system import (
    Account,
    Entity,
    User,
    EntityCredentialType,
    AccountCredentialParam,
)
from flask import request, jsonify, render_template, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api import filter_by_username, demo_check
from services.queue import queue_read
from models.cryptography import AESCipher
from sqlalchemy.dialects.postgresql import insert
from config import settings
from services.redis import RedisClient as RedisClientClass

redisClient = RedisClientClass()
import json


log = logging.getLogger(__name__)

namespace = Namespace("entities")

system_account = namespace.model('AccountModel', {
    "name": fields.String(required=True, min_length=1, max_length=32),
    "entity_id": fields.Integer(required=True),
    "currency": fields.String(required=True, min_length=1, max_length=10)
})

credential = namespace.model('CredentialModel', {
    "value": fields.String(required=True, min_length=1, max_length=180),
    "credential_type_id": fields.Integer(required=True),
})

credentials_registration = namespace.model('AccountCredentialParams', {
    'parameters':  fields.List(fields.Nested(credential)),
    "encrypt_password": fields.String(required=True, min_length=1, max_length=180),
})

account_reader = namespace.model('AccountReader', {
    "encrypt_password": fields.String(required=True, min_length=1, max_length=32),
})

account_validation = namespace.model(
    "AccountValidation",
    {
        "encrypt_password": fields.String(required=True, min_length=1, max_length=32),
        "validation_code": fields.String(required=True, min_length=1, max_length=32),
    },
)


@namespace.route('/')
class List(Resource):

    def get(self):
        """Returns all entities."""
        result = Entity.query.all()
        items = []
        for r in result:
            items.append(r.json)
        return jsonify(items)


@namespace.route('/accounts')
class AccountList(Resource):

    @jwt_required()
    def get(self):
        """Returns all account accounts from authenticated user."""
        user_id = get_jwt_identity()
        accounts = Account.query.filter(Account.user_id == user_id)
        items = []
        for r in accounts:
            item = r.json
            item['entity_type'] = r.entity.type
            item['entity_name'] = r.entity.name
            items.append(item)
        return jsonify(items)

    @namespace.expect(system_account, validate=True)
    @demo_check
    @jwt_required()
    def post(self):
        """Create an account."""
        user_id = get_jwt_identity()

        content = request.get_json(silent=True)
        # entity = Entity.query.filter(Entity.id == content['entity_id']).one()

        account = Account(
            name=content['name'],
            entity_id=content['entity_id'],
            user_id=user_id,
            currency=content['currency'],
            balance=0,
            virtual_balance=0,
            allows_csv=content.get('allows_csv', False)
        )
        try:
            account.save()
        except Exception as e:
            log.error("Error saving account: {0}".format(e))
            return {'message': 'Something went wrong'}, 500

        log.info("Account created")
        return {'id': account.id}


@namespace.route('/accounts/<int:id>')
class AccountElement(Resource):

    @demo_check
    @jwt_required()
    def put(self, id):
        """Update account."""
        accounts = filter_by_username(Account).all()
        if id not in [a.id for a in accounts]:
            return {'message': 'Unable to delete the account!'}, 400

        log.debug(f"Request update of account {id}")
        account = filter_by_username(Account).filter(Account.id == id).one()

        log.info(f"Found account: {account.id}. Trying to update the account")
        content = request.get_json(silent=True)
        try:
            account.name = content['name']
            account.currency = content['currency']
            account.save()
        except Exception as e:
            log.error(f"Unable to update: {e}")

        log.debug("Account updated")
        return {'message': 'Account updated!'}

    @demo_check
    @jwt_required()
    def delete(self, id):
        """Deletes an account and the related items."""
        accounts = filter_by_username(Account).all()
        if id not in [a.id for a in accounts]:
            return {'message': 'Unable to delete the account!'}, 400

        log.debug(f"Request deletion of account {id}")
        account = filter_by_username(Account).filter(Account.id == id).one()

        log.info(f"Found account: {account.id}. Trying to delete the account and related models")
        try:
            account.destroy()
        except Exception as e:
            log.error(f"Unable to delete: {e}")

        log.debug("Account deleted")
        return {'message': 'Account deleted!'}


@namespace.route('/<int:id>/credentials')
class CredentialList(Resource):

    def get(self, id):
        """Returns credentials by entity."""
        result = EntityCredentialType.query.filter(EntityCredentialType.entity_id == id).all()
        items = []
        for r in result:
            item = r.json
            items.append(item)
        return jsonify(items)


@namespace.route('/accounts/<int:id>/credentials')
class AccountCredentials(Resource):

    @namespace.expect(credentials_registration, validate=True)
    @demo_check
    @jwt_required()
    def post(self, id):
        account = filter_by_username(Account).filter(Account.id == id).one()

        content = request.get_json(silent=True)
        encrypt_password = content['encrypt_password']
        cipher = AESCipher(encrypt_password)
        try:
            for c in content['parameters']:
                encrypted_value = cipher.encrypt(c['value'])
                cred_param = AccountCredentialParam(
                    account_id=account.id,
                    credential_type_id=c['credential_type_id'],
                    value=encrypted_value.decode()
                )
                values = {
                    "account_id": account.id,
                    "credential_type_id": c['credential_type_id'],
                    "value": encrypted_value.decode()
                }
                stmt = insert(AccountCredentialParam).values(values)
                # stmt = stmt.on_conflict_do_update(constraint="cred_type_account_uc", set_={"value": stmt.excluded.value})
                stmt = stmt.on_conflict_do_update(
                    index_elements=["credential_type_id", "account_id"],
                    set_={"value": stmt.excluded.value}
                )

                cred_param.update_on_conflict(stmt)
        except Exception as e:
            log.error("Error saving account credential: {0}".format(e))
            return {'message': 'Something went wrong'}, 500

        log.debug("Account credential created")
        return {'message': 'Credentials created!'}


@namespace.route('/accounts/<int:id>/read')
class AccountReader(Resource):

    @namespace.expect(account_reader, validate=True)
    @demo_check
    @jwt_required()
    def post(self, id):
        user_id = get_jwt_identity()
        account = filter_by_username(Account).filter(Account.id == id).one()
        credentials = AccountCredentialParam.query.filter(
            AccountCredentialParam.account_id == id
        ).all()

        if not credentials:
            return {'message': 'Account without credentials!'}, 400

        content = request.get_json(silent=True)
        encrypt_password = content['encrypt_password']
        cipher = AESCipher(encrypt_password)
        data = {
            "entity_type": account.entity.type,
            "entity_name": account.entity.name,
            "account_id": account.id
        }
        for c in credentials:
            try:
                decrypted_value = cipher.decrypt(c.value)
            except:
                return {'message': 'Invalid passphrase!'}, 400

            if not decrypted_value:
                log.warning("Decrypted value is empty!")
                return {'message': 'Invalid passphrase!'}, 400

            # Deserialize JSON if the credential type is one that stores JSON
            credential_type_name = c.credential_type.cred_type.lower()
            if credential_type_name in ['device_token', 'cookie_token']:
                try:
                    decrypted_value = json.loads(decrypted_value)
                except (json.JSONDecodeError, ValueError):
                    # If it's not valid JSON, keep it as string (backward compatibility)
                    pass

            data[credential_type_name] = decrypted_value

        queue_name = None
        if account.entity.type == Entity.Type.BROKER:
            queue_name = 'broker'
        elif account.entity.type == Entity.Type.EXCHANGE:
            queue_name = 'crypto'

        log.info(f"Queuing read to queue {queue_name}")
        read_data = queue_read(data, queue_name)
        if not read_data:
            return {'message': 'Unable to enqueue the read!'}, 400

        # Store "reading" status immediately so frontend knows the read started
        try:
            status_key = f"validation_status:account_{id}"
            import time
            status_json = json.dumps({
                "status": "reading",
                "message": f"Reading account {account.name}...",
                "account_id": id,
                "timestamp": time.time()
            })
            redisClient.client.set(status_key, status_json, ex=300)  # Expire after 5 minutes
            log.info(f"Stored reading status for account {id}")
        except Exception as e:
            log.warning(f"Failed to store reading status: {e}")

        log.debug("Account credential check")

        return {
            "status": "processing",
            "message": f"Reading account {account.name}...",
            "account_id": account.id,
        }


@namespace.route("/accounts/<int:id>/read-status")
class AccountReadStatus(Resource):
    @jwt_required()
    def get(self, id):
        """Poll endpoint to check read status and validation requirements"""
        current_user_id = get_jwt_identity()

        # Verify account belongs to user
        account = filter_by_username(Account).filter(Account.id == id).first()
        # account = Account.query.filter(Account.id == id).one()
        if not account:
            return {"error": "Account not found"}, 404

        # Check Redis for validation status
        try:
            status_key = f"validation_status:account_{id}"
            status_data = redisClient.get(status_key)

            if status_data:
                status = status_data
                log.info(f"Validation status for account {id}: {status.get('status')}")

                # If validation completed successfully, return it and clear the status
                if status.get("status") == "success":
                    # Return success status, but delete it immediately so next poll gets "reading"
                    redisClient.delete(status_key)
                    log.info(f"Deleted success status for account {id} after returning it")
                    return jsonify(status)
                
                # If validation_required status is older than 30 seconds, consider it stale
                # and return 'reading' instead (in case worker is processing)
                if status.get("status") == "validation_required":
                    timestamp = status.get("timestamp", 0)
                    age_seconds = time.time() - timestamp
                    if age_seconds > 30:
                        log.info(f"Validation status for account {id} is stale ({age_seconds:.1f}s old), returning 'reading'")
                        return jsonify({"status": "reading", "message": "Reading account..."})

                return jsonify(status)

            # No validation status in Redis - read is either in progress or completed successfully
            # Return 'reading' status to indicate no validation requirement yet
            return jsonify({"status": "reading", "message": "Reading account..."})

        except Exception as e:
            log.error(f"Error checking validation status for account {id}: {e}")
            return jsonify(
                {"status": "error", "message": "Unable to check status"}
            ), 500


@namespace.route("/accounts/<int:id>/validate")
class AccountValidation(Resource):
    @namespace.expect(account_validation, validate=True)
    @demo_check
    @jwt_required()
    def post(self, id):
        """Handle device validation for broker accounts"""
        current_user_id = get_jwt_identity()
        account = filter_by_username(Account).filter(Account.id == id).one()
        credentials = AccountCredentialParam.query.filter(
            AccountCredentialParam.account_id == id
        ).all()

        if not credentials:
            return {"message": "Account without credentials!"}, 400

        content = request.get_json(silent=True)
        encrypt_password = content["encrypt_password"]
        validation_code = content["validation_code"]
        cipher = AESCipher(encrypt_password)
        data = {
            "entity_type": account.entity.type,
            "entity_name": account.entity.name,
            "account_id": account.id,
            "totp_code": validation_code,
            "encrypt_password": encrypt_password,
            "user_id": current_user_id,
        }

        for c in credentials:
            try:
                decrypted_value = cipher.decrypt(c.value)
            except:
                return {"message": "Invalid passphrase!"}, 400

            if not decrypted_value:
                log.warning("Decrypted value is empty!")
                return {"message": "Invalid passphrase!"}, 400

            # Deserialize JSON if the credential type is one that stores JSON
            credential_type_name = c.credential_type.cred_type.lower()
            if credential_type_name in ['device_token', 'cookie_token']:
                try:
                    decrypted_value = json.loads(decrypted_value)
                except (json.JSONDecodeError, ValueError):
                    # If it's not valid JSON, keep it as string (backward compatibility)
                    pass

            data[credential_type_name] = decrypted_value

        queue_name = None
        if account.entity.type == Entity.Type.BROKER:
            queue_name = "broker_validation"
        elif account.entity.type == Entity.Type.EXCHANGE:
            queue_name = "crypto_validation"

        log.info(f"Queuing validation to queue {queue_name}")
        read_data = queue_read(data, queue_name)
        if not read_data:
            return {"message": "Unable to enqueue the validation!"}, 400

        # Store "reading" status immediately with fresh timestamp and new message
        try:
            status_key = f"validation_status:account_{id}"
            import time
            status_json = json.dumps({
                "status": "reading",
                "message": "Validating OTP code...",
                "account_id": id,
                "timestamp": time.time()
            })
            redisClient.client.set(status_key, status_json, ex=300)  # Expire after 5 minutes
            log.info(f"Stored reading status for account {id} after OTP submission")
        except Exception as e:
            log.warning(f"Failed to store reading status after OTP submission: {e}")

        log.debug("Account validation submitted")
        return {"message": f"Validating account {account.name}!"}


@namespace.route("/stats")
class AccountStats(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        accounts = (
            Account.query.with_entities(Account.id)
            .filter(Account.user_id == user_id)
            .all()
        )

        # TODO:
        # values required: current portfolio wallet, current gain, total_invested
        # call stock and crypto wallet

        stats = {"portfolio_value": 0, "buy": 0, "sell": 0, "gain": 0}

        return stats


@namespace.route("/upload_csv")
class UploadCSV(Resource):

    def get(self):
        accounts = Account.query.all()
        # TODO: create templates models, return fields for each entity
        return make_response(
            render_template(
                "upload_csv.html", fields=["amount", "price"], accounts=accounts
            ),
            200,
        )

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        account_id = request.form.get(
            "account_id"
        )  # Adjust key based on your form field name
        log.info(f"Processing CSV file. Account ID: {account_id}")
        uploaded_file = request.files.get("file")

        if not uploaded_file:
            return {'message': 'No file uploaded!'}, 400

        account = filter_by_username(Account).filter(Account.id == account_id).one()

        # enqueue order
        content = uploaded_file.read().decode("utf-8")
        data = {
            "entity_type": account.entity.type,
            "entity_name": account.entity.name,
            "account_id": account.id,
            "user_id": user_id,
            "data": content
        }

        queue_name = "csv"
        log.info(f"Queuing read to queue {queue_name}")
        read_data = queue_read(data, queue_name)
        if not read_data:
            return {'message': 'Unable to enqueue the read!'}, 400

        log.debug("Processing the CSV...")
        return {'message': f'Processing the csv for the account {account.name}!'}
