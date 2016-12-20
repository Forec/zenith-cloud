# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：包含了 auth 蓝本中使用到的全部 wtf 表单

from ..models    import User
from flask_wtf   import FlaskForm
from flask_login import current_user
from wtforms     import StringField, PasswordField, \
                        BooleanField, SubmitField
from wtforms     import ValidationError
from wtforms.validators import Required, Length, \
                               Email, EqualTo

# -------------------------------------------------------------
# LoginForm 为用户登录表单
class LoginForm(FlaskForm):
    email = StringField('电子邮箱', validators=
        [Required(), Email(message='您使用的电子邮箱不合法！')])
    password = PasswordField('密码', validators=
        [Required(), Length(4,
                            64,
                            message='密码长度必须为 4 ~ 64 个字符')])
    remember_me = BooleanField('保持登陆')
    submit = SubmitField('登陆')

# ----------------------------------------------------------------
# RegistrationForm 为用户注册表单
class RegistrationForm(FlaskForm):
    email = StringField('电子邮箱', validators=
        [Required(), Email(message='您使用的电子邮箱不合法！')])
    nickname = StringField('昵称', validators=
        [Required(),Length(4,
                           64,
                           message='昵称长度必须为 4 ~ 64 个字符')])
    password = PasswordField('密码', validators=
        [Required(), EqualTo('password2',
                             message='两次输入密码不一致')])
    password2 = PasswordField('确认密码',
                              validators=[Required()])
    submit = SubmitField('注册')

    # 验证邮箱是否已被注册
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')

    # 验证昵称是否已被使用
    def validate_nickname(self, field):
        if User.query.filter_by(nickname=field.data).first():
            raise ValidationError('该昵称已被使用')

# -----------------------------------------------------------------
# ChangePasswordForm 为用户修改密码表单
class ChangePasswordForm(FlaskForm):
    oldPassword = PasswordField('旧密码', validators=
        [Required(), Length(4,
                            64,
                            message='密码长度必须为 4 ~ 64 个字符')])
    newPassword = PasswordField('新密码', validators=
        [Required(), Length(4,
                            64,
                            message="密码长度必须为 4 ~ 64 个字符")])
    newPassword2 = PasswordField('确认新密码', validators=
        [Required(),
         Length(4, 64, message="密码长度必须为 4 ~ 64 个字符"),
         EqualTo('newPassword', message = '两次输入密码不一致')])
    submit = SubmitField('修改')

    # 验证新密码是否与原密码相同
    def validate_newPassword(self, field):
        if current_user.verify_password(field.data):
            raise ValidationError('新密码不能与原密码相同')

# -----------------------------------------------------------------
# ChangeProfileForm 为用户修改个人资料表单
class ChangeProfileForm(FlaskForm):
    newNickname = StringField('新昵称', validators=
        [Required(), Length(4,
                            64,
                            message='昵称长度必须为 4 ~ 64 个字符')])
    password = PasswordField('输入密码', validators=
        [Required(), Length(4,
                            64,
                            message='密码长度必须为 4 ~ 64 个字符')])
    submit = SubmitField('修改')

    # 验证昵称未被使用
    def validate_newNickname(self, field):
        if User.query.filter_by(nickname=field.data).first():
            raise ValidationError('非常抱歉，该昵称已被使用。')

# --------------------------------------------------------------------
# ChangeEmailForm 为用户修改邮箱表单
class ChangeEmailForm(FlaskForm):
    email = StringField('新电子邮箱地址', validators=
        [Required(), Email(message='您输入的电子邮箱不合法！')])
    password = PasswordField('输入密码', validators=
        [Required(), Length(4,
                            64,
                            message='密码长度必须为 4 ~ 64 个字符')])
    submit = SubmitField('修改')

    # 验证用户试图更换的邮箱尚未被注册
    def validate_newEmail(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该电子邮箱已被注册')

# ---------------------------------------------------------------------
# PasswordResetRequestForm 为用户申请重置密码表单
class PasswordResetRequestForm(FlaskForm):
    email = StringField('注册时使用的电子邮箱', validators=
        [Required(), Email(message='您输入的电子邮箱地址不合法！')])
    submit = SubmitField('重置密码')

# ---------------------------------------------------------------------
# PasswordResetForm 为用户重置密码表单
class PasswordResetForm(FlaskForm):
    email = StringField('电子邮箱', validators=
        [Required(), Email(message='您输入的电子邮箱不合法！')])
    password = PasswordField('新密码', validators=
        [Required(), EqualTo('password2',
                             message='两次输入密码不一致')])
    password2 = PasswordField('确认密码', validators=[Required()])
    submit = SubmitField('重置密码')

    # 确定电子邮箱是否已注册
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('未知的电子邮箱')