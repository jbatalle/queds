import os
import importlib
import importlib.util

ENVIRONMENT_VARIABLE = "BACKEND_SETTINGS"


class Settings:
    def __init__(self, settings_module='config.local'):
        self._settings_module = settings_module
        self.environment = self._settings_module.split('.')[-1].lower()
        print(f"Loading settings for env: {self.environment}")

        self.DEMO_MODE = False
        self.DEBUG = False
        self.JWT_SECRET_KEY = 'tQjMCau8W939'

        self.SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
        self.BCRYPT_LOG_ROUNDS = 4
        self.SQL_CONF = {
            'user': 'queds',
            'password': '',
            'host': '',
            'port': '5432',
            'database': 'queds',
            'options': {}
        }

        self.REDIS = {
            'host': '0.0.0.0',
            'port': 6379
        }

        mod = importlib.import_module(settings_module)
        for setting in dir(mod):
            if setting.startswith('_'):
                continue

            setting_value = getattr(mod, setting)

            if hasattr(self, setting):
                if isinstance(setting_value, dict):
                    dst = getattr(self, setting)
                    dst.update(setting_value)
                else:
                    setattr(self, setting, setting_value)


env = os.environ.setdefault(ENVIRONMENT_VARIABLE, "config.local")

settings = Settings(env)
