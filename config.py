# config.py

import os


class Config:
    DEBUG = False
    SECRET_KEY = 'default_secret_key'
    DATABASE_URI = 'sqlite:///app.db'

    # logging configuration
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
            },
            # Rotating by file size
            # 'app_file': {
            #     'level': 'DEBUG',
            #     'class': 'logging.handlers.RotatingFileHandler',
            #     'formatter': 'standard',
            #     'filename': 'app.log',
            #     'maxBytes': 10485760 / 2,  # 5 MB
            #     'backupCount': 5,
            # },
            'app_file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'standard',
                'filename': 'app.log',
                'when': 'midnight',
                'interval': 1,
                'backupCount': 5,
            },
            'system_file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'standard',
                'filename': 'sys.log',
                'when': 'midnight',
                'interval': 1,
                'backupCount': 5,
            },
        },
        'loggers': {
            'app': {
                'level': 'DEBUG',
                'propagate': False
            },
            'sys': {
                'level': 'DEBUG',
                'propagate': False
            },
        }
    }


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = 'development_secret_key'
    DATABASE_URI = 'mysql+pymysql://root:'
    DATABASE_URI_1 = 'mysql+pymysql://root:'


class TestingConfig(Config):
    DEBUG = True
    SECRET_KEY = 'test_secret_key'
    DATABASE_URI = 'sqlite:///test.db'


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = 'production_secret_key'
    DATABASE_URI = 'postgresql://user:password@localhost/mydatabase'


# 根据环境变量 FLASK_ENV 加载不同的配置
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig  # 默认配置为开发环境
}


def get_config():
    env = os.getenv('FLASK_ENV', 'default')
    return config[env]