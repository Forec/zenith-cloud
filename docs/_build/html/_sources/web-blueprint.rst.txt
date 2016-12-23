.. _web-blueprint:

蓝本介绍
==========

此部分文档主要介绍顶点云 Web 服务器中的两个蓝本： `main` 以及 `auth` ，以及如何创建新的自定义蓝本。

.. _web-blueprint-auth:

Auth 蓝本
----------------

此蓝本主要用于授权用户，如注册、登录、重置密码等。蓝本位于 `web/app/auth` 目录下，结构为：

.. code-block:: shell

   - auth
     - __init__.py
     - forms.py
     - views.py
     
上面三个文件中， `__init__.py` 用于初始化蓝本 Auth，`forms.py` 定义了 Auth 蓝本视图函数需要使用的表单类，`views.py` 具体处理转发给 Auth 蓝本的请求。

下面简单介绍 `forms.py` 中提供的表单，对于 `views.py` 中的视图函数，请查阅 :ref:`web-viewfunction-auth` 。

`forms.py` 提供了如下表单：

* `LoginForm` ：用户登录界面填写的表单
* `RegistrationForm` ：用户注册界面填写的表单，顶点云默认关闭了注册接口，你需要参考 :ref:`web-quickstart-expand` 来开启此接口
* `ChangePasswordForm` ：用户修改密码时填写的表单
* `ChangeEmailForm` ：用户修改邮箱时填写的表单
* `PasswordResetForm` ：用户重置密码时填写的表单
* `PasswordResetRequestForm` ：用户申请重置密码时填写的表单

.. _web-blueprint-main:

Main 蓝本
----------------

此蓝本主要用于处理用户服务请求。蓝本位于 `web/app/main` 目录下，结构为：

.. code-block:: shell

   - main
     - __init__.py
     - forms.py
     - views.py
     - errors.py
     
上面三个文件中， `__init__.py` 用于初始化蓝本 Main，`forms.py` 定义了 Main 蓝本视图函数需要使用的表单类，`views.py` 具体处理转发给 Main 蓝本的请求，`errors.py` 处理用户遇到的错误并使用服务器模板渲染错误界面。

下面简单介绍 `forms.py` 中提供的表单，对于 `views.py` 中的视图函数，请查阅 :ref:`web-viewfunction-main` 。

`forms.py` 提供了如下表单：

* `EditProfileForm` ：用户编辑个人资料界面填写的表单
* `EditProfileAdminForm` ：管理员编辑其他用户个人资料界面填写的表单
* `UploadForm` ：用户上传文件时填写的表单
* `CommentForm` ：用户评论文件时填写的表单
* `SearchForm` ：用户搜索文件时填写的表单
* `FileDeleteConfirmForm` ：用户确认删除文件时填写的表单
* `ChatForm` ：用户聊天界面的对话框
* `SetShareForm` ：用户设置文件共享和提取码时填写的表单
* `ConfirmShareForm` ：用户对其他用户的共享文件执行 Fork、下载等操作前填写提取码的表单
* `NewFolderForm` ：用户创建新文件夹时填写的表单

自定义蓝本
-----------------------

关于蓝本的概念不属于本文档讨论范围，如果您尚不了解，可以参考 `Flask 文档中关于蓝本的部分 <http://flask.pocoo.org/docs/0.12/search/?q=blueprint>`_ 。

对于顶点云，如果您需要添加自定义蓝本，请在目录 `web/app` 下创建新的蓝本目录并添加您的自定义路由。

接下来请您阅读 :ref:`web-models` 。
