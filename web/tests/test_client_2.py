import unittest, re
from flask import url_for
from app import create_app, db
from app.models import User, Role

class ZENITHClientTestCase(unittest.TestCase):
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

	def test_rules(self):
		# 测试注册须知界面
		response = self.client.get(url_for('auth.rules'), follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('仔细阅读' in data)

	# 测试重置密码、修改邮箱、修改密码
	def test_reset_and_change(self):

        # 登录用户尝试访问安全中心
		response = self.client.get(url_for('auth.secure_center'),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('安全中心' in data)

        # 登录用户尝试访问修改密码界面
		response = self.client.get(url_for('auth.change_password'),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('更改密码' in data)

        # 登录用户用错误密码尝试修改密码
		response = self.client.post(url_for('auth.change_password'), data={
            'oldPassword':'test1',
            'newPassword':'test2',
            'newPassword2': 'test2'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('密码错误' in data)

        # 登录用户尝试修改密码
		response = self.client.post(url_for('auth.change_password'), data={
            'oldPassword':'cattt',
            'newPassword':'test2',
            'newPassword2': 'test2'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('您的密码已更新' in data)

		# 登录用户尝试违例访问重置页面
		user = User.query.filter_by(email='test@forec.cn').first()
		response = self.client.get(url_for('auth.password_reset', token = '123'),
				follow_redirects = True)
		data = response.get_data(as_text=True)  # 重定向到 main.index
		self.assertTrue('顶点云' in data)

		# 登出
		response = self.client.get(url_for('auth.logout'), follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('您已经登出' in data)

        # 未登录用户用错误密码尝试修改密码，当前正确密码为 test2
		response = self.client.post(url_for('auth.change_password'), data={
            'oldPassword':'test1',
            'newPassword':'test3',
            'newPassword2': 'test3'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('先登录' in data)

        # 未登录用户尝试修改密码
		response = self.client.post(url_for('auth.change_password'), data={
            'oldPassword':'test2',
            'newPassword':'test3',
            'newPassword2': 'test3'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('先登录' in data)

		# 忘记密码界面
		response = self.client.get(url_for('auth.password_reset_request'),
                        follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('重置密码' in data)

		# 申请重置密码
		response = self.client.post(url_for('auth.password_reset_request'), data={
			'email': 'test@forec.cn'
			}, follow_redirects=True)
		data = response.get_data(as_text = True)     # 重定向到登陆界面
		self.assertTrue('一封指导您' in data)

		# 尝试访问重置页面
		user = User.query.filter_by(email='test@forec.cn').first()
		token = user.generate_reset_token()
		response = self.client.get(url_for('auth.password_reset', token = token),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('重置密码' in data)

		# 发送确认令牌并重置密码
		user = User.query.filter_by(email='test@forec.cn').first()
		token = user.generate_reset_token()
		response = self.client.post(url_for('auth.password_reset', token = token),data={
            'email': 'test@forec.cn',
            'password': 'test1',
            'password2': 'test1'
            }, follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('重置成功' in data)

		# 未登录用户尝试违例 token 重置
		user = User.query.filter_by(email='test@forec.cn').first()
		response = self.client.post(url_for('auth.password_reset', token='123'), data ={
            'email': 'test@forec.cn',
            'password': 'hacker',
            'password2': 'hacker'
        }, follow_redirects = True)
		data = response.get_data(as_text=True)  # 403
		self.assertTrue('权限' in data)

		# 重新登录
		response = self.client.post(url_for('auth.login'), data={
			'email': 'test@forec.cn',
			'password': 'test1',
			'remember_me' : False
			}, follow_redirects=True)
		data = response.get_data(as_text=True)  # index
		self.assertTrue('我的云盘' in data)


        # 登录用户尝试访问修改邮箱界面
		response = self.client.get(url_for('auth.change_email_request'),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('修改电子邮箱' in data)

        # 登录用户用错误密码尝试修改邮箱
		response = self.client.post(url_for('auth.change_email_request'), data={
            'email':'test2@forec.cn',
            'password':'test2'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('密码错误' in data)

        # 登录用户用正确密码尝试修改邮箱
		response = self.client.post(url_for('auth.change_email_request'), data={
            'email':'test2@forec.cn',
            'password':'test1'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('已经发到您' in data)

		# 发送违例令牌以修改邮箱
		user = User.query.filter_by(email='test@forec.cn').first()
		response = self.client.get(url_for('auth.change_email', token = '123'),
                            follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('非法请求' in data)

		# 发送确认令牌以修改邮箱
		user = User.query.filter_by(email='test@forec.cn').first()
		token = user.generate_email_change_token('test2@forec.cn')
		response = self.client.get(url_for('auth.change_email', token = token),
                            follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('已经更新' in data)

		# 登出
		response = self.client.get(url_for('auth.logout'), follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('您已经登出' in data)

        # 未登录用户尝试访问修改邮箱界面
		response = self.client.get(url_for('auth.change_email_request'),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('先登录' in data)

        # 未登录用户用错误密码尝试修改邮箱
		response = self.client.post(url_for('auth.change_email_request'), data={
            'email':'test3@forec.cn',
            'password':'test2'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('先登录' in data)

		# 未登录用户发送确认令牌以修改邮箱，此时邮箱已经更新为 test2@forec.cn
		user = User.query.filter_by(email='test2@forec.cn').first()
		token = user.generate_email_change_token('test3@forec.cn;')
		response = self.client.get(url_for('auth.change_email', token = token),
                            follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('先登录' in data)

        # 未登录用户发送违例确认令牌以修改邮箱，此时邮箱已经更新为 test2@forec.cn
		user = User.query.filter_by(email='test2@forec.cn').first()
		response = self.client.get(url_for('auth.change_email', token = '123'),
                            follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('先登录' in data)

	def test_admin_and_view_share(self):

		# 普通用户创建私有新文件夹 test1(id = 1)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test1',
			'body': 'this is test1'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test1' in data)

		# 普通用户创建私有新文件夹 test2(id = 2)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test2',
			'body': 'this is test2'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test2' in data)

		# 普通用户进入编辑私有文件夹 test1(id = 1) 的界面
		response = self.client.get(url_for('main.edit_file', id=1),
                        follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('修改文件信息' in data)

		# 普通用户编辑私有文件夹 test1(id = 1)，并试图重命名为已存在文件test2
		response = self.client.post(url_for('main.edit_file', id=1), data={
			'filename': 'test2',
			'body': 'this is test1'
			}, follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('同名的文件' in data)

		# 普通用户编辑私有文件夹 test1(id = 1)，并试图修改文件名为 test3
		response = self.client.post(url_for('main.edit_file', id=1), data={
            'filename': 'test3',
			'body': 'this is test1'
			}, follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('目录信息已被更新' in data)

		# 普通用户编辑私有文件夹 test3(id = 1)，并试图修改文件名为 test1
		response = self.client.post(url_for('main.edit_file', id=1), data={
            'filename': 'test1',
			'body': 'this is test1'
			}, follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('目录信息已被更新' in data)

		# 普通用户在文件夹 test1(id = 1) 的界面中评论，评论 id = 1
		response = self.client.post(url_for('main.file', id=1), data={
			'body': 'this is test comment1'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test comment1' in data)

        # 屏蔽自己发布的评论
		response = self.client.get(url_for('main.moderate_comments_disable_own', id=1),
                    follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('评论已被设置为不可见' in data)

		# 普通用户在文件夹 test1(id = 1) 的界面中评论，评论 id = 2
		response = self.client.post(url_for('main.file', id=1), data={
			'body': 'this is test comment2'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test comment2' in data)

		# # 普通用户违例删除私有文件夹 test1(id = 1)
		# response = self.client.get(url_for('main.delete_file_confirm', token='123'),
         #                follow_redirects=True)
		# data= response.get_data(as_text=True)
		# self.assertTrue('权限' in data)

		# 普通用户直接删除私有文件夹 test1(id = 1)
		user = User.query.filter_by(email='test@forec.cn').first()
		token = user.generate_delete_token(fileid=1, expiration=3600)
		response = self.client.get(url_for('main.delete_file_confirm', token=token),
                        follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('成功删除' in data)

        # 登出
		response = self.client.get(url_for('auth.logout'), follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('您已经登出' in data)

		# 注册管理员用户
		response = self.client.post(url_for('auth.register'), data={
			'email': 'forec@bupt.edu.cn',
			'nickname': 'forec',
			'password': 'forecp',
			'password2': 'forecp'})

		# 使用新注册用户登录
		response = self.client.post(url_for('auth.login'), data={
			'email': 'forec@bupt.edu.cn',
			'password': 'forecp',
			'remember_me' : False
			}, follow_redirects=True)

		# 管理员用户无需确认

        # 访问管理页面
		response = self.client.get(url_for('main.moderate'),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('管理员' in data)

        # 访问管理文件页面
		response = self.client.get(url_for('main.moderate_files'),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('文件管理' in data)

        # 访问管理评论页面
		response = self.client.get(url_for('main.moderate_comments'),
				follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('评论管理' in data)

		# 创建私有新文件夹 test3(id = 3)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test3',
			'body': 'this is test3'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test3' in data)

        # 搜索管理文件界面
		response = self.client.post(url_for('main.moderate_files'), data={
            'key': 'test'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('test2' in data)

		# 在文件夹 test3(id = 3) 的界面中评论，评论 id = 3
		response = self.client.post(url_for('main.file', id=3), data={
			'body': 'this is test comment3'
			}, follow_redirects=True)	 # 重定向 main.file
		data= response.get_data(as_text=True)
		self.assertTrue('this is test comment3' in data)

        # 搜索管理文件界面
		response = self.client.post(url_for('main.moderate_comments'), data={
            'key': 'test'
            },follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('test comment' in data)

        # 屏蔽普通用户发布的评论
		response = self.client.get(url_for('main.moderate_comments_disable', id=2),
                    follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('评论管理' in data)     # 重定向 moderate_comments

        # 解屏蔽普通用户发布的评论
		response = self.client.get(url_for('main.moderate_comments_enable', id=1),
                    follow_redirects = True)
		data = response.get_data(as_text=True)
		self.assertTrue('评论管理' in data)     # 重定向 moderate_comments

		# 管理员用户进入编辑私有文件夹 test2(id = 2) 的界面
		response = self.client.get(url_for('main.edit_file', id=2),
                        follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('修改文件信息' in data)

		# 管理用户编辑私有文件夹 test2(id = 2)，并重命名为已存在文件test4
		response = self.client.post(url_for('main.edit_file', id=2), data={
			'filename': 'test4',
			'body': 'this is test2'
			}, follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('目录信息已被更新' in data)

		# 管理员用户直接删除私有文件夹 test4(id = 2)
		response = self.client.get(url_for('main.moderate_files_delete', id=2),
                        follow_redirects=True)
		data= response.get_data(as_text=True)
		self.assertTrue('成功删除' in data)

		# 管理员测试创建共享新文件夹 test4(id = 4)
		response = self.client.post(url_for('main.newfolder', path='/'), data={
			'foldername': 'test4',
			'body': 'this is test4',
			'share': True
			}, follow_redirects=True)	# 重定向 main.set_share
		data= response.get_data(as_text=True)
		self.assertTrue('设置共享密码' in data)

		# 管理员为 test4 设置共享密码
		response = self.client.post(url_for('main.set_share', id=4), data={
			'password': '1234'
			}, follow_redirects=True)	 # 重定向到 main.index
		data = response.get_data(as_text=True)
		self.assertTrue('共享密码为 1234' in data)

        # 登出
		response = self.client.get(url_for('auth.logout'), follow_redirects=True)
		data = response.get_data(as_text=True)
		self.assertTrue('您已经登出' in data)

        # 登录
		response = self.client.post(url_for('auth.login'), data={
			'email': 'test@forec.cn',
			'password': 'cattt',
			'remember_me' : False
			}, follow_redirects=True)

