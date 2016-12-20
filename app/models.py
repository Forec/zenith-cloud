# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：应用涉及的全部模型，包括用户、文件、消息、
#    分页、关注、评论、权限等

import hashlib, bleach, os
from math import ceil
from datetime import datetime
from config import basedir
from flask import current_app, request
from flask import url_for
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer
from markdown import markdown
from . import db, login_manager

# ----------------------------------------------------------------------
# 用户聊天消息模型
class Message(db.Model):
    __tablename__ = "cmessages"
    # 消息唯一 id
    mesid = db.Column(db.Integer,
                      primary_key=True)
    # 消息接收方 id
    targetid = db.Column(db.Integer,
                         db.ForeignKey('cuser.uid'))
    # 消息发送方 id
    sendid = db.Column(db.Integer,
                       db.ForeignKey('cuser.uid'))
    # 消息实体
    message = db.Column(db.String(512))
    # 消息创建时间
    created = db.Column(db.DateTime,
                        default= datetime.utcnow)
    # 消息是否已发送
    sended = db.Column(db.Boolean, default=False)
    # 消息是否已读
    viewed = db.Column(db.Boolean, default=False)
    # 消息发送方是否已删除此消息
    send_delete = db.Column(db.Boolean, default=False)
    # 消息接收方是否已删除此消息
    recv_delete = db.Column(db.Boolean, default=False)

    # 生成测试用随机消息
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        for i in range(count):
            u1Index = randint(0, user_count-1)
            u2Index = randint(0, user_count-1)
            while u1Index == u2Index:
                u2Index = randint(0, user_count-1)
            # 随机选择两个不同用户作为接收/发送方
            u1 = User.query.offset(u1Index).first()
            u2 = User.query.offset(u2Index).first()
            m = Message(
                     sender=u1,
                     receiver=u2,
                     message=forgery_py.\
                         lorem_ipsum.sentences(randint(2,3)),
                     created=forgery_py.date.date(True),
                     sended=False)
            db.session.add(m)
        db.session.commit()

# ---------------------------------------------------------------------
# 定义用户间的关注关系，第三方表。
class Follow(db.Model):
    __tablename__ = 'follows'
    # 关注者 id
    follower_id = db.Column(db.Integer,
                            db.ForeignKey('cuser.uid'),
                            primary_key = True)
    # 被关注者 id
    followed_id = db.Column(db.Integer,
                            db.ForeignKey('cuser.uid'),
                             primary_key = True)
    # 关注开始时间
    timestamp = db.Column(db.DateTime,
                          default=datetime.utcnow)

