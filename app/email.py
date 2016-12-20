# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：邮件发送相关函数

from . import mail
from threading import Thread
from flask_mail import Message
from flask import current_app, render_template

# 异步发送邮件
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

# 发送邮件函数
def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['ZENITH_MAIL_SUBJECT_PREFIX'] + \
                        ' ' + subject,
                  sender=app.config['ZENITH_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])

    # 启动异步线程发送邮件
    thr.start()
    return thr
