# 作者：Forec
# 最后修改时间：2016-12-13
# 邮箱：forec@bupt.edu.cn
# 关于此文件：包含了 main 蓝本中使用到的全部 wtf 表单

from ..models import Role, User
from flask import current_app
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField, \
    TextAreaField, BooleanField, SelectField, \
    IntegerField
from wtforms.validators import Required, Length, \
    Email, ValidationError

# ------------------------------------------------------------------
# 用户编辑自己个人资料的表单，昵称长度必须在 3 到 64 个字符之间，且必须唯一
class EditProfileForm(FlaskForm):
    thumbnail = FileField('上传头像')
    nickname = StringField('昵称',
        validators=[Length(3, 64, message='昵称长度必须在 3 ~ 64 个字符之间！')])
    about_me = TextAreaField('关于我',
        validators=[Length(0, 60, message='不能超过 40 个字符！')])
    submit = SubmitField('提交')

    def validate_nickname(self, field):     # 验证昵称未被其他用户使用
        if field.data != current_user.nickname and \
            User.query.filter_by(nickname=field.data).first():
            raise ValidationError('该昵称已被使用.')
    def validate_thumbnail(self, field):     # 验证昵称未被其他用户使用
        if not field.has_file():
            return
        valid = False
        for _suffix in current_app.config['ZENITH_VALID_THUMBNAIL']:
            if _suffix in field.data.filename:
                valid = True
        if not valid:
            raise ValidationError('上传的头像必须为 .jpg/'
                                  '.jpeg/.png/.ico 格式之一！')

# ------------------------------------------------------------------
# 管理员编辑用户资料的表单，电子邮箱和昵称必须唯一。
class EditProfileAdminForm(FlaskForm):
    email = StringField('电子邮箱',
            validators=[Required(),
                        Length(5,64,'你输入的电子邮箱过长！'),
                        Email(message='不是合法的电子邮箱地址！')])
    nickname = StringField('昵称',
            validators=[Required(),
                        Length(3, 64)])
    maxm = IntegerField('云盘容量（MB）',
            validators=[Required()])
    confirmed = BooleanField('已验证邮箱')
    role = SelectField('身份', coerce=int)
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):    # 验证邮箱未被其他用户注册
        if field.data != self.user.email and \
            User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已注册.')

    def validate_nickname(self, field):     # 验证昵称未被其他用户使用
        if field.data != self.user.nickname and \
            User.query.filter_by(nickname=field.data).first():
            raise ValidationError('该昵称已被使用.')

# ------------------------------------------------------------------------
# 用户上传文件的表单，文件名长度不能超过 128 字符。
class UploadForm(FlaskForm):
    file = FileField('选择文件',
            validators=[FileRequired()])
    share = BooleanField('共享此文件/目录')
    body = TextAreaField("资源描述（回车和多余空字符将被过滤）")
    submit = SubmitField('确定上传')

    def validate_body(self, field):     # 限制资源描述在 200 字符内
        if len(field.data) > 200:
            raise ValidationError('描述过长，请限制在200字内')
    def validate_file(self, field):     # 禁止违例文件名
        for inffix in current_app.config['ZENITH_INVALID_INFFIX']:
            if inffix in field.data.filename:
                raise ValidationError('您上传的文件名不合法，'
                                      '请检查并重新上传！')

# -------------------------------------------------------------------------
# 用户执行删除文件操作时，用于确认的表单。
class FileDeleteConfirmForm(FlaskForm):
    filename = StringField("文件名",
        validators=[Required(),
                    Length(1, 128)])
    body = TextAreaField("资源描述（回车和多余空字符将被过滤）")
    submit = SubmitField('修改')

    def validate_body(self, field):     # 限制资源描述在 200 字符内
        if len(field.data) > 200:
            raise ValidationError('描述过长，请限制在200字内')

# -------------------------------------------------------------------------
# 用户评论提交表单
class CommentForm(FlaskForm):
    body = StringField('添加评论',
                       validators=[Required()])
    submit = SubmitField('提交')

# --------------------------------------------------------------------------
# 管理员在搜索关键字评论/文件、用户搜索关键字文件/消息时的表单。
class SearchForm(FlaskForm):
    key = StringField()
    go = SubmitField('搜索')

# --------------------------------------------------------------------------
# 用户聊天时发送消息的表单，消息不能超过 300 字符。
class ChatForm(FlaskForm):
    body = TextAreaField('发送消息',
        validators=[Length(1, 300, message='消息过长，请限制在150字内')])
    submit = SubmitField('发送')

# ---------------------------------------------------------------------------
# 用户设置文件共享属性的表单。
class SetShareForm(FlaskForm):
    password = StringField(
        '请设置共享密码（0~4位），'
        '留空则其他用户可直接下载',
        validators=[Length(0,4,message="共享密码不能超过 4 位")])
    submit = SubmitField('确定')

# ----------------------------------------------------------------------------
# 用户下载/Fork其他用户的资源时，输入提取码的验证表单。
class ConfirmShareForm(FlaskForm):
    password = StringField('请输入提取码（1~4位）',
                           validators=[Required()])
    submit = SubmitField('确定')

# ----------------------------------------------------------------------------
# 用户创建文件夹表单
class NewFolderForm(FlaskForm):
    foldername = StringField("文件夹名",
        validators=[Required(),
                    Length(1, 64, message='文件夹名长度不能超过 64 个 ASCII 字符')])
    body = TextAreaField("目录描述（回车和多余空字符将被过滤）")
    share = BooleanField("分享此目录")
    submit = SubmitField('新建')

    def validate_body(self, field):     # 限制资源描述在 200 字符内
        if len(field.data) > 200:
            raise ValidationError('描述过长，请限制在100字内')