# -----------------------------------------------------------------------
# 用户模型
class User(UserMixin, db.Model):
    __tablename__ = 'cuser'
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

    def __repr__(self):
        return '<User %r>' % self.nickname

    # 获取用户 id
    def get_id(self):
        return self.uid

    # 设定无法从模型中获取密码
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    # 设定密码自动转为哈希值
    @password.setter
    def password(self, _password):
        self.password_hash = hashlib.md5(_password.encode('utf-8')).\
            hexdigest().upper()
    # 密码验证函数
    def verify_password(self, _password):
        return self.password_hash == hashlib.md5(_password.encode('utf-8')).\
            hexdigest().upper()
    # 生成邮箱验证 token
    def generate_confirmation_token(self, expiration=3600):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({'confirm':self.uid})
    # 生成修改邮箱 token
    def generate_email_change_token(self, new_email, expiration = 3600):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({'change_email': self.uid,
                        'new_email': new_email})
    # 生成重置密码 token
    def generate_reset_token(self, expiration=3600):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({'reset': self.uid})
    # 生成删除文件 token
    def generate_delete_token(self, fileid, expiration):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({'delete': fileid,
                        'user':self.uid})

    # 用户验证重置密码的 token
    def reset_password(self, token ,new_password):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.uid:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    # 用户验证邮箱激活的 token
    def confirm(self, token):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.uid:
            return False
        if self.role == None:
            self.role = Role.query.filter_by(name = 'User').first()
        elif self.role.name == 'Uncheck_user':
            self.role = Role.query.filter_by(name='User').first()
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    # 用户验证修改邮箱的 token
    def change_email(self, token):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.uid:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email = new_email).first() is not None:
            return False
        self.email = new_email
        if self.avatar_hash is None or \
            self.avatar_hash[0] != ':':
            # 用户无自定义头像则重新生成 avatar hash
            self.avatar_hash = hashlib.md5(
                    new_email.encode('utf-8')).\
                    hexdigest()
        db.session.add(self)
        db.session.commit()
        return True

    # 用户验证删除文件的 token
    def delete_file(self, token):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('delete') is None:
            return None
        if data.get('user') is None:
            return None
        user = User.query.filter_by(uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            return None
        # 获取要删除的 file 编号
        fileid = data.get('delete')
        file = File.query.filter_by(uid=fileid).first()
        if file is None or \
            (file.ownerid != self.uid and \
             not user.can(Permission.ADMINISTER)):
            return None
        returnURL = file.path

        if file.isdir == False:
            # 用户要删除单个文件
            if file.cfileid > 0:
                cfile = file.cfile
                cfile.ref -= 1
                self.used -= cfile.size
                if cfile.ref <= 0:
                    # 对应的 CFILE 已不被任何记录引用，删除
                    os.remove(
                        current_app.config['ZENITH_FILE_STORE_PATH'] +
                        str(cfile.uid)
                    )
                    db.session.delete(cfile)
                else:
                    db.session.add(cfile)
                db.session.add(self)
            db.session.delete(file)
        else:
            # 用户试图删除一个目录，寻找到该目录下的全部文件
            files_related = File.query.filter(
                    File.path.like(file.path+file.filename+'/%'))
            # 确保删除当前用户的文件
            files_related = files_related.filter("ownerid=:_id").\
                params(_id=self.uid).all()
            for _file in files_related:
                if _file.cfileid > 0:
                    cfile = _file.cfile
                    cfile.ref -= 1
                    self.used -= cfile.size
                    # 减少每个相关 CFILE 的引用数
                    if cfile.ref <= 0:
                        os.remove(
                            current_app.config['ZENITH_FILE_STORE_PATH'] +
                            str(cfile.uid)
                        )
                        db.session.delete(cfile)
                    else:
                        db.session.add(cfile)
                    db.session.add(self)
                db.session.delete(_file)
            db.session.delete(file)
        db.session.commit()
        return returnURL, file.ownerid

    # 生成文件复制操作的 token
    def generate_copy_token(self, fileid, _path, expiration):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({'copy': fileid,
                        'path': _path,
                        'user':self.uid})

    # 验证用户文件复制的 token
    def copy_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('copy') is None or \
            data.get('user') is None or \
            data.get('path') is None:
            return None
        user = User.query.filter_by(
                uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            # 若当前用户不具备管理员权限且与token中用户不同
            return None
        fileid = data.get('copy')
        file = File.query.filter_by(uid=fileid).first()
        if file is None or \
            (file.ownerid != self.uid and \
             not user.can(Permission.ADMINISTER)):
            # 要复制的文件不存在 或 用户不具有管理员权限且不是文件所有者
            return None
        # 返回一个列表，包含要复制的文件 id 以及要复制到的目标路径
        return [fileid, data.get('path')]

    # 生成用户文件移动的 token
    def generate_move_token(self, fileid, _path, expiration):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({'move': fileid,
                        'path': _path,
                        'user':self.uid})

    # 验证用户文件移动的 token
    def move_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('move') is None or \
            data.get('user') is None or \
            data.get('path') is None:
            return None
        user = User.query.filter_by(
                uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            return None
        fileid = data.get('move')
        file = File.query.filter_by(uid=fileid).first()
        if file is None or \
            (file.ownerid != self.uid and \
             not user.can(Permission.ADMINISTER)):
            # 文件不存在 或 用户不具有管理员权限且不是文件所有者
            return None
        # 返回要移动的文件 id，以及要移动到的路径
        return [fileid, data.get('path')]

    # 生成用户 Fork 文件 token
    def generate_fork_token(self,
                            fileid,
                            _path,
                            _linkpass,
                            expiration):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({'fork': fileid,
                        'path': _path,
                        'linkpass': _linkpass,
                        'user':self.uid})

    # 校验用户 Fork 文件 token 的合法性
    def fork_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('fork') is None or \
            data.get('user') is None or \
            data.get('path') is None or \
            data.get('linkpass') is None:
            # token 中包含的信息不全
            return None
        user = User.query.filter_by(
                uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            # 用户不具有管理员权限且和token中的用户不一致
            return None
        fileid = data.get('fork')
        password = data.get('linkpass')
        file = File.query.get(fileid)
        if file is None or \
            file.private==True or \
            file.linkpass != password:
            # 文件不存在 或 文件为私有 或 token 中携带的文件提取码不正确
            return None
        # 返回要 Fork 的文件 id，要 Fork 到的路径以及 文件提取码
        return [fileid, data.get('path'), password]

    # 生成用户下载的 token
    def generate_download_token(self,
                                fileid,
                                _linkpass,
                                expiration):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({'download': fileid,
                        'linkpass': _linkpass,
                        'user':self.uid})

    # 验证用户下载 token 的合法性
    def download_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('download') is None or \
            data.get('user') is None or \
            data.get('linkpass') is None:
            # token 包含信息不完整
            return None
        user = User.query.filter_by(
                uid=data.get('user')).first()
        if user.uid != self.uid and \
            not user.can(Permission.ADMINISTER):
            # 用户不具有管理员权限且和 token 中的用户不一致
            return None
        fileid = data.get('download')
        password = data.get('linkpass')
        file = File.query.get(fileid)
        if file is None or \
            (file.private==True and \
             file.ownerid != self.uid and \
             not self.can(Permission.ADMINISTER)) or \
            file.linkpass != password:
            # 文件不存在 或
            # 文件私有且用户不是文件所有人且用户不具备管理员权限 或
            # 提取码不正确
            return None
        # 返回要下载的文件 id 和 提取码
        return [fileid, password]

    # 生成共享文件查看 token
    def generate_view_token(self,
                            rootid = -1,
                            _linkpass = '',
                            type = 'all',
                            order = 'name',
                            direction = 'front',
                            path = '',
                            key = '',
                            expiration = 3600):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'],
                expiration)
        return s.dumps({
            'view': rootid,
            'linkpass': _linkpass,
            'user': self.uid,
            'order': order,
            'direction': direction,
            'path': path,
            'key': key,
            'type': type
        })

    # 验证查看其他用户文件的 token 合法性
    def view_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(
                current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('view') is None or \
            data.get('user') is None or \
            data.get('linkpass') is None:
            # token 信息不完整
            return None
        user = User.query.filter_by(
                uid=data.get('user')).first()
        if user.uid != self.uid and \
            not user.can(Permission.ADMINISTER):
            # 当前用户不具有管理员权限且和 token 中用户不一致
            return None
        fileid = data.get('view')
        password = data.get('linkpass')
        file = File.query.get(fileid)
        if file is None or \
           (file.private==True and \
            file.ownerid != self.uid and \
            not self.can(Permission.ADMINISTER)) or \
           file.linkpass != password:
            # 文件不存在 或
            # 文件私有且当前用户不具有管理员权限且当前用户不是文件所有人 或
            # 文件提取码不正确
            return None
        # 返回 查看的类型、顺序、方向、关键词、根文件 id 以及当前路径
        return {
            'type': data.get('type') or 'all',
            'order': data.get('order') or 'time',
            'direction': data.get('direction') or 'front',
            'key': data.get('key') or '',
            'password': data.get('linkpass'),
            'rootid': data.get('view'),
            'path': data.get('path') or \
                    file.path + file.filename + '/'
        }

    # 获取用户头像链接
    def gravatar(self, size=100, default='identicon', rating='g'):
        # 若存在用户自定义头像则返回自定义头像
        if self.avatar_hash is not None and self.avatar_hash[0] == ':':
            # 定义 avatar_hash 的第一个字符为 : 时有自定义头像
            return self.avatar_hash[1:]
        for _suffix in current_app.config['ZENITH_VALID_THUMBNAIL']:
            thumbnailPath = os.path.join(basedir,
                                 'app/static/thumbnail/' +
                                    str(self.uid) + _suffix)
            if os.path.isfile(thumbnailPath):
                thumbnailURL = url_for('static',
                               filename = 'thumbnail/' +
                                          str(self.uid) +
                                          _suffix,
                               _external=True)
                self.avatar_hash = ':'+ thumbnailURL
                db.session.add(self)
                return thumbnailURL

        # 不存在自定义头像则从 gravatar 获取
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url= 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or \
               hashlib.md5(self.email.encode('utf-8')).\
               hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
                url = url,
                hash = hash,
                size=size,
                default = default,
                rating = rating
        )

    # 用户是否具有某项权限
    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    # 用户是否为管理员
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # 更新用户最近登录时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    # 关注某个用户
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    # 取消关注某个用户
    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.uid).first()
        if f:
            db.session.delete(f)

    # 是否已关注某个用户
    def is_following(self, user):
        return self.followed.filter_by(
            followed_id = user.uid
        ).first() is not None

    # 是否被某用户关注
    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id = user.uid
        ).first() is not None

    # 用户关注的人发布的共享文件
    @property
    def followed_files(self):
        fileList = []
        for fl in self.followed.all():
            _user = User.query.get(fl.followed_id)
            if _user is None:
                continue
            # 过滤关注的人和共享文件
            files = File.query.filter("private=0 and ownerid=:d").\
                params(d=_user.uid).all()
            fileList.extend(files)
        return fileList

    # 生成随机用户
    @staticmethod
    def generate_fake(count=5):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py
        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     nickname = forgery_py.internet.user_name(True),
                     password = forgery_py.lorem_ipsum.word(),
                     confirmed = True,
                     about_me = forgery_py.lorem_ipsum.sentence(),
                     member_since = forgery_py.date.date(True))
            # 为用户添加默认的 public 目录
            f1 = File(path = '/',
                     filename = 'public',
                     perlink = '',
                     cfileid= -1,
                     isdir=True,
                     linkpass = '',
                     private = 0,
                     created= u.member_since,
                     owner = u,
                     description ='')
            # 为用户添加默认的 upload 目录
            f2 = File(path = '/',
                     filename = 'upload',
                     perlink = '',
                     cfileid= -1,
                     isdir=True,
                     linkpass = '',
                     private = 1,
                     created= u.member_since,
                     owner = u,
                     description ='')
            db.session.add(u)
            db.session.add(f1)
            db.session.add(f2)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    # 用户初始化函数
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            # 用户邮箱和管理员邮箱一致则设为管理员权限
            if self.email == current_app.config['EMAIL_ADMIN']:
                self.role = Role.query.filter_by(permission=0xff).first()
            # 分配默认用户身份
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        # 为用户分配头像链接
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')
            ).hexdigest()
        # 新加入的用户需关注自己
        self.follow(self)
