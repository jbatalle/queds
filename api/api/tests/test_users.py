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


class PostModelTestCase(BaseTestClass):

    # @patch('models.system.User.check_password')
    @patch('models.system.User.get_by_email')
    def test_login(self, mock):
        data = {
            "email": "string2",
            "password": "blabla"
        }
        mock.return_value = User(email="mail", password="blabla")
        res = self.client.post('/api/users/login', json=data)
        response = res.get_json()

        self.assertEqual(200, res.status_code)
        self.assertIn('token', response)

    @patch('models.system.User.get_by_email')
    def test_login_invalid_pwd(self, mock):
        data = {
            "email": "string2",
            "password": "different pass"
        }
        mock.return_value = User(email="mail", password="blabla")
        res = self.client.post('/api/users/login', json=data)
        response = res.get_json()

        self.assertEqual(400, res.status_code)
        self.assertIn('message', response)
        self.assertEqual(response['message'], "Wrong credentials.")

    @patch('models.system.User.get_by_email')
    def test_register_exists(self, mock):
        data = {
              "username": "string",
              "email": "string",
              "password": "string"
            }
        mock.return_value = User(email="mail", password="blabla")
        res = self.client.post('/api/users/register', json=data)
        response = res.get_json()

        self.assertEqual(400, res.status_code)
        self.assertIn('message', response)
        self.assertEqual(response['message'], "Email already taken.")

    @patch('models.system.User.save')
    @patch('models.system.User.get_by_email')
    def test_register_no_exists(self, mock, mock_save):
        data = {
              "username": "string",
              "email": "string",
              "password": "string"
            }
        mock.return_value = None
        mock_save.return_value = None
        res = self.client.post('/api/users/register', json=data)
        response = res.get_json()

        self.assertEqual(200, res.status_code)
        self.assertIn('message', response)
        self.assertEqual(response['message'], "The user was successfully registered.")

    @patch('config.settings.DEMO_MODE')
    @patch('models.system.User.save')
    @patch('models.system.User.get_by_email')
    def test_register_demo_mode(self, mock, mock_save, mock_setting):
        mock_setting.return_value = True

        data = {
              "username": "string",
              "email": "string",
              "password": "string"
            }
        mock.return_value = None
        mock_save.return_value = None
        res = self.client.post('/api/users/register', json=data)
        response = res.get_json()

        self.assertEqual(400, res.status_code)
        self.assertIn('message', response)
        self.assertEqual(response['message'], "Demo mode")

    def atest_title_slug(self):
        res = self.client.get('/api/crypto/accounts')
        self.assertEqual(401, res.status_code)
        self.assertIn('login', res.location)
