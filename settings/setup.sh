# 顶点云在 Linux 环境下的配置脚本

cd ..
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
deactivate
echo 部署完成
