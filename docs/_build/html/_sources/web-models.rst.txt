.. _web-models:

模型介绍
==========

此部分文档主要介绍顶点云 Web 服务器使用的数据库格式和模型。

.. _web-models-database:

数据库
----------

顶点云 Web 服务器使用的数据库与 :ref:`zenith-app` 使用的数据库兼容。您可以直接阅读 :ref:`app-models-database` 来查看数据库格式。


.. _web-models-class:

内置自定义类
----------------

此部分文档主要介绍顶点云 Web 服务器定义的几个模型。用户模型的定义均位于 `web/app/models.py` 中，包括：

* `User` ：用户类
* `Message` ：用户聊天消息类，与 :ref:`app-models-database-cmessages` 保持一致
* `Follow` ：第三方表，用于存储用户之间的多对多关注关系
* `Permission` ：用户权限模型
* `Role` ：用户身份模型
* `CFILE` ：实体文件模型，与 :ref:`app-models-database-cfile` 保持一致
* `File` ：用户资源记录模型，与 :ref:`app-models-database-ufile` 保持一致
* `Comment` ：用户评论类
* `Pagination` ：自定义文件分页模型，用于在列表过长时分页显示，该模型允许从列表构造分页器，可替代 SQLAlchemy 提供的 `Pagination` 类
* `AnonymousUser` ：匿名用户模型，提供给 `flask_login` 作为未登录用户实例

下面将简单介绍每个模型提供的方法。

.. _web-models-user:

用户类
>>>>>>>>>>>>

`User` 模型同时继承了 `UserMixin` 和 SQLAlchemy 数据库模型，它具有如下元素：

.. code-block:: python

    # 用户 id
    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64),unique=True)
    # 用户密码的加盐哈希值
    password_hash = db.Column(db.String(32))
    # 用户创建时间
    created = db.Column(db.DateTime, default = datetime.utcnow)
    # 用户是否已激活邮箱
    confirmed = db.Column(db.Boolean, default= False)
    # 用户昵称
    nickname = db.Column(db.String(64))
    # 用户头像链接
    avatar_hash = db.Column(db.String(32))
    # 用户个人介绍
    about_me = db.Column(db.Text)
    # 与 created 相同，adapter
    member_since = db.Column(db.DateTime,
                             default = datetime.utcnow)
    # 上次登录时间
    last_seen = db.Column(db.DateTime,
                          default = datetime.utcnow)
    # 用户积分
    score = db.Column(db.Integer, default = 20)
    # 用户角色 id（管理员/审核员/普通用户等）
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # 用户拥有的文件，外链 File 表
    files = db.relationship('File', backref='owner', lazy = 'dynamic')
    # 用户发布的评论，外链 Comment 表
    comments = db.relationship('Comment',backref='author', lazy='dynamic')
    # 此用户关注的人，外链 Follow 表
    followed = db.relationship('Follow',
                               # 指定外键
                               foreign_keys= [Follow.follower_id],
                               # 回调变量
                               backref = db.backref('follower', lazy='joined'),
                               lazy = 'dynamic',
                               # 当用户删除时连带删除全部记录
                               cascade='all, delete-orphan')
    # 此用户的关注者，外链 Follow 表
    followers = db.relationship('Follow',
                               foreign_keys= [Follow.followed_id],
                               backref = db.backref('followed', lazy='joined'),
                               lazy = 'dynamic',
                               cascade='all, delete-orphan')
    # 用户发送过的消息
    sendMessages = db.relationship('Message',
                                   backref='sender',
                                   lazy='dynamic',
                                   foreign_keys = [Message.sendid])
    # 用户接收到的消息
    recvMessages = db.relationship('Message',
                                   backref='receiver',
                                   lazy='dynamic',
                                   foreign_keys = [Message.targetid])
    # 用户已使用的网盘空间，单位为字节
    used = db.Column(db.Integer, default=0)
    # 用户最大网盘空间，单位为字节，默认 256 MB
    maxm = db.Column(db.Integer, default=256*1024*1024)

`User` 类具有如下方法：

