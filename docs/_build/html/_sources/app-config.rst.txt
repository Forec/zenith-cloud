.. _app-config:

应用程序服务器全局设置
=========================

在阅读以下内容前，请确保您已经按照 :ref:`app-installation` 正确部署了应用程序服务器，并位于源码目录下（/path-to/zenith-cloud/app/）。

您可以根据您的环境修改源码目录下的 `config/config.go` 文件以配置服务器。

样例配置文件
----------------

您从 GitHub 仓库获取的源码中已经包含了一份默认的配置文件，忽略注释和函数部分后内容如下：

.. code-block:: go
   
   const STORE_PATH = "G:\\Cloud\\"
   const DOWNLOAD_PATH = "G:\\Cloud\\"
   const CLIENT_VERSION = "Windows"
   const AUTHEN_BUFSIZE = 1024
   const BUFLEN = 4096 * 1024
   const MAXTRANSMITTER = 20
   const DATABASE_TYPE = "sqlite3"
   const DATABASE_PATH = "work.db"
   const START_USER_LIST = 10
   const TEST_USERNAME = "forec@bupt.edu.cn"
   const TEST_PASSWORD = "TESTTHISPASSWORD"
   const TEST_SAFELEVEL = 3
   const TEST_IP = "127.0.0.1"
   const TEST_PORT = 10087
   const SEPERATER = "+"
   const CHECK_MESSAGE_SEPERATE = 5
	
样例配置文件每项均有对应注释，您也可以查看下面的 :ref:`app-config-detailed` 了解每一项的具体功能。

.. _app-config-detailed:

样例文件详细解释
-------------------

配置文件中的每一项对应配置如下：

1. ``STORE_PATH`` ：服务器中存储所有用户上传文件的路径。

2. ``DOWNLOAD_PATH`` ：在 ``app/client`` 目录中提供了一个测试客户端，此记录用于设置测试客户端从服务器下载文件的存储路径。

3. ``CLIENT_VERSION`` ：测试用客户端使用的操作系统。

4. ``AUTHEN_BUFSIZE`` ：服务器和客户端之间命令交互连接使用的缓冲区大小，如果你不了解此字段的含义，可以保留默认值。此字段详细的介绍请参考 :ref:`app-protocal-authen-bufsize` 。

5. ``BUFLEN`` ：服务器和客户端之间传输长数据流时使用的缓冲区大小，在网络环境较差的情况下应降低该项的大小，在网络丢包率较低的情况下应增加该项的大小。如果你不了解此字段的含义，可以保留默认值。此字段的详细介绍请参考 :ref:`app-protocal-buflen` 。

6. ``MAXTRANSMITTER`` ：服务器为每个客户端允许分配的最大同时活动连接数量，增加此数值可以在用户尝试下载多个文件时提供并行能力。

7. ``DATABASE_TYPE`` ：服务器使用的数据库类型。

8. ``DATABASE_PATH`` ：服务器使用的数据库所在的路径，此路径可为绝对路径，也可为相对服务器可执行文件所在目录的相对路径。

9. ``START_USER_LIST`` ：服务器在启动后会维护一个活动的用户池，此项指定了服务器启动时分配的用户池大小，在加入新用户后无需分配新内存，除非用户池已满。

10. ``TEST_USERNAME`` ：客户端测试使用的用户名，你可以手动此用户加入数据库，或在服务器第一次启动时将此用户模型加入数据库。默认配置文件中的用户名、密码已经加入到仓库中的 ``work.db`` 数据库。

11. ``TEST_PASSWORD`` ：客户端测试使用的登陆密码。

12. ``TEST_SAFELEVEL`` ：测试客户端和服务器约定使用的安全等级，可设置为任意整数，小于等于 1 时被规整为 1，大于等于 3 时被规整为 3。1、2、3 等级分别对应在加密时使用 16、24、32字节的密钥。

13. ``TEST_IP`` ：测试服务器时开放的 IP 地址。

14. ``TEST_PORT`` ：测试服务器时开放的端口。

15. ``SEPERATER`` ：此项指定了服务器和客户端约定的命令格式使用的分隔符，默认情况下为 ``+`` 。如果你不了解命令格式，可以查看 :ref:`app-protocal-command` 。

16. ``CHECK_MESSAGE_SEPERATE`` ：此项指定了服务器转发消息执行的间隔，默认为 5。服务器会每隔 ``CHECK_MESSAGE_SEPERATE`` 秒向每个用户转发其他用户发送给他的消息。如果你不明白此项的意义，请查看 :ref:`app-protocal-chat` 。

例如，在使用 WiFi 连接的 Ubuntu 16.04 下部署服务器以供 Windows 客户端使用时，可参考的配置文件如下：

.. code-block:: go
   
   const STORE_PATH = "/usr/local/cloud-store/"
   const DOWNLOAD_PATH = "/usr/local/cloud-download"
   const CLIENT_VERSION = "Windows"
   const AUTHEN_BUFSIZE = 1024
   const BUFLEN = 1024 * 1024  // 网络情况较差，减小缓冲区长度
   const MAXTRANSMITTER = 10
   const DATABASE_TYPE = "sqlite3"
   const DATABASE_PATH = "/usr/local/cloud/cloud.db"
   const START_USER_LIST = 10
   const TEST_USERNAME = "test@test.com"
   const TEST_PASSWORD = "TEST"
   const TEST_SAFELEVEL = 1
   const TEST_IP = "you ip address on Internet"	// 开放在公网地址
   const TEST_PORT = 10087
   const SEPERATER = "+"
   const CHECK_LIVE_SEPERATE = 10
   const CHECK_LIVE_TAG = "[check]"
   const CHECK_MESSAGE_SEPERATE = 10
   
接下来请您阅读 :ref:`app-quickstart` 。
