# 顶点云在 Linux 环境下的安装脚本

git clone https://github.com/Forec/cloud-storage-webserver.git
mv cloud-storage-webserver cloud
cd cloud
mkdir venv
cd venv
python3 -m venv .
cd ..
source venv/bin/activate
pip3 install -r requirements.txt --index-url https://pypi.douban.com/simple
pip3 install gunicorn --index-url https://pypi.douban.com/simple
deactivate
source venv/bin/activate
python3 manager.py simple_init
gunicorn -w 4 -b 127.0.0.1:5001 --worker-connections 100 wsgi:app