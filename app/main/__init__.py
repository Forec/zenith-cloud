# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：初始化 main 蓝本

from flask import Blueprint
from . import views, errors
from ..models import Permission

# 注册蓝本
main = Blueprint('main', __name__)

# 注册上下文权限管理
@main.app_context_processor
def inject_permissions():
    return dict(Permission = Permission)