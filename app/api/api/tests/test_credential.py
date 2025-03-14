import unittest
from app import app, db
from mock import patch, create_autospec
from models.system import User


class BaseTestClass(unittest.TestCase):
    def setUp(self):
        self.app = app#create_app(settings_module="config.testing")
        self.client = self.app.test_client()
        # Crea un contexto de aplicación
        with self.app.app_context():
            # Crea las tablas de la base de datos
            # db.create_all()
            print("Create all")

    def tearDown(self):
        with self.app.app_context():
            # Elimina todas las tablas de la base de datos
            #db.session.remove()
            #db.drop_all()
            print("Delete all")


class CredentialTestCase(BaseTestClass):

    # @patch('models.system.User.check_password')
    @patch('models.system.User.get_by_email')
    def test_create_credential(self, mock):
        data = {
            "parameters": [
                {
                    "value": "value1",
                    "credential_type_id": 0
                }
            ],
            "encrypt_password": "password"
        }
        mock.return_value = User(email="mail", password="blabla")
        res = self.client.post('/api/entities/accounts/1/credentials', json=data)
        response = res.get_json()

        self.assertEqual(200, res.status_code)
        self.assertIn('token', response)