* `get_id` ：获取用户 id
* `verify_password` ：验证密码是否正确
* `generate_confirmation_token` ：生成用户邮箱验证 token
* `generate_email_change_token` ：生成修改邮箱 token
* `generate_reset_token` ：生成重置密码 token
* `generate_delete_token` ：生成删除文件 token
* `reset_password` ：用户验证重置密码的 token
* `confirm` ：用户验证邮箱激活的 token
* `change_email` ：用户验证修改邮箱的 token
* `delete_file` ：用户验证删除文件的 token
* `generate_copy_token` ：生成文件复制操作的 token
* `copy_token_verify` ：验证用户文件复制的 token
* `generate_move_token` ：生成用户文件移动的 token
* `move_token_verify` ：验证用户文件移动的 token
* `generate_fork_token` ：生成用户 Fork 文件 token
* `fork_token_verify` ：校验用户 Fork 文件 token 的合法性
* `generate_download_token` ：生成用户下载的 token
* `download_token_verify` ：验证用户下载 token 的合法性
* `generate_view_token` ：生成共享文件查看 token
* `view_token_verify` ：验证查看其他用户文件的 token 合法性
* `gravatar` ：获取用户头像链接，若存在自定义头像则返回自定义头像链接，否则从 gravatar 获取
* `can` ：用户是否具有某项权限
* `is_administrator` ：用户是否为管理员
* `ping` ：更新用户最近登录时间
* `follow` ：关注某个用户
* `unfollow` ：取消关注某个用户
* `is_following` ：是否已关注某个用户
* `is_followed_by` ：是否被某用户关注
* `followed_files` ：用户关注的人发布的共享文件
* `generate_fake` ：生成随机用户

可以看出，`User` 类的多数方法都用于处理需要鉴别用户身份的请求，包括生成 token 、验证 token 以及在验证通过后执行相应的处理。以删除资源为例， :ref:`web-blueprint-main` 中的 `delete_do` 视图函数将请求转发给当前用户，由当前用户验证 token 并执行删除操作，删除操作定义在方法 `delete_file` 中。

详细方法的参数请查看 `web/app/models.py` ，代码中给出了详细的注释。

.. _web-models-cfile:

实体文件 CFILE 类
>>>>>>>>>>>>>>>>>>>

`CFILE` 类和 :ref:`app-models-database-cfile` 保持一致，同时提供了如下 3 个方法：

* `md5FromFile(filepath)` ：计算指定路径的文件的 MD5 值，计算方法与 :ref:`app-protocal-md5` 相同。
* `makeFile(filepath, size)` ：在指定路径创建一个指定大小的随机内容的文件。
* `generate_fake(count)` ：在 `config.py` 中指定的 `ZENITH_FILE_STORE_PATH` 下生成指定数量个随机文件。


.. _web-models-permission:

权限
>>>>>>>>>>

`Permission` 类指定了如下几种权限：

.. code-block:: python

    FOLLOW = 0x01  # 关注其他用户
    COMMENT = 0x02  # 评论文件
    PUBLIC_FILES = 0x04  # 发布文件
    MODERATE_COMMENTS = 0x08  # 管理评论
    MODERATE_FILES = 0x10  # 管理文件
    ADMINISTER = 0x80  # 管理员
    
:ref:`web-models-role` 中的 `permissions` 元素代表该身份具有的权限，将 `permissions` 与指定权限做与操作，若结果为 1 则代表该身份具有指定权限。

.. _web-models-role:

身份
>>>>>>>

`Role` 类定义了用户的不同身份，顶点云默认提供的身份和对应权限有：

.. code-block:: python
   
   roles = {
    'Uncheck_user': (0x00, True),
    'User': (Permission.FOLLOW |
             Permission.COMMENT |
             Permission.WRITE_ARTICLES, False),
    'Moderator_comments': (Permission.FOLLOW |
             Permission.COMMENT |
             Permission.WRITE_ARTICLES |
             Permission.MODERATE_COMMENTS, False),
    'Moderator_tasks':(
             Permission.COMMENT |
             Permission.WRITE_ARTICLES |
             Permission.MODERATE_FILES, False),
    'Administrator': (0xff, False)
   }
   
`Moderator_tasks` 作为可扩展身份，默认的顶点云暂时没有启用。默认顶点云支持 `Uncheck_user` （邮箱未认证的用户）、`User` （普通用户）、`Moderator_comments` （评论管理员）以及 `Administrator` （超级管理员）。


接下来请您阅读 :ref:`web-viewfunction` 。

