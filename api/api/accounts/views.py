import logging
from flask_restx import Resource, fields, Namespace
from models.system import Account, Entity, User, EntityCredentialType, AccountCredentialParam
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from api import filter_by_username, demo_check
from services.queue import queue_read
from models.cryptography import AESCipher
from sqlalchemy.dialects.postgresql import insert


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
        result = filter_by_username(Account).all()
        items = []
        for r in result:
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
        current_user_email = get_jwt_identity()
        user_id = User.find_by_email(current_user_email).id

        content = request.get_json(silent=True)

        account = Account(
            name=content['name'],
            entity_id=content['entity_id'],
            user_id=user_id,
            currency=content['currency'],
            balance=0,
            virtual_balance=0
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
    def delete(self, id):
        """Deletes and account and the related items."""
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
                stmt = stmt.on_conflict_do_update(constraint="cred_type_account_uc",
                                                  set_={
                                                      "value": stmt.excluded.value
                                                  })
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
        account = filter_by_username(Account).filter(Account.id == id).one()
        credentials = AccountCredentialParam.query.filter(AccountCredentialParam.account_id==id).all()

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

            data[c.credential_type.cred_type.lower()] = decrypted_value

        queue_name = None
        if account.entity.type == Entity.Type.BROKER:
            queue_name = 'broker'
        elif account.entity.type == Entity.Type.EXCHANGE:
            queue_name = 'crypto'

        log.info(f"Queuing read to queue {queue_name}")
        read_data = queue_read(data, queue_name)
        if not read_data:
            return {'message': 'Unable to enqueue the read!'}, 400

        log.debug("Account credential check")
        return {'message': f'Reading account {account.name}!'}
