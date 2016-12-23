.. _web-installation:

部署顶点云 Web 服务器
=====================

顶点云的 Web 服务器使用 Python3 编写，基于 Flask 框架，在部署前请确保您已经安装 Python3、Pip、Pyvenv 等，并已正确设置环境变量。我们推荐的 Python3 版本为 Python 3.5.0。有关 Python3 和 Flask 的介绍不在本文档范围内，如果您尚不了解，请参阅以下相关链接：

-	`Python3 快速上手指南 <https://docs.python.org/3/tutorial/index.html>`_
-	`Pip 安装指南 <https://pip.pypa.io/en/stable/installing/>`_
-	`Pyvenv 使用指南 <https://docs.python.org/3/library/venv.html>`_
-	`Flask 文档 <http://flask.pocoo.org/docs/0.12/>`_

获取源码
-------------

顶点云的 Web 服务器源码托管在 `GitHub <https://github.com/Forec/zenith-cloud>`_ 上，您可以使用 Git 克隆仓库或直接通过 GitHub 下载源码的压缩包。假设您熟悉 Git，请通过以下命令获取源码。

.. code-block:: shell
    
    git clone https://github.com/Forec/zenith-cloud.git
    cd zenith-cloud/web/
    
此时您应当已经进入顶点云 Web 服务器源码目录。

安装第三方支持
-------------------

顶点云 Web 服务器使用到的所有第三方库均包含在需求文件 ``web/requirements.txt`` 中，您有两种方式部署。

一键部署脚本
>>>>>>>>>>>>>>>>>>

顶点云 Web 服务器为 Linux 提供了一键部署脚本，它位于 ``web/settings`` 下。您可以运行以下命令。

.. code-block:: shell
    
    cd settings
    ./setup.sh
	
如果您使用 Windows 系统，请参考下方的手动配置，或者如果您使用 Git Command，可以在 Git 的 Bash 命令行中运行 `setup.sh` 。
	
如果您的 Python 环境工作正常并且网络畅通，您应该可以看到终端中没有提示任何信息并且显示 *部署完成* 字样。

手动部署
>>>>>>>>>>>>>>>

您可以选择手动部署顶点云 Web 服务器，流程如下：

.. code-block:: shell

	mkdir venv
	python3 -m venv venv/
	source venv/bin/activate		// Windows 系统此步骤为 venv/Scripts/activate.bat
	pip3 install -r requirements.txt --index-url https://pypi.douban.com/simple
	pip3 install gunicorn --index-url https://pypi.douban.com/simple
	python3 manager.py simple_init
	deactivate
	
如果您的 Python 环境工作正常并且网络畅通，此时顶点云的 Web 服务器应当已经部署完毕。

运行测试
----------------

顶点云的 Web 服务器提供了一部分单元测试，您可以运行单元测试以确保环境配置正常。

进入 `web` 目录，运行 `python3 manage.py test` 。若测试结果显示通过则顶点云 Web 服务器部署成功。

顶点云的 Web 服务器可运行在任何主流体系结构计算机以及任何操作系统上。接下来请您阅读 :ref:`web-config` 以根据您的系统配置顶点云 Web 服务器。


