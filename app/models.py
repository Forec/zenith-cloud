from . import db
import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from . import login_manager
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import current_app, request
from datetime import datetime
from markdown import markdown
import hashlib
import bleach

class Message(db.Model):
    __tablename__ = "cmessages"
    mesid = db.Column(db.Integer, primary_key=True)
    targetid = db.Column(db.Integer, db.ForeignKey('cuser.uid'))
    sendid = db.Column(db.Integer, db.ForeignKey('cuser.uid'))
    message = db.Column(db.String(512))
    created = db.Column(db.DateTime, default= datetime.utcnow)
    sended = db.Column(db.Boolean, default=False)
    viewed = db.Column(db.Boolean, default=False)
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        for i in range(count):
            u1 = User.query.offset(randint(0, user_count-1)).first()
            u2 = User.query.offset(randint(0, user_count-1)).first()
            m = Message(
                     sender=u1,
                     receiver=u2,
                     message=forgery_py.lorem_ipsum.sentence(randint(2,3)),
                     sended=False)
            db.session.add(m)
        db.session.commit()


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('cuser.uid'),
                            primary_key = True)
    followed_id = db.Column(db.Integer, db.ForeignKey('cuser.uid'),
                             primary_key = True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    __tablename__ = 'cuser'
    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64),unique=True)
    password_hash = db.Column(db.String(32))
    created = db.Column(db.DateTime, default = datetime.utcnow)
    confirmed = db.Column(db.Boolean, default= False)
    nickname = db.Column(db.String(64))
    avatar_hash = db.Column(db.String(32))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default = datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default = datetime.utcnow)
    score = db.Column(db.Integer, default = 20)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    files = db.relationship('File', backref='owner', lazy = 'dynamic')
    comments = db.relationship('Comment',backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys= [Follow.follower_id],
                               backref = db.backref('follower', lazy='joined'),
                               lazy = 'dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                               foreign_keys= [Follow.followed_id],
                               backref = db.backref('followed', lazy='joined'),
                               lazy = 'dynamic',
                               cascade='all, delete-orphan')

    sendMessages = db.relationship('Message', backref='sender', lazy='dynamic',
                              foreign_keys = [Message.sendid])

    recvMessages = db.relationship('Message', backref='receiver', lazy='dynamic',
                               foreign_keys = [Message.targetid])

    current_path = '/'
    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    @password.setter
    def password(self, _password):
        self.password_hash = hashlib.md5(_password.encode('utf-8')).hexdigest().upper()
    def verify_password(self, _password):
        return self.password_hash == hashlib.md5(_password.encode('utf-8')).hexdigest().upper()
    def generate_confirmation_token(self, expiration=3600):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm':self.uid})
    def generate_email_change_token(self, new_email, expiration = 3600):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.uid, 'new_email': new_email})
    def generate_reset_token(self, expiration=3600):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.uid})
    def generate_delete_token(self, fileid, expiration):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'delete': fileid, 'user':self.uid})
    def reset_password(self, token ,new_password):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
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
    def get_id(self):
        return self.uid
    def confirm(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY']) # match logged user
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
    def change_email(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
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
        self.avatar_hash = hashlib.md5(new_email.encode('utf-8')).hexdigest()
        db.session.add(self)
        db.session.commit()
        return True
    def delete_file(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('delete') is None:
            return False
        if data.get('user') is None:
            return False
        user = User.query.filter_by(uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            return False
        fileid = data.get('delete')
        file = File.query.filter_by(uid=fileid).first()
        if file is None or (file.ownerid != self.uid and not user.can(Permission.ADMINISTER)):
            return False
        db.session.delete(file)
        db.session.commit()
        return True
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url= 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or \
               hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url = url, hash = hash, size=size, default = default, rating = rating
        )
    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.uid).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id = user.uid
        ).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id = user.uid
        ).first() is not None

    @property
    def followed_files(self):
        return File.query.join(Follow, Follow.followed_id==File.ownerid).\
            filter(Follow.follower_id==self.uid).filter("private=0 or ownerid=:id").params(id=self.uid)

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
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['EMAIL_ADMIN']:
                self.role = Role.query.filter_by(permission=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')
            ).hexdigest()
        self.follow(self)

