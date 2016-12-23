.. _app-installation:

部署顶点云应用程序服务器
=================================

顶点云的应用程序服务器使用 Go 语言编写，部署前请确保您已安装 Golang，并向环境变量中正确添加了 GOROOT、GOPATH 等记录。我们推荐的 Go 语言版本为 Go 1.7.3。有关 Go 语言的环境配置不在本文档范围内，如果您尚不了解，请参阅以下相关链接：

-	`安装 Golang <https://golang.org/doc/install>`_
-	`Go 语言文档 <https://golang.org/doc/>`_

获取源码
-------------

顶点云的应用程序服务器源码托管在 `GitHub <https://github.com/Forec/zenith-cloud>`_ 上，您可以使用 Git 克隆仓库或直接通过 GitHub 下载源码的压缩包。假设您熟悉 Git，请通过以下命令获取源码。

**请注意** ：顶点云的 GitHub 仓库中包含了应用程序服务器和 Web 服务器两部分，因为 Go 语言要求编译的包需要在 `GOPATH` 目录下，因此你需要将 `app` 目录移动到 `GOPATH` 下，并将其重命名为 `cloud-storage` 。

.. code-block:: shell
    
    git clone https://github.com/Forec/zenith-cloud.git
	cd zenith-cloud
	mv app $GOPATH/cloud-storage
    cd $GOPATH/cloud-storage
    
此时您应当已经进入顶点云的应用程序服务器源码目录。

安装第三方库
-------------------

顶点云默认使用的数据库为 SQLITE3，使用了第三方的 go-sqlite3 库，请确保您已正确安装 Golang，并执行以下命令安装第三方库。

.. code-block:: shell
    
    go get github.com/mattn/go-sqlite3
    
运行测试
----------------

顶点云的应用程序服务器提供了一部分单元测试，您可以运行单元测试以确保环境配置正常。

进入 `app/test` 目录，运行 `runtest.sh` （Linux 系统）或 `runtest.bat` （Windows系统）。若测试结果显示通过则顶点云的应用程序服务器部署成功。

至此，顶点云应用程序已部署完成。顶点云可运行在任何主流体系结构计算机以及任何操作系统上。接下来请您阅读 :ref:`app-config` 以根据您的系统配置顶点云。
