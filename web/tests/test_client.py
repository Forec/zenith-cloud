import unittest, re
from flask import url_for
from app import create_app, db
from app.models import User, Role

class FlaskClientTestCase(unittest.TestCase):
	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.drop_all()
		db.create_all()
		Role.insert_roles()
		self.client=self.app.test_client(use_cookies= True)

		# 注册新用户
		response = self.client.post(url_for('auth.register'), data={
			'email': 'test@forec.cn',
			'nickname': 'test',
			'password': 'cattt',
			'password2': 'cattt'})
		# 使用新注册用户登录
		response = self.client.post(url_for('auth.login'), data={
			'email': 'test@forec.cn',
			'password': 'cattt',
			'remember_me' : False
			}, follow_redirects=True)
		# 发送确认令牌
		user = User.query.filter_by(email='test@forec.cn').first()
		token = user.generate_confirmation_token()
		response = self.client.get(url_for('auth.confirm', token = token),
				follow_redirects = True)
		
	def tearDown(self):
		# 登出
		response = self.client.get(url_for('auth.logout'), follow_redirects=True)
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	# 测试主页
	def test_index_page(self):
		response = self.client.get(url_for('main.index'))
		self.assertTrue('顶点云' in response.get_data(as_text=True))

	# 测试介绍页
	def test_home_page(self):
		response = self.client.get(url_for('main.home'))
		self.assertTrue('专为北邮人' in response.get_data(as_text=True))

	# 测试注册、登录、登出
	def test_register_and_login(self):
		# 登出
		response = self.client.get(url_for('auth.logout'), follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('您已经登出' in data)
		
		# 注册新用户
		response = self.client.post(url_for('auth.register'), data={
			'email': 'forec_test@forec.cn',
			'nickname': 'forec_test',
			'password': 'cattt',
			'password2': 'cattt'})
		self.assertTrue(response.status_code == 302)

		# 使用新注册用户登录
		response = self.client.post(url_for('auth.login'), data={
			'email': 'forec_test@forec.cn',
			'password': 'cattt',
			'remember_me' : False
			}, follow_redirects=True)
		data = response.get_data(as_text = True)
		self.assertTrue(re.search('forec_test', data))
		self.assertTrue('您的帐户尚未通过验证' in data)
		
		# 发送确认令牌
		user = User.query.filter_by(email='forec_test@forec.cn').first()
		token = user.generate_confirmation_token()
		response = self.client.get(url_for('auth.confirm', token = token),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('您已经验证了您的邮箱' in data)		

	# 测试云盘新建文件夹操作
	def test_clouds(self):
		# 测试我的云盘主界面
		response = self.client.get(url_for('main.cloud', path='/'), follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('当前路径' in data)

		# 测试创建文件夹界面
		response = self.client.get(url_for('main.newfolder', path='/'),
								   follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('创建新文件夹' in data)
		
		# 测试创建私有新文件夹 test1(id = 1)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test1',
			'body': 'this is test1'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test1' in data)

		# 测试创建共享新文件夹 test2(id = 2)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test2',
			'body': 'this is test2',
			'share': True
			}, follow_redirects=True)	# 重定向 main.set_share
		data= response.get_data(as_text=True)
		self.assertTrue('设置共享密码' in data)

		# 设置共享密码
		response = self.client.post(url_for('main.set_share', id=2), data={
			'password': '1234'
			}, follow_redirects=True)	 # 重定向到 main.index
		data = response.get_data(as_text=True)
		self.assertTrue('共享密码为 1234' in data)

	# 测试复制
	def test_copy(self):
		# 创建私有新文件夹 test1(id = 1)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test1',
			'body': 'this is test1'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test1' in data)

		# 拷贝界面
		response = self.client.get(url_for('main.copy',
										   path='/',
										   id=1,
										   order='time',
										   ),
								   follow_redirects=True)
		data = response.get_data(as_text = True)
		self.assertTrue('确认拷贝' in data)

		# 拷贝操作执行
		user = User.query.filter_by(email='test@forec.cn').first()
		token = user.generate_copy_token(fileid=1, _path='/', expiration=3600)
		response = self.client.get(url_for('main.copy_check',
										   token=token),
								   follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('已拷贝到' in data and '文件夹' in data)

	# 测试移动
	def test_move(self):
		# 创建私有新文件夹 test1(id = 1)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test1',
			'body': 'this is test1'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test1' in data)

		# 移动界面
		response = self.client.get(url_for('main.move',
										   path='/',
										   id=1,
										   order='time',
										   ),
								   follow_redirects=True)
		data = response.get_data(as_text = True)
		self.assertTrue('确认移动' in data)

		# 移动操作执行
		user = User.query.filter_by(email='test@forec.cn').first()
		token = user.generate_move_token(fileid=1, _path='/', expiration=3600)
		response = self.client.get(url_for('main.move_check',
										   token=token),
								   follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('已移动到' in data and '文件夹' in data)

	# 测试 Fork
	def test_fork(self):
		# 创建共享新文件夹 test1(id = 1)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test1',
			'body': 'this is test1',
			'share': True
			}, follow_redirects=True)	 # 重定向 main.set_share
		data= response.get_data(as_text=True)
		self.assertTrue('设置共享密码' in data)

		# 设置共享密码
		response = self.client.post(url_for('main.set_share', id=1), data={
			'password': '1234'
			}, follow_redirects=True)	 # 重定向到 main.index
		data = response.get_data(as_text=True)
		self.assertTrue('共享密码为 1234' in data)

		# 无法 Fork 自己的文件
		response = self.client.get(url_for('main.fork',
										   id=1,
										   ),
								   follow_redirects=True)
		data = response.get_data(as_text = True)
		self.assertTrue('您无法 Fork 自己的文件' in data)		 

		# 验证 fork_do 同样无法 Fork 自己的文件
		response = self.client.get(url_for('main.fork_do',
										   id = 1,
										   _pass='1234'
										   ),
								   follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('您无法 Fork 自己的文件' in data)

		# 登出
		response = self.client.get(url_for('auth.logout'), follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('您已经登出' in data)

		# 注册新用户
		response = self.client.post(url_for('auth.register'), data={
			'email': 'forec_test@forec.cn',
			'nickname': 'forec_test',
			'password': 'cattt',
			'password2': 'cattt'})
		self.assertTrue(response.status_code == 302)

		# 使用新注册用户登录
		response = self.client.post(url_for('auth.login'), data={
			'email': 'forec_test@forec.cn',
			'password': 'cattt',
			'remember_me' : False
			}, follow_redirects=True)
		data = response.get_data(as_text = True)
		self.assertTrue(re.search('forec_test', data))
		self.assertTrue('您的帐户尚未通过验证' in data)
		
		# 发送确认令牌
		user = User.query.filter_by(email='forec_test@forec.cn').first()
		token = user.generate_confirmation_token()
		response = self.client.get(url_for('auth.confirm', token = token),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('您已经验证了您的邮箱' in data)		
		
		# Fork 界面
		response = self.client.get(url_for('main.fork',
										   id=1,
										   ),
								   follow_redirects=True)
		data = response.get_data(as_text = True)
		self.assertTrue('请输入提取码' in data)

		# 输入正确提取码
		response = self.client.post(url_for('main.fork', id=1), data={
			'password': '1234'
			},follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('Fork 到' in data and '用户' in data)

		# 输入错误提取码到 Fork
		response = self.client.post(url_for('main.fork', id=1), data={
			'password': '0'
			},follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('提取码错误' in data)
		
		# 输入错误提取码到 Fork_do
		response = self.client.get(url_for('main.fork_do',
										   id = 1,
										   _pass='0'
										   ),
								   follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('提取码错误' in data)

		# 执行 Fork
		user = User.query.filter_by(email='forec_test@forec.cn').first()
		token = user.generate_fork_token(fileid=1,
										 _path='/',
										 _linkpass='1234',
										 expiration=3600)
		response = self.client.get(url_for('main.fork_check',
										   token= token),
								   follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('已 Fork 用户 test 的文件' in data)

		# 错误 Pass 进入 Fork
		user = User.query.filter_by(email='forec_test@forec.cn').first()
		token = user.generate_fork_token(fileid=1,
										 _path='/',
										 _linkpass='0',
										 expiration=3600)
		response = self.client.get(url_for('main.fork_check',
										   token= token),
								   follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('没有权限' in data)
		
