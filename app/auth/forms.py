from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
    email = StringField('电子邮箱', validators=[Required(),
                                             Email(message='您使用的电子邮箱不合法！')])
    password = PasswordField('密码', validators=[Required(),
                                                     Length(4,64,message='密码长度必须为 4 ~ 64 个字符')])
    remember_me = BooleanField('保持登陆')
    submit = SubmitField('登陆')

class RegistrationForm(FlaskForm):
    email = StringField('电子邮箱', validators=[Required(),
                                             Email(message='您使用的电子邮箱不合法！')])
    nickname = StringField('昵称', validators=[Required(),Length(4,64, message='昵称长度必须为 4 ~ 64 个字符')])
    password = PasswordField('密码', validators=[Required(),
            EqualTo('password2', message='两次输入密码不一致')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('注册')
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')
    def validate_nickname(self, field):
        if User.query.filter_by(nickname=field.data).first():
            raise ValidationError('该昵称已被使用')

class ChangePasswordForm(FlaskForm):
    oldPassword = PasswordField('旧密码', validators=[Required(),
                                                            Length(4,64, message='密码长度必须为 4 ~ 64 个字符')])
    newPassword = PasswordField('新密码', validators=[Required(),
                Length(4,64)])
    newPassword2 = PasswordField('确认新密码', validators=[Required(),
                Length(4,64),EqualTo('newPassword', message = '两次输入密码不一致')])
    submit = SubmitField('修改')
    def validate_newPassword(self, field):
        if current_user.verify_password(field.data):
            raise ValidationError('新密码不能与原密码相同')


class ChangeProfileForm(FlaskForm):
    newNickname = StringField('新昵称', validators=[Required(),Length(4,64,message='昵称长度必须为 4 ~ 64 个字符')])
    password = PasswordField('输入密码', validators=[Required(),
                                                            Length(4,64,  message='密码长度必须为 4 ~ 64 个字符')])
    submit = SubmitField('修改')
    def validate_newNickname(self, field):
        if User.query.filter_by(nickname=field.data).first():
            raise ValidationError('非常抱歉，该昵称已被使用。')


class ChangeEmailForm(FlaskForm):
    email = StringField('新电子邮箱地址', validators=[Required(),
                    Email(message='您输入的电子邮箱不合法！')])
    password = PasswordField('输入密码', validators=[Required(),
                                                            Length(4,64, message='密码长度必须为 4 ~ 64 个字符')])
    submit = SubmitField('修改')
    def validate_newEmail(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该电子邮箱已被注册')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('注册时使用的电子邮箱',
                        validators=[Required(),
                                    Email(message='您输入的电子邮箱地址不合法！')])
    submit = SubmitField('重置密码')

class PasswordResetForm(FlaskForm):
    email = StringField('电子邮箱', validators=[Required(),
                                             Email(message='您输入的电子邮箱不合法！')])
    password = PasswordField('新密码', validators=[
        Required(), EqualTo('password2', message='两次输入密码不一致')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('重置密码')
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('未知的电子邮箱')