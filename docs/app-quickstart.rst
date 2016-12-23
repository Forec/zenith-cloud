.. _app-quickstart:

快速上手
==========

此部分文档将带领您在一个假想的纯净环境中部署、配置、扩展自定义功能并启动顶点云服务器。

假想环境
---------

有一天我意外获得了一台免费的 CVM，而我恰巧获得了一次得到顶点云源码的机会。这台云主机使用的操作系统为 CentOS 7.2，公网 IP 地址为 ``123.123.123.123`` ，已安装好 Golang 并配置了环境变量。下面的指令均通过 SSH 远程操作。

.. code-block:: shell

    cd $GOPATH
    git clone https://github.com/Forec/zenith-cloud.git
	cd zenith-cloud
	mv app $GOPATH/cloud-storage
    cd $GOPATH/cloud-storage

我已经获得了顶点云应用程序服务器的源码，接下来安装第三方库。

.. code-block:: shell

    go get github.com/mattn/go-sqlite3

很高兴 Golang 顺利地配置了第三方库。接下来测试一下代码是否能够在本地机器通过测试。

.. code-block:: shell

	cd test
	./runtest.sh
	
非常顺利！测试脚本告诉我所有测试均已完成，顶点云应用程序各个基础模块能够在这台服务器上运转正常。

针对假想环境修改配置文件
--------------------------

鉴于顶点云提供的默认配置仅适用于 Forec 的史诗级笔记本，下面根据这台服务器的情况修改配置文件。编辑 `config.go` :

.. code-block:: shell

	cd ../config
	nano config.go
	
我根据如下考虑对配置文件做了一定修改：

* 我想将用户上传的文件存储到 ``/usr/local/cloud`` ，因此我修改 ``STORE_PATH = "/usr/local/cloud"`` 
* 我想让这台云主机上运行的服务器为 Linux 用户提供服务，因此修改 ``CLIENT_VERSION = "Linux"``
* 我的云主机网络情况良好并且带宽很高，因此我觉得可以适当提高缓冲区的大小，修改 ``AUTHEN_BUFSIZE = 4096`` ，修改 ``BUFSIZE = 3 * 4096 * 1024`` 
* 我觉得顶点云默认使用的 SQLITE 数据库很方便，因此我决定保留默认配置
* 我的服务器这么强，因此我将每个用户允许的最大同时连接线程数设置为 50
* 我觉得我的服务器可能会受到大家的热烈欢迎，因此我决定增加初始用户池大小，修改 ``START_USER_LIST = 100`` ，我想应该足够了。
* 我想让我的服务器更安全，因此我保留了默认配置中的最高安全等级
* 我想让世界上任何一个角落均能访问我的顶点云服务器，因此我将测试 IP 地址修改为 ``123.123.123.123``
* 我觉得剩下的配置没什么需要变动的了，不过每 5 秒转发一次消息似乎有些过慢了，因此我将 ``CHECK_MESSAGE_SEPERATE`` 修改为 2

看起来配置文件没什么值得修改的了，我决定按下 ``CTRL+X`` 保存配置文件，顺便通过 ``git diff`` 检查了一下修改过的部分：

.. code-block:: go
	
   const STORE_PATH = "/usr/local/cloud"
   const CLIENT_VERSION = "Linux"
   const AUTHEN_BUFSIZE = 4096
   const BUFLEN = 3 * 4096 * 1024
   const MAXTRANSMITTER = 50
   const START_USER_LIST = 100
   const TEST_SAFELEVEL = 3
   const TEST_IP = "123.123.123.123"
   const CHECK_MESSAGE_SEPERATE = 2
   
启动顶点云应用程序服务器
-----------------------------

看起来万事大吉了，我决定启动服务器看看究竟是否如此。

.. code-block:: shell

	cd ../cloud
	go build cloud.go
	./cloud
	
似乎运行成功了？我决定配置一下测试客户端，看看是否能够正常使用。

.. _app-quickstart-runtest-client:

运行测试客户端
-----------------

启动一个新的 SSH 连接，进入配置文件所在的目录，编辑配置文件。

配置文件中的默认用户测试密码实在是太长了，但是很无奈，为了方便不得不使用默认的数据库和测试用户。经过检查，我还需要设置测试客户端下载文件保存路径，因此我修改 ``DOWNLOAD_PATH = "/usr/local/cloud/download"`` 。

看起来似乎配置好了，我决定运行测试客户端尝试一下。

.. code-block:: shell
	
	cd client
	go build client.go && ./client
	
测试客户端提示我输入命令，看起来似乎运行正常。我决定做如下尝试（顶点云的默认测试客户端没有屏蔽服务器发送的保活信息，这一点会留在 :ref:`app-test-client-modify` 中作为教程，如果你在测试过程中觉得频繁出现的保活信息很困扰，可以注释掉 ``client/client.go`` 的第 70 行）。

