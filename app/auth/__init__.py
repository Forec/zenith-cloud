# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：auth 蓝本的初始化脚本

from flask import Blueprint

# 注册 auth 蓝本
auth = Blueprint('auth', __name__)

from . import views