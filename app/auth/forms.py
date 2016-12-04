from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
    email = StringField('电子邮箱', validators=[Required(),
                                             Length(5, 64),
                                             Email()])
    password = PasswordField('密码', validators=[Required(),
                                                     Length(4,64)])
    remember_me = BooleanField('保持登陆')
    submit = SubmitField('登陆')

class RegistrationForm(FlaskForm):
    email = StringField('电子邮箱', validators=[Required(),
                                             Length(5,64),
                                             Email()])
    username = StringField('用户名', validators=[Required(),
            Length(4,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
            '用户名仅能包含字母、数字和下划线')])
    password = PasswordField('密码', validators=[Required(),
            EqualTo('password2', message='两次输入密码不一致')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('注册')
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')

class ChangePasswordForm(FlaskForm):
    oldPassword = PasswordField('旧密码', validators=[Required(),
                                                            Length(4,64)])
    newPassword = PasswordField('新密码', validators=[Required(),
                Length(4,64)])
    newPassword2 = PasswordField('确认新密码', validators=[Required(),
                Length(4,64),EqualTo('newPassword', message = '两次输入密码不一致')])
    submit = SubmitField('修改')
    def validate_newPassword(self, field):
        if current_user.verify_password(field.data):
            raise ValidationError('新密码不能与原密码相同')


class ChangeProfileForm(FlaskForm):
    newUsername = StringField('新用户名', validators=[Required(),
            Length(4,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
            '用户名仅能包含字母、数字和下划线')])
    password = PasswordField('输入密码', validators=[Required(),
                                                            Length(4,64)])
    submit = SubmitField('修改')
    def validate_newUsername(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用.')


class ChangeEmailForm(FlaskForm):
    email = StringField('新电子邮箱地址', validators=[Required(),
            Length(5,64), Email()])
    password = PasswordField('输入密码', validators=[Required(),
                                                            Length(4,64)])
    submit = SubmitField('修改')
    def validate_newEmail(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该电子邮箱已被注册')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('注册时使用的电子邮箱', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField('重置密码')

class PasswordResetForm(FlaskForm):
    email = StringField('电子邮箱', validators=[Required(), Length(5, 64),
                                             Email()])
    password = PasswordField('新密码', validators=[
        Required(), EqualTo('password2', message='两次输入密码不一致')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('重置密码')
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('未知的电子邮箱')