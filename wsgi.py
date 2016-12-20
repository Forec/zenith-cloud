# 作者：Forec
# 最后修改时间：2016-12-20
# 邮箱：forec@bupt.edu.cn
# 关于此文件：gunicorn 的执行脚本

from app import create_app

# 更改配置名称以切换环境
app = create_app('linux')

if __name__ == '__main__':
    app.run()