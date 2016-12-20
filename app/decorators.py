# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：自定义装饰器

from flask import abort
from functools import wraps
from flask_login import current_user
from .models import Permission

# 定义权限管理装饰器
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 定义管理员权限装饰器
def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)