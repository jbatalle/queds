import os
import importlib
import importlib.util
import logging
import logging.config

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

        self.TELEGRAM_CONFIG = {
            "token": "",
            "chat": None
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

        self.LOG_LEVEL = logging.DEBUG
        self.std_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        self.enabled_handlers = ['default']
        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': False,
            'filters': {
            },
            'formatters': {
                'standard': {
                    'format': self.std_format
                }
            },
            'handlers': {
                'default': {
                    'level': self.LOG_LEVEL,
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler',
                    'filters': []
                },
            },
            'loggers': {
                '': {
                    'handlers': self.enabled_handlers,
                    'level': self.LOG_LEVEL,
                    'propagate': True
                },
                'urllib3': {
                    'handlers': self.enabled_handlers,
                    'level': logging.WARNING
                },
                'requests': {  # disable requests library logging
                    'handlers': self.enabled_handlers,
                    'level': logging.WARNING
                },
                'sqlalchemy': {
                    'handlers': self.enabled_handlers,
                    'level': logging.ERROR
                },
                'sqlalchemy.engine': {
                    'handlers': self.enabled_handlers,
                    'level': logging.CRITICAL
                },
            }
        })


env = os.environ.setdefault(ENVIRONMENT_VARIABLE, "config.local")

settings = Settings(env)