# -----------------------------------------------------------------------
# 用户权限模型
class Permission:
    FOLLOW = 0x01  # 关注其他用户
    COMMENT = 0x02  # 评论文件
    PUBLIC_FILES = 0x04  # 发布文件
    MODERATE_COMMENTS = 0x08  # 管理评论
    MODERATE_FILES = 0x10  # 管理文件
    ADMINISTER = 0x80  # 管理员

# ------------------------------------------------------------------------
# 用户身份模型
class Role(db.Model):
    __tablename__ = 'roles'
    # 身份编号
    id = db.Column(db.Integer, primary_key=True)
    # 身份名称
    name = db.Column(db.String(64), unique=True, index=True)
    # 是否为身份默认身份
    default = db.Column(db.Boolean, default=False)
    # 此身份具有的权限
    permissions = db.Column(db.Integer)
    # 具有此身份的用户
    users = db.relationship('User', backref='role', lazy='dynamic')

    # 向数据库插入用户
    @staticmethod
    def insert_roles():
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
                Permission.MODERATE_FILES, False
            ),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

# ---------------------------------------------------------------------
# 实体文件模型
class CFILE(db.Model):
    __tablename__  = 'cfile'
    # 文件编号
    uid = db.Column(db.Integer, primary_key=True)
    # 文件的md5值（4M为一块计算 md5，拼接后计算 md5）
    md5 = db.Column(db.String(32))
    # 文件大小
    size = db.Column(db.Integer)
    # 文件引用数
    ref = db.Column(db.Integer, default=0)
    # 文件创建时间
    created = db.Column(db.DateTime,
                        default=datetime.utcnow)
    # 引用此文件的用户文件记录
    records = db.relationship('File', backref='cfile', lazy='dynamic')

    # 从文件路径计算出该文件的 md5 值
    @staticmethod
    def md5FromFile(filepath):
        midterm = ""
        f = open(filepath, 'rb')
        buffer = 4096*1024  # 4M
        while 1:
            chunk = f.read(buffer)
            if not chunk:
                break
            midterm += hashlib.md5(chunk).hexdigest()
        f.close()
        return hashlib.md5(midterm.encode('utf-8')).hexdigest().upper()

    # 在指定路径生成一个指定大小的随机内容文件
    @staticmethod
    def makeFile(filepath, size):
        f = open(filepath, 'wb')
        for i in range(0, size):
            f.write('a'.encode('utf-8'))
        f.close()

    # 生成测试用的随机实体文件
    @staticmethod
    def generate_fake(count=5):
        from random import seed, randint
        seed()
        for i in range(count):
            # 随机大小，从 512kB 到 20MB
            _size= randint(512 * 1024,20*1024*1024)
            c = CFILE(size=_size,
                      ref=0,
                      md5=""
                      )
            db.session.add(c)
            db.session.commit()
            CFILE.makeFile(
                    current_app.config['ZENITH_FILE_STORE_PATH']+str(c.uid),
                    _size)
            c.md5 = CFILE.md5FromFile(
                    current_app.config['ZENITH_FILE_STORE_PATH']+str(c.uid))
            db.session.add(c)
            db.session.commit()

