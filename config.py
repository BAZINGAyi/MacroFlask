# config.py

import os


class Config:
    DEBUG = False
    SECRET_KEY = 'default_secret_key'
    DATABASE_URI = 'sqlite:///app.db'


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