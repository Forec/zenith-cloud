import os
from app import create_app, db
from app.models import User, Role, File, Permission, \
    Comment, CFILE, Message
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app('development')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
	return dict(app = app,
				db = db,
				User = User,
				Role = Role,
				File = File,
                CFILE= CFILE,
                Comment = Comment,
                Message = Message,
				Permission=Permission)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)

@manager.command
def test():
	"""Run the unit tests"""
	import unittest
	tests = unittest.TestLoader().discover("tests")
	unittest.TextTestRunner(verbosity=2).run(tests)

@manager.command
def init():
	'''Init the database'''
	db.drop_all()
	db.create_all()
	Role.insert_roles()
	u = User(email='forec@bupt.edu.cn',\
			 nickname = 'forec',\
			 password = 'TESTTHISPASSWORD',\
			 confirmed = True,\
			 role = Role.query.filter_by(name='Administrator').first(),\
			 about_me = 'Wait for updating')
	db.session.add(u)
	db.session.commit()
	CFILE.generate_fake(5)
	User.generate_fake(5)
	File.generate_fake(100)
	Comment.generate_fake(50)
	Message.generate_fake(30)

if __name__ == "__main__":
	manager.run()