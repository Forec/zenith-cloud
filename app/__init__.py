# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：包含了初始化应用函数以及全局变量

from config           import config  # 导入全局设置
from flask            import Flask
from flask_mail       import Mail
from flask_login      import LoginManager
from flask_moment     import Moment
from flask_pagedown   import PageDown
from flask_bootstrap  import Bootstrap
from flask_sqlalchemy import SQLAlchemy
import os, pymysql

pymysql.install_as_MySQLdb()    # 注册 Mysql 接口

bootstrap = Bootstrap()         # 导入 Bootstrap 模板
mail = Mail()                   # 导入邮件处理函数
moment = Moment()               # 导入时间处理函数
db = SQLAlchemy()               # 导入数据库接口
login_manager = LoginManager()  # 导入用户登录处理代理
pagedown = PageDown()           # 导入 Md 渲染接口

# 设置用户 session 的安全性，可为 None/basic/strong
login_manager.session_protection = 'strong'

# 向登录处理代理注册用户登录入口
login_manager.login_view = 'auth.login'

# 创建应用
def create_app(config_name):
    app = Flask(__name__)

    # 应用按指定配置类设置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 将全局变量注册到应用
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    # 注册蓝本
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix = '/auth')

    # 创建文件存储和缓存目录
    try:
        os.mkdir(config[config_name].ZENITH_FILE_STORE_PATH)
    except:
        pass
    try:
        os.mkdir(config[config_name].ZENITH_TEMPFILE_STORE_PATH)
    except:
        pass

    return app