class Permission:
    FOLLOW = 0x01  # follow other users
    COMMENT = 0x02  # comment on other users' articles
    WRITE_ARTICLES = 0x04  # write articles
    MODERATE_COMMENTS = 0x08  # moderate users' comments
    MODERATE_FILES = 0x10
    ADMINISTER = 0x80  # administer
#  anynomous 0x00 0b00000000   read only
#  user	 0x07 0b00000111   write articles, comment, follow ( default user )
#  helper admin 0x0f 0b00001111	  add moderation on normal user
#  administer  0xff	 0b11111111	  all permissions

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    default = db.Column(db.Boolean, default=False)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

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

class CFILE(db.Model):
    __tablename__  = 'cfile'
    uid = db.Column(db.Integer, primary_key=True)
    md5 = db.Column(db.String(32))
    size = db.Column(db.Integer)
    ref = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime,default=datetime.utcnow)
    records = db.relationship('File', backref='cfile', lazy='dynamic')

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
    @staticmethod
    def makeFile(filepath, size):
        f = open(filepath, 'wb')
        for i in range(0, size):
            f.write('a'.encode('utf-8'))
        f.close()
    @staticmethod
    def generate_fake(count=5):
        from random import seed, randint
        import forgery_py
        seed()
        for i in range(count):
            _size= randint(128,512*1024)
            c = CFILE(size=_size,
                      ref=0,
                      md5=""
                      )
            db.session.add(c)
            db.session.commit()
            CFILE.makeFile("G:\\Cloud\\"+str(c.uid), _size)
            c.md5 = CFILE.md5FromFile("G:\\Cloud\\"+str(c.uid))
            db.session.add(c)
            db.session.commit()

class File(db.Model):
    __tablename__ = 'ufile'
    uid = db.Column(db.Integer, primary_key=True)
    ownerid = db.Column(db.Integer, db.ForeignKey('cuser.uid'))
    cfileid = db.Column(db.Integer, db.ForeignKey('cfile.uid'))
    path = db.Column(db.String(256))
    perlink = db.Column(db.String(128))
    created = db.Column(db.DateTime, default =datetime.utcnow)
    shared = db.Column(db.Integer, default=0)
    downloaded = db.Column(db.Integer, default=0)
    filename = db.Column(db.String(128))
    private = db.Column(db.Boolean, default=True)
    linkpass = db.Column(db.String(4))
    isdir = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(256))
    comments = db.relationship('Comment',backref='file', lazy='dynamic')
    def __repr__(self):
        return '<File %r>' % self.filename
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        cfile_count = CFILE.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            _cfile = CFILE.query.offset(randint(0, cfile_count-1)).first()
            _cfile.ref += 1
            db.session.add(_cfile)
            f = File(path = '/',
                     filename = forgery_py.lorem_ipsum.word(),
                     perlink = forgery_py.lorem_ipsum.word(),
                     cfile= _cfile,
                     linkpass = str(randint(1000,9999)),
                     private = randint(0,1),
                     created=forgery_py.date.date(True),
                     owner = u,
                     description ='')
            db.session.add(f)
        db.session.commit()


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index= True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default = False)
    author_id= db.Column(db.Integer, db.ForeignKey('cuser.uid'))
    file_id = db.Column(db.Integer, db.ForeignKey('ufile.uid'))
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i','br',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        file_count = File.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            f = File.query.offset(randint(0, file_count-1)).first()
            c = Comment(
                     body = forgery_py.lorem_ipsum.sentences(randint(1,3)),
                     timestamp=forgery_py.date.date(True),
                     author = u,
                     disabled = False,
                     file = f)
            db.session.add(c)
        db.session.commit()

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser
login_manager.login_message = u"您需要先登录才能访问此界面！"

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))