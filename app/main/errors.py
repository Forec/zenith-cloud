# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：包含了应用处理错误的视图函数

from . import main
from flask import render_template

# 处理 403 错误入口
@main.app_errorhandler(403)
def forbidden(e):
	return render_template('error/403.html'), 403

# 处理 404 错误入口
@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

# 处理 500 错误入口
@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('error/500.html'), 500