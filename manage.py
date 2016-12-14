from app import create_app, db
from app.models import User, Role, File, Permission, \
    Comment, CFILE, Message
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app('development')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app,
                db=db,
                User=User,
                Role=Role,
                File=File,
                CFILE=CFILE,
                Comment=Comment,
                Message=Message,
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
    u = User(email='forec@bupt.edu.cn', \
             nickname='Admin', \
             password='TESTTHISPASSWORD', \
             confirmed=True, \
             role=Role.query.filter_by(name='Administrator').first(), \
             about_me='Wait for updating')
    db.session.add(u)
    u = User(email='test@test.com', \
             nickname='testuser', \
             password='test', \
             confirmed=True, \
             role=Role.query.filter_by(name='User').first(), \
             about_me='this is a test user')
    db.session.add(u)
    db.session.commit()
    CFILE.generate_fake(5)
    User.generate_fake(5)
    File.generate_fake(100)
    Comment.generate_fake(70)
    Message.generate_fake(100)

@manager.command
def simple_init():
    '''Simple Init the database'''
    db.drop_all()
    db.create_all()
    Role.insert_roles()
    u = User(email='forec@bupt.edu.cn', \
             nickname='Administrator', \
             password='cloud-storage', \
             confirmed=True, \
             role=Role.query.filter_by(name='Administrator').first(), \
             about_me='顶点云管理员')
    db.session.add(u)
    u = User(email='test@test.com', \
             nickname='测试者', \
             password='cloud-storage', \
             confirmed=True, \
             role=Role.query.filter_by(name='User').first(), \
             about_me='欢迎来到顶点云的线上测试')
    db.session.add(u)
    db.session.commit()

if __name__ == "__main__":
    manager.run()
