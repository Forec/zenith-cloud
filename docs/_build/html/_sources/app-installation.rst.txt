.. _app-installation:

部署顶点云应用程序服务器
=================================

顶点云的应用程序服务器使用 Go 语言编写，部署前请确保您已安装 Golang，并向环境变量中正确添加了 GOROOT、GOPATH 等记录。我们推荐的 Go 语言版本为 Go 1.7.3。有关 Go 语言的环境配置不在本文档范围内，如果您尚不了解，请参阅以下相关链接：

-	`安装 Golang <https://golang.org/doc/install>`_
-	`Go 语言文档 <https://golang.org/doc/>`_

获取源码
-------------

顶点云的应用程序服务器源码托管在 `GitHub <https://github.com/Forec/zenith-cloud>`_ 上，您可以使用 Git 克隆仓库或直接通过 GitHub 下载源码的压缩包。假设您熟悉 Git，请通过以下命令获取源码。

.. code-block:: shell
    
    git clone https://github.com/Forec/zenith-cloud.git
    cd zenith-cloud/app/
    
此时您应当已经进入顶点云的应用程序服务器源码目录。

安装第三方库
-------------------

顶点云默认使用的数据库为 SQLITE3，使用了第三方的 go-sqlite3 库，请确保您已正确安装 Golang，并执行以下命令安装第三方库。

.. code-block:: shell
    
    go get github.com/mattn/go-sqlite3

至此，顶点云应用程序已部署完成。顶点云可运行在任何主流体系结构计算机以及任何操作系统上。接下来请您阅读 :ref:`app-config` 以根据您的系统配置顶点云。