# -------------------------------------------------------------------------
# 用户资源记录模型
class File(db.Model):
    __tablename__ = 'ufile'
    uid = db.Column(db.Integer, primary_key=True)
    # 资源所有者
    ownerid = db.Column(db.Integer,
                        db.ForeignKey('cuser.uid'))
    # 资源引用的实体文件编号
    cfileid = db.Column(db.Integer,
                        db.ForeignKey('cfile.uid'))
    # 资源所在的路径
    path = db.Column(db.String(256))
    # 资源外链
    perlink = db.Column(db.String(128))
    # 资源创建时间
    created = db.Column(db.DateTime,
                        default =datetime.utcnow)
    # 资源的分享数
    shared = db.Column(db.Integer, default=0)
    # 资源被下载数
    downloaded = db.Column(db.Integer, default=0)
    # 资源名
    filename = db.Column(db.String(128))
    # 是否为私有资源
    private = db.Column(db.Boolean, default=True)
    # 资源提取码
    linkpass = db.Column(db.String(4))
    # 资源是否为文件夹
    isdir = db.Column(db.Boolean, default=False)
    # 资源描述
    description = db.Column(db.String(256))
    # 资源下的评论，外链 comment 表
    comments = db.relationship('Comment',backref='file', lazy='dynamic')

    def __repr__(self):
        return '<File %r>' % self.filename

    # 生成随机资源
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        cfile_count = CFILE.query.count()
        suffixList = [['.avi', '.mp4', '.mpeg', '.flv', '.rmvb',
                       '.rm', '.wmv'],
                      ['.jpg', '.jpeg', '.png', '.svg', '.bmp',
                       '.psd'],
                      ['.doc', '.ppt', '.pptx', '.docx', '.xls',
                       '.xlsx', '.txt', '.md', '.rst', '.note'],
                      ['.rar', '.zip', '.gz', '.gzip', '.tar',
                       '.7z'],
                      ['.mp3', '.wav', '.wma', '.ogg'],
                      ['']]
        # 资源类型后缀
        for i in range(count):
            # 随机选取用户作为资源所有人
            u = User.query.offset(randint(0, user_count-1)).first()
            # 随机选取实体文件作为资源引用
            _cfile = CFILE.query.offset(randint(0, cfile_count-1)).first()
            _cfile.ref += 1
            db.session.add(_cfile)
            # 随机生成 0 -5 的路径深度
            pathDeep = randint(0, 5)
            pathPart = '/'
            prePrivate = 1
            _linkpass =  str(randint(1000,9999))
            for j in range(0, pathDeep):
                folder = forgery_py.lorem_ipsum.word()
                isFile = File.query.filter_by(path=pathPart).\
                    filter_by(filename=folder).\
                    filter_by(isdir=True).first()
                if isFile is not None and isFile.ownerid == u.uid:
                    pathPart += folder
                    pathPart += '/'
                    continue
                # 若父级目录为私有，则当前目录随机设定共享/私有
                if prePrivate == 1:
                    prePrivate = randint(0, 1)
                # 否则当前目录为共享
                f = File(path = pathPart,
                         filename=folder,
                         perlink = '',
                         cfileid = -1,
                         isdir=True,
                         linkpass =_linkpass,
                         created=forgery_py.date.date(True),
                         ownerid=u.uid,
                         private = prePrivate,
                         description=forgery_py.lorem_ipsum.\
                                sentences(randint(3,5)))
                pathPart += folder
                pathPart += '/'
                # 生成路径上的子目录，并加入数据库
                db.session.add(f)

            # 随机选择生成文件的拓展名
            suffixType = randint(0, 5)
            suffixTypeIndex = randint(0, len(suffixList[suffixType])-1)
            # 若资源父级目录为私有，则文件随机决定共享/私有
            if prePrivate == 1:
                prePrivate = randint(0, 1)
            f = File(path = pathPart,
                     filename = forgery_py.lorem_ipsum.word() +
                                suffixList[suffixType][suffixTypeIndex],
                     perlink = forgery_py.lorem_ipsum.word(),
                     cfile= _cfile,
                     linkpass =_linkpass,
                     private = prePrivate,
                     created=forgery_py.date.date(True),
                     ownerid = u.uid,
                     description =forgery_py.lorem_ipsum.\
                        sentences(randint(4,8)))
            db.session.add(f)
            # 用户已使用云盘空间增加实体文件大小
            u.used += _cfile.size
            db.session.add(u)
        db.session.commit()

