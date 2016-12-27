# 作者：Forec
# 最后修改日期：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：此文件包含了服务器认证部分的视图函数，包括登录、注册、密码重置等。
# 蓝本：auth

from flask       import render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, login_required, logout_user, current_user
from .           import auth
from .forms      import LoginForm, RegistrationForm, ChangePasswordForm,\
                        ChangeEmailForm, PasswordResetForm, \
                        PasswordResetRequestForm
from .. import db
from ..models import User
from ..email import send_email


# ----------------------------------------------------------------
# rules 函数提供了 “注册须知” 界面的入口
@auth.route('/rules')
def rules():
    return render_template('auth/rules.html')

# ----------------------------------------------------------------
# login 函数提供了登录界面入口
@auth.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index', _external=True))
    form  = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
                email = form.email.data
        ).first()
        if user is not None and \
            user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or \
                    url_for('main.index', _external=True))
        flash('错误的用户名或密码')
    return render_template('auth/login.html', form = form)

# -----------------------------------------------------------------
# logout 函数提供了登出操作，登出后默认重定向到登陆入口
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已经登出')
    return redirect(url_for('auth.login', _external=True))

# ------------------------------------------------------------------
# register 函数提供了注册入口
@auth.route('/register', methods = ['GET', 'POST'])
def register():
    # 展示状态，禁止注册
    # return render_template('auth/testing.html', _external=True)

    form = RegistrationForm()
    if current_user.is_authenticated:
        flash('您已经登陆，登陆状态下无法注册')
        return redirect(url_for('main.index', _external=True))
    if form.validate_on_submit():
        user = User(email = form.email.data,
                    nickname = form.nickname.data,
                    password = form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,
                   '确认您的帐户',
                   'auth/email/confirm',
                   user=user,
                   token=token)
        flash('一封确认邮件已经发送到您填写的邮箱，'
              '请查看以激活您的帐号')
        login_user(user)
        return redirect('http://mail.'+user.email.split('@')[-1])
    return render_template('auth/register.html', form=form)

# -------------------------------------------------------------------
# confirm 函数提供了用户注册邮箱激活入口，根据向用户发送的激活链接尾部的
# token 校验用户是否合法。
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index', _external=True))
    if current_user.confirm(token):
        flash('您已经验证了您的邮箱！感谢您的支持！')
    else:
        flash('此验证链接无效或已过期！')
    return redirect(url_for('main.index', _external=True))

# --------------------------------------------------------------------
# resend_confirmation 用于在用户未收到激活邮件时重发。
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
        # 生成新的激活 token
    send_email(current_user.email,
               '确认您的帐户',
               'auth/email/confirm',
               user = current_user,
               token = token)
    flash('一封确认邮件已经发送到您注册时填写的邮箱，'
          '请查看以激活您的帐号')
    return redirect(url_for('main.index', _external=True))

# --------------------------------------------------------------------
# change_password 为用户修改密码的视图函数。
@auth.route('/change-password', methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.oldPassword.data):
            current_user.password = form.newPassword.data
            db.session.add(current_user)
            db.session.commit()
            flash('您的密码已更新')
            return redirect(url_for('main.index',
                                    _external=True))
        else:
            flash('密码错误')
    return render_template('auth/secure/change_password.html',
                           form = form)

# ----------------------------------------------------------------------
# change_email_request 为用户重置邮箱请求入口。
@auth.route('/change-email', methods = ['GET', 'POST'])
@login_required
def change_email_request():
    form =ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.\
                generate_email_change_token(new_email)
            send_email(new_email,
                       '确认您的邮箱',
                       'auth/email/change_email',
                       user = current_user,
                       token = token)
            flash('一封包含指导您激活新邮箱的'
                  '邮件已经发到您的新邮箱')
            return redirect(url_for('main.index',
                                    _external=True))
        else:
            flash('错误的的用户名或密码')
    return render_template("auth/secure/change_email.html",
                           form=form)

# --------------------------------------------------------------------
# change_email 用于验证用户重置邮箱后的激活链接。
@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('您的电子邮箱已经更新')
    else:
        flash('非法请求')
    return redirect(url_for('main.index',
                            _external=True))

# --------------------------------------------------------------------
# password_reset_request 为用户重置密码入口。
@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index',
                                _external=True))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
                email = form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email,
                       '重置您的密码',
                       'auth/email/reset_password',
                       user = user,
                       token = token,
                       next = request.args.get('next'))
            flash('一封指导您重置密码的邮件已经发送到您注册时'
                  '填写的邮箱，请查看邮件并重置您的密码')
            return redirect(url_for('auth.login',
                                    _external=True))
    return render_template('auth/reset_password.html',
                           form=form)

# -------------------------------------------------------------------
# password_reset 函数用于验证用户重置密码请求 token 的合法性。
@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index',
                                _external=True))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
                email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index',
                                    _external=True))
        if user.reset_password(token, form.password.data):
            flash('您的密码已经重置成功')
            return redirect(url_for('auth.login',
                                    _external=True))
        else:
            abort(403)
    return render_template('auth/reset_password.html',
                           form=form)

# ------------------------------------------------------------------
# secure_center 返回安全中心界面。
@auth.route('/secure_center')
@login_required
def secure_center():
    return render_template('auth/secure/secure_center.html')

# -------------------------------------------------------------------
# before_request 注册了用户未激活邮箱时的跳转接口。
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
           and request.endpoint[:5] != 'auth.' \
           and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed',
                                    _external=True))

# -------------------------------------------------------------------
# unconfirmed 函数提供了未验证的界面。
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index', _external=True))
    return render_template('auth/unconfirmed.html')
