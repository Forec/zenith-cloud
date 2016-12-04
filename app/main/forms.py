from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, \
    BooleanField, SelectField, FileField
from wtforms.validators import Required, Length, Email, Regexp, ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User, File

class EditProfileForm(FlaskForm):
    name = StringField('昵称', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    contactE = StringField('联系方式', validators=[Length(0,64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')

class EditProfileAdminForm(FlaskForm):
    email = StringField('电子邮箱', validators=[Required(), Length(5,64), Email()])
    username = StringField('昵称', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_]*$', 0,
                                          '用户名仅能包含字母、数字和下划线')])
    confirmed = BooleanField('Confirmed')
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

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用.')

class FileForm(FlaskForm):
    file = FileField("选择文件", validators=[Required()])
    body = TextAreaField("资源描述（回车和多余空字符将被过滤）", validators=[Required()])
    submit = SubmitField('确定上传')
    def validate_body(self, field):
        if len(field.data) > 200:
            raise ValidationError('描述过长，请限制在200字内')

class FileDeleteConfirmForm(FlaskForm):
    filename = StringField("文件名", validators=[Required(), Length(0, 128)])
    path = StringField("路径",  validators=[Required(), Length(0, 256)])
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