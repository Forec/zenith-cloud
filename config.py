import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = '9d0e91f3372224b3ec7afec2' \
                 '4313e745efcf00ba4a5b767b' \
                 '35b17834d5f26efac197fd69' \
                 'd881dd92e629dbfdc2f1fbf6'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    ZENITH_MAIL_SUBJECT_PREFIX = '[顶点云]'
    ZENITH_MAIL_SENDER = 'cloud-storage@forec.cn'
    ZENITH_FILES_PER_PAGE = 10
    ZENITH_FOLLOWERS_PER_PAGE = 15
    ZENITH_COMMENTS_PER_PAGE = 10
    PROFILE_ZENITH_FILES_PER_PAGE = 6
    ZENITH_MESSAGES_PER_PAGE = 15
    EMAIL_ADMIN ='forec@bupt.edu.cn'
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'work.db')
    MAIL_SERVER = 'smtp.exmail.qq.com'
    MAIL_PORT = 25#465
    MAIL_USE_TLS = True
    MAIL_USERNAME = "cloud-storage@forec.cn"
    MAIL_PASSWORD = "Cloud-Storage-2016"

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'work.db')

config = {
    'development' : DevelopmentConfig,
    'testing' : TestingConfig,
    'default' : DevelopmentConfig
}