.. code-block:: shell

	请输入命令：ls+0+/
	UID  PATH    FILE        CREATED TIME   SIZE   SHARED  MODE
	请输入命令：touch+test.txt+/home/+0
	xxxxxxxx
	请输入命令：put+1+13990+18459158D123788165BBB8C3F3DFDF91
	上传传输结束
	请输入命令：ls+1+/
	UID  PATH    FILE        CREATED TIME   SIZE   SHARED  MODE
	  1  /home/  client.go   xxxxxxxxxxxx   13990    0     FILE
	请输入命令：get+1+?
	文件 test.txt 已被下载
	  
我真的很讨厌 Forec 的这一套指令，冗长而且难懂。不过毕竟这里只是一个测试用的客户端，没有图形界面的包装。在尝试了专门设计的 `客户端`_ 后，我觉得效果还是可以接受的，不过这都是后话了。

我阅读了 :ref:`app-protocal` ，终于明白了上面指令的意义：

* 第一条 ``ls`` 指令用于获取目录 ``/`` 下的资源列表，在开始时数据库中没有任何记录，所以只有返回的表头。两个 ``+`` 之间的数字 0 代表只查询 ``/`` 一级目录下的文件
* 第二条 ``touch`` 指令创建了一个空文件，我创建了一个名为 ``test.txt`` 的空文件，后面的 ``/home/`` 代表我想将 ``test.txt`` 创建在我的云盘的 ``/home/`` 目录下。很高兴顶点云的服务器还算人性化，虽然我此前并没有创建过 ``home`` 目录，不过在执行完这条命令后，服务器为我同时创建了 ``home`` 目录和 ``test.txt`` 文件。最后一个数字 0 表示我创建的是一个文件而非目录。
* 第三条 ``put`` 指令向服务器中的一个文件上传数据，我将测试客户端当前路径下的文件 ``client.go`` 随手上传了。数字 1 代表要上传文件资源的编号，因为我刚刚开始使用顶点云，数据库还是空的，添加的第一条记录必然对应编号 1。它的文件大小是 13990 字节，根据 Forec 的协议计算出的 MD5 值为 18459158D123788165BBB8C3F3DFDF91。
* 第四条 ``ls`` 指令递归获取目录 ``/`` 下的资源。很高兴我看到了刚刚创建的文件，并且它的大小已经成了 13990 字节，路径也没有错误。
* 最后一条 ``get`` 指令，我决定下载刚刚上传的文件，看看是否真的可行。这里的数字 1 仍然是我要下载的文件编号，问号处其实可以填写任意非空值，这个参数只有在我想下载别人的文件时服务器才会检查。很高兴服务器提醒我下载成功了。

经过比对，顶点云服务器似乎基本的功能都执行正常。不过，我有更好的功能想添加。我通过 ``CTRL+C`` 结束掉了正在运行的服务器和测试客户端。

.. _app-quickstart-expand:

扩展自定义功能
-----------------

不得不说 Forec 的设计实在是太简陋了，至少客户端应该能够看到自己的昵称！我想，添加一条指令以获取自己的用户名这个功能应该不那么困难。

在阅读了 :ref:`app-structual` 后，我了解了整个顶点云应用程序服务器的结构，下面我准备添加这个简单的功能。

进入 ``cstruct`` 目录并编辑 ``cuser_operations.go`` ：

.. code-block:: shell
	
	cd cstruct
	nano cuser_operations.go
	
我在源码的 70 行附近发现了一个 ``switch`` 代码块，很明显这里将命令映射到了不同的处理函数上。我决定定义一个新的指令 ``whatsmyname`` 并在最后一个 ``case`` 和 ``default`` 之间添加一条映射关系，将它映射到我自定义的受理函数 ``lookupname`` 上：

.. code-block:: go

	case len(command) >= 5 && strings.ToUpper(command[:5]) == "CHMOD":
		// 改变资源权限
		u.chmod(db, command)
		
	// 此处添加自定义映射关系
	case len(command) >= 11 && strings.ToUpper(command[:11) == "WHATSMYNAME":
		u.lookupname(command)
	
	default:
		// 指令无法识别，返回错误信息
		u.listen.SendBytes([]byte("Invalid Command"))

添加了映射关系，我决定实现受理此命令的函数 ``lookupname`` ：

.. code-block:: go

	func (u *cuser) lookupname(command string) {
		if len(command) < 11 || 
			strings.ToUpper(command[:11]) != "WHATSMYNAME" ||
			u.nickname == ""{
			// 指令不合法或用户不存在昵称
			u.listen.SendBytes("查询失败！")
		} else {
			u.listen.SendBytes(u.nickname)
		}
	}
	
看起来已经没有需要改动的地方了。我将服务器重新编译了一次，并启动了测试客户端：

.. code-block:: shell

	cd ../cloud
	go build cloud.go && ./cloud &
	cd ../client
	go build client.go && ./client
	请输入命令：whatsnyname
	forec

虽然我很不喜欢 Forec 这个名字，但是他毕竟只是个测试用户而已，至少这说明了我的功能扩展成功了。

接下来请您阅读 :ref:`app-protocal` 。

.. _客户端: https://github.com/forec-org/cloud-storage-client
