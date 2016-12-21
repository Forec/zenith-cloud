# 顶点云在 Windows 环境下的配置脚本

cd ..
mkdir venv
cd venv
python3 -m venv .
cd ..
venv/Scripts/activate.bat
pip3 install -r requirements.txt --index-url https://pypi.douban.com/simple
pip3 install gunicorn --index-url https://pypi.douban.com/simple
deactivate
venv/Scripts/activate.bat
python3 manager.py simple_init
deactivate
echo 部署完成
