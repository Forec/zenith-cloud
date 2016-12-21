# 顶点云在 Linux 环境下的启动脚本

cd ..
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:5001 --worker-connections 100 wsgi:app
