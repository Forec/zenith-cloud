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
    send_delete = db.Column(db.Boolean, default=False)
    recv_delete = db.Column(db.Boolean, default=False)
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
            u1 = User.query.offset(u1Index).first()
            u2 = User.query.offset(u2Index).first()
            m = Message(
                     sender=u1,
                     receiver=u2,
                     message=forgery_py.lorem_ipsum.sentences(randint(2,3)),
                     created=forgery_py.date.date(True),
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
    used = db.Column(db.Integer, default=0)
    maxm = db.Column(db.Integer, default=512*1024*1024) # 512M

    def __repr__(self):
        return '<User %r>' % self.nickname

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
            return None
        if data.get('delete') is None:
            return None
        if data.get('user') is None:
            return None
        user = User.query.filter_by(uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            return None
        fileid = data.get('delete')
        file = File.query.filter_by(uid=fileid).first()
        if file is None or (file.ownerid != self.uid and not user.can(Permission.ADMINISTER)):
            return None
        returnURL = file.path
        if file.isdir == False:
            if file.cfileid > 0:
                cfile = file.cfile
                cfile.ref -= 1
                db.session.add(cfile)
                self.used -= cfile.size
                db.session.add(self)
            db.session.delete(file)
        else:
            files_related = File.query.filter(File.path.like(file.path+file.filename+'/%')).all()
            for _file in files_related:
                if _file.cfileid > 0:
                    cfile = _file.cfile
                    cfile.ref -= 1
                    db.session.add(cfile)
                    self.used -= cfile.size
                    db.session.add(self)
                db.session.delete(_file)
            db.session.delete(file)
        db.session.commit()
        return returnURL, file.ownerid

    def generate_copy_token(self, fileid, _path, expiration):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'copy': fileid, 'path': _path, 'user':self.uid})
    def copy_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('copy') is None or data.get('user') is None or data.get('path') is None:
            return None
        user = User.query.filter_by(uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            return None
        fileid = data.get('copy')
        file = File.query.filter_by(uid=fileid).first()
        if file is None or (file.ownerid != self.uid and not user.can(Permission.ADMINISTER)):
            return None
        return [fileid, data.get('path')]

    def generate_move_token(self, fileid, _path, expiration):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'move': fileid, 'path': _path, 'user':self.uid})
    def move_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('move') is None or data.get('user') is None or data.get('path') is None:
            return None
        user = User.query.filter_by(uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            return None
        fileid = data.get('move')
        file = File.query.filter_by(uid=fileid).first()
        if file is None or (file.ownerid != self.uid and not user.can(Permission.ADMINISTER)):
            return None
        return [fileid, data.get('path')]


    def generate_fork_token(self, fileid, _path, _linkpass, expiration):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'fork': fileid, 'path': _path, 'linkpass': _linkpass, 'user':self.uid})
    def fork_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('fork') is None or data.get('user') is None or \
                        data.get('path') is None or data.get('linkpass') is None:
            return None
        user = User.query.filter_by(uid=data.get('user')).first()
        if user.uid != self.uid  and \
            not user.can(Permission.ADMINISTER):
            return None
        fileid = data.get('fork')
        password = data.get('linkpass')
        file = File.query.get(fileid)
        if file is None or file.private==True or file.linkpass != password:
            return None
        return [fileid, data.get('path'), password]

    def generate_download_token(self, fileid, _linkpass, expiration):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'download': fileid, 'linkpass': _linkpass, 'user':self.uid})
    def download_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('download') is None or data.get('user') is None or data.get('linkpass') is None:
            return None
        user = User.query.filter_by(uid=data.get('user')).first()
        if user.uid != self.uid and \
            not user.can(Permission.ADMINISTER):
            return None
        fileid = data.get('download')
        password = data.get('linkpass')
        file = File.query.get(fileid)
        if file is None or \
            (file.private==True and file.ownerid != self.uid and not self.can(Permission.ADMINISTER)) or \
            file.linkpass != password:
            return None
        return [fileid, password]

    def generate_view_token(self,
                            rootid,
                            _linkpass,
                            type,
                            order,
                            direction,
                            path,
                            key,
                            expiration):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
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

    def view_token_verify(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        if data.get('view') is None or \
            data.get('user') is None or \
            data.get('linkpass') is None:
            return None
        user = User.query.filter_by(uid=data.get('user')).first()
        if user.uid != self.uid and \
            not user.can(Permission.ADMINISTER):
            return None
        fileid = data.get('view')
        password = data.get('linkpass')
        file = File.query.get(fileid)
        if file is None or \
           (file.private==True and \
            file.ownerid != self.uid and \
            not self.can(Permission.ADMINISTER)) or \
           file.linkpass != password:
            return None
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
        fileList = []
        for fl in self.followed.all():
            _user = User.query.get(fl.followed_id)
            if _user is None:
                continue
            files = File.query.filter("private=0 and ownerid=:d").params(d=_user.uid).all()
            fileList.extend(files)
        return fileList

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
            f = File(path = '/',
                     filename = 'public',
                     perlink = '',
                     cfileid= -1,
                     isdir=True,
                     linkpass = '',
                     private = 0,
                     created= u.member_since,
                     owner = u,
                     description ='')
            db.session.add(u)
            db.session.add(f)
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
            _size= randint(512 * 1024,20*1024*1024)
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
        suffixList = [['.avi', '.mp4', '.mpeg', '.flv', '.rmvb', '.rm', '.wmv'],
                      ['.jpg', '.jpeg', '.png', '.svg', '.bmp', '.psd'],
                      ['.doc', '.ppt', '.pptx', '.docx', '.xls', '.xlsx', '.txt', '.md', '.rst', '.note'],
                      ['.rar', '.zip', '.gz', '.gzip', '.tar', '.7z'],
                      ['.mp3', '.wav', '.wma', '.ogg'],
                      ['']]
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            _cfile = CFILE.query.offset(randint(0, cfile_count-1)).first()
            _cfile.ref += 1
            db.session.add(_cfile)
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
                if prePrivate == 1:
                    prePrivate = randint(0, 1)
                f = File(path = pathPart,
                         filename=folder,
                         perlink = '',
                         cfileid = -1,
                         isdir=True,
                         linkpass =_linkpass,
                         created=forgery_py.date.date(True),
                         ownerid=u.uid,
                         private = prePrivate,
                         description=forgery_py.lorem_ipsum.sentences(randint(3,5)))
                pathPart += folder
                pathPart += '/'
                db.session.add(f)
            # parhPart is now the dest path
            suffixType = randint(0, 5)
            suffixTypeIndex = randint(0, len(suffixList[suffixType])-1)
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
                     description =forgery_py.lorem_ipsum.sentences(randint(4,8)))
            db.session.add(f)
            u.used += _cfile.size
            db.session.add(u)
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

from math import ceil


class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count
    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))
    @property
    def has_prev(self):
        return self.page > 1
    @property
    def has_next(self):
        return self.page < self.pages
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