# -------------------------------------------------------------------------
# 用户评论模型
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer,
                   primary_key = True)
    # 评论内容
    body = db.Column(db.Text)
    # 评论可使用 markdown 语法，内容渲染为 html
    body_html = db.Column(db.Text)
    # 评论发布时间
    timestamp = db.Column(db.DateTime,
                          index= True,
                          default=datetime.utcnow)
    # 评论是否被折叠
    disabled = db.Column(db.Boolean,
                         default = False)
    # 评论发布者的编号
    author_id= db.Column(db.Integer,
                         db.ForeignKey('cuser.uid'))
    # 评论所属的资源编号
    file_id = db.Column(db.Integer,
                        db.ForeignKey('ufile.uid'))

    # 评论内容发生变化时重新渲染
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        # 允许出现的标签
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code',
                        'em', 'i','br', 'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    # 随机生成评论
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        file_count = File.query.count()
        for i in range(count):
            # 随机选择用户作为评论发布者
            u = User.query.offset(randint(0, user_count-1)).first()
            # 随机选择资源作为评论父级资源
            f = File.query.offset(randint(0, file_count-1)).first()
            c = Comment(
                     body = forgery_py.lorem_ipsum.\
                         sentences(randint(1,3)),
                     timestamp=forgery_py.date.date(True),
                     author = u,
                     disabled = False,
                     file = f)
            db.session.add(c)
        db.session.commit()

# --------------------------------------------------------------------
# 匿名用户模型，注册到 flask_login 为未登录用户
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    def is_administrator(self):
        return False

# 注册匿名用户
login_manager.anonymous_user = AnonymousUser
login_manager.login_message = u"您需要先登录才能访问此界面！"

# ----------------------------------------------------------------------
# flask_login 所需的用户登录标识符
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

# -----------------------------------------------------------------------
# 自定义内容分页模型
class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count
    # 页数
    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))
    # 当前页是否有更前页
    @property
    def has_prev(self):
        return self.page > 1
    # 当前页是否有后页
    @property
    def has_next(self):
        return self.page < self.pages
    # 当前页的内容列表
    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num