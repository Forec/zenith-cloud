from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, \
    BooleanField, SelectField, FileField
from wtforms.validators import Required, Length, Email, Regexp, ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User, File

class EditProfileForm(FlaskForm):
    nickname = StringField('昵称', validators=[Length(0, 64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')

class EditProfileAdminForm(FlaskForm):
    email = StringField('电子邮箱', validators=[Required(), Length(5,64), Email()])
    nickname = StringField('昵称', validators=[Required(), Length(1, 64)])
    confirmed = BooleanField('已验证邮箱')
    role = SelectField('身份', coerce=int)
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已注册.')

    def validate_nickname(self, field):
        if field.data != self.user.nickname and \
                User.query.filter_by(nickname=field.data).first():
            raise ValidationError('该昵称已被使用.')

class FileForm(FlaskForm):
    file = FileField('', validators=[Required()])
    body = TextAreaField("资源描述（回车和多余空字符将被过滤）", validators=[Required()])
    submit = SubmitField('确定上传')
    def validate_body(self, field):
        if len(field.data) > 200:
            raise ValidationError('描述过长，请限制在200字内')

class FileDeleteConfirmForm(FlaskForm):
    filename = StringField("文件名", validators=[Required(), Length(1, 128)])
    body = TextAreaField("资源描述（回车和多余空字符将被过滤）", validators=[Required()])
    submit = SubmitField('修改')
    def validate_body(self, field):
        if len(field.data) > 200:
            raise ValidationError('描述过长，请限制在200字内')

class CommentForm(FlaskForm):
    body = StringField('添加评论', validators=[Required()])
    submit = SubmitField('提交')

class SearchForm(FlaskForm):
    key = StringField('搜索', validators=[])

class ChatForm(FlaskForm):
    body = TextAreaField('发送消息', validators=[Length(0, 300)])
    submit = SubmitField('发送')
    def validate_body(self, field):
        if len(field.data) > 300:
            raise ValidationError('消息过长，请限制在300字内')

class SetShareForm(FlaskForm):
    password = StringField('请设置共享密码（0~4位）',
                           validators=[Length(0,4, message="共享密码不能超过 4 位")])
    submit = SubmitField('确定')
