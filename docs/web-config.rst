.. _web-config:

Web 服务器全局配置
=====================

在阅读以下内容前，请确保您已经按照 :ref:`web-installation` 正确部署了顶点云 Web 服务器，并位于源码目录下（/path-to/zenith-cloud/web/）。

您可以根据您的环境修改源码目录下的 `config.py` 文件以配置服务器。

样例配置文件
----------------

您从 GitHub 仓库获取的源码中已经包含了一份默认的配置文件，这份配置文件中提供了一个基类 `Config` ，去掉注释后它的内容如下：

.. code-block:: python
   
   class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
                 '9d0e91f3372224b3ec7afec2' \
                 '4313e745efcf00ba4a5b767b' \
                 '35b17834d5f26efac197fd69' \
                 'd881dd92e629dbfdc2f1fbf6'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    ZENITH_MAIL_SUBJECT_PREFIX = '[顶点云]'
    ZENITH_MAIL_SENDER = os.environ.get('ZENITH_MAIL_SENDER') or \
                         'cloud-storage@forec.cn'
    ZENITH_FILES_PER_PAGE = 10
    ZENITH_FOLLOWERS_PER_PAGE = 10
    ZENITH_COMMENTS_PER_PAGE = 10
    PROFILE_ZENITH_FILES_PER_PAGE = 6
    ZENITH_MESSAGES_PER_PAGE = 10
    ZENITH_TEMPFOLDER_LENGTH = 12
    ZENITH_PATH_SEPERATOR = '\\'
    ZENITH_FILE_STORE_PATH = 'G:\\Cloud\\'
    ZENITH_TEMPFILE_STORE_PATH = ZENITH_FILE_STORE_PATH + \
                             'TEMP' + ZENITH_PATH_SEPERATOR
    ZENITH_FOLDER_ZIP_SUFFIX = 'zenith'
    ZENITH_INVALID_INFFIX = ['//', '\\', '/', '..', '%', '^', '&',
                             '*', '$', '!', '+', '#']
    EMAIL_ADMIN ='forec@bupt.edu.cn'
    ZENITH_RANDOM_PATH_ELEMENTS = ['a', 'b', 'c', 'd', 'e', 'f', 'g',
                                   'h', 'i', 'j', 'k', 'l', 'm', 'n',
                                   'o', 'p', 'q', 'r', 's', 't', 'u',
                                   'v', 'w', 'x', 'y', 'z', '1', '2',
                                   '3', '4', '5', '6', '7', '8', '9',
                                   '0', 'A', 'B', 'C', 'D', 'E', 'F',
                                   'G', 'H', 'I', 'J', 'K', 'L', 'M',
                                   'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                                   'U', 'V', 'W', 'X', 'Y', 'Z']
    ZENITH_VALID_THUMBNAIL = ['.jpg', '.png', '.ico', '.jpeg']
    ZENITH_VALID_THUMBNAIL_SIZE = 512 * 1024

	
样例配置文件中，每项均有对应注释，您也可以查看下面的 :ref:`web-config-detailed` 了解每一项的具体功能。

.. _web-config-detailed:

样例文件详细解释
-------------------

配置文件中 `Config` 类的每一项对应配置如下：

1. ``SECRET_KEY`` ：用于服务器生成 token 使用的密钥，不可泄露，应当设置在服务器部署系统的环境变量中
2. ``SQLALCHEMY_COMMIT_ON_TEARDOWN`` ：为 ``True`` 时服务器终止运行时向数据库提交变动
3. ``SQLALCHEMY_TRACK_MODIFICATIONS`` ：为 ``True`` 时数据库将追踪服务器对数据的改动
4. ``ZENITH_MAIL_SUBJECT_PREFIX`` ：服务器向用户发送的验证邮件的主题前缀
5. ``ZENITH_MAIL_SENDER`` ：服务器向用户发送验证邮件使用的邮箱
6. ``ZENITH_FILES_PER_PAGE`` ：Index 页面每页显示的文件数量
7. ``ZENITH_FOLLOWERS_PER_PAGE`` ：关注着界面每页显示的用户数量
8. ``ZENITH_COMMENTS_PER_PAGE`` ：文件详细页面每页显示的评论数量
9. ``PROFILE_ZENITH_FILES_PER_PAGE`` ：用户资料页每页显示的文件数量
10. ``ZENITH_MESSAGES_PER_PAGE`` ：用户消息页面每页显示的消息数量
11. ``ZENITH_TEMPFOLDER_LENGTH`` ：服务器在临时存储文件时生成的随机目录名长度
12. ``ZENITH_PATH_SEPERATOR`` ：服务器所属文件系统的目录分隔符，Windows为 *\* ，Linux 为 */*
13. ``ZENITH_FILE_STORE_PATH`` ：服务器用于存储用户文件的路径
14. ``ZENITH_TEMPFILE_STORE_PATH`` ：服务器生成的随机目录的根路径，默认为文件存储路径下的 TMEP 文件夹
15. ``ZENITH_FOLDER_ZIP_SUFFIX`` ：用户上传目录压缩包时使用的后缀，使用此后缀的文件会被视作一个目录
16. ``ZENITH_INVALID_INFFIX`` ：此列表中的字符不能出现在用户文件名中，否则视为不合法
17. ``EMAIL_ADMIN`` ：管理员账户使用的邮箱
18. ``ZENITH_RANDOM_PATH_ELEMENTS`` ：服务器生成的随机路径包含的元素
19. ``ZENITH_VALID_THUMBNAIL`` ：服务器允许用户上传的头像后缀名
20. ``ZENITH_VALID_THUMBNAIL_SIZE`` ：服务器允许用户上传的最大头像大小

`Config` 类仅仅是配置类的基类，你需要扩展此类才可完成配置。在 `config.py` 文件中，存在一些默认的 `Config` 子类，如 `LinuxConfig` 、 `WindowsConfig` 。

下面简单介绍 `LinuxConfig` 并以一个环境为例讲解如何配置。

`LinuxConfig` 类的内容如下，它是我（ `Forec`_ ）在我的云主机部署 Web 服务器时使用的配置类：

.. code-block:: python
   
   class LinuxConfig(Config):
    ZENITH_PATH_SEPERATOR = '/'    # 服务器所属文件系统的目录分隔符
    ZENITH_FILE_STORE_PATH = '/root/work/cloud/Cloud/'  # 服务器存储用户文件的路径
    ZENITH_TEMPFILE_STORE_PATH = ZENITH_FILE_STORE_PATH + \
                                 'TEMP' + ZENITH_PATH_SEPERATOR
    ZENITH_SERVER_ADDRESS = 'cloud.forec.cn' # 服务器部署的域名/IP地址
    SERVER_NAME = ZENITH_SERVER_ADDRESS
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'work.db')
    MAIL_SERVER = 'smtp.exmail.qq.com'
    MAIL_PORT = 25 # SSL is 465
    MAIL_USE_TLS = True
    MAIL_USERNAME = "cloud-storage@forec.cn"
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

可以看出， `LinuxConfig` 类重写了 `Config` 类的几项，同时添加了几个新的选项。新选项介绍如下：

1. ``ZENITH_SERVER_ADDRESS`` ：服务器部署使用的域名/IP地址
2. ``SERVER_NAME`` ：Flask 中的 *url_for* 函数使用的服务器名，通常保持和 *SERVER_NAME* 一致
3. ``SQLALCHEMY_DATABASE_URI`` ：服务器使用的数据库所在的路径
4. ``MAIL_SERVER`` ：服务器发送邮件使用的邮箱服务器
5. ``MAIL_PORT`` ：服务器使用 stmp 协议的端口号，通常为 25。使用 SSL 时设置为 465 但这取决于 *MAIL_SERVER* 是否支持 SSL
6. ``MAIL_USE_TLS`` ：是否启用安全连接发送邮件，通常设置为 ``True`` 
7. ``MAIL_USERNAME`` ：服务器发送邮件使用的邮箱帐号，通常和 *ZENITH_MAIL_SENDER* 保持一致
8. ``MAIL_PASSWORD`` ：服务器发送邮件使用的邮箱帐号的密码，通常保存在环境变量中

.. _web-config-example:

下面通过一个实例环境解释如何配置。

例如，在安装 Ubuntu 16.04 的主机上部署 Web 服务器，可参考的配置文件如下（使用扩展类）：

.. code-block:: python
   
   class MyConfig(Config):
    ZENITH_PATH_SEPERATOR = '/'
    ZENITH_FILE_STORE_PATH = '/home/cloud/'  # 将用户上传文件存储在 /home/cloud 中
    ZENITH_TEMPFILE_STORE_PATH = ZENITH_FILE_STORE_PATH + \
                                 'TEMP' + ZENITH_PATH_SEPERATOR
    ZENITH_SERVER_ADDRESS = 'myaddress.my.io' # 自定义的域名，你需要先购买此域名并且映射到部署主机上
    SERVER_NAME = ZENITH_SERVER_ADDRESS
    SQLALCHEMY_DATABASE_URI = '/usr/local/cloud/mydb.db'
    	# 设置数据库为 /usr/local/cloud/mydb.db
    MAIL_SERVER = 'smtp.163.com'	# 使用 163 邮箱
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USERNAME = "mycloud@163.com"
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '123456'
    	# 在环境变量中添加密码，若环境变量未找到对应值则使用 123456
    	
.. _web-config-add:

添加自定义配置类到表
------------------------

在已经定义了自定义配置类后，你需要将自定义配置类添加到表驱动中以使 :ref:`web-app-factory` 能根据我的配置类生成服务器实例。

在 `config.py` 中，有一个名为 `config` 的字典如下：

.. code-block:: python

   config = {
    'development' : DevelopmentConfig,      # 开发环境
    'linux': LinuxConfig,                   # 提供的 Linux 模板环境
    'windows': WindowsConfig,               # 提供的 Windows模板环境
    'testing' : TestingConfig,              # 测试环境
    'default' : DevelopmentConfig           # 默认为开发环境
    }
    
你需要添加自己的自定义配置类到此表中，如添加 ``'myconfig': MyConfig`` 。之后，修改 `manage.py` 中的第 21 行 ``app = create_app('default')`` 为 ``app = create_app('myconfig')`` 即可。
   
接下来请您阅读 :ref:`web-quickstart` 。

.. _Forec: http://forec.cn
