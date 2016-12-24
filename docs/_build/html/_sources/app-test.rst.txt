.. _app-test:

测试
==========

此部分文档主要介绍顶点云的单元测试和测试客户端。顶点云提供了对部分内置模块的单元测试，覆盖了 :ref:`app-protocal-authentication-procedure` 、 :ref:`app-protocal-transmitter` 和 :ref:`app-models-class` 中的绝大部分。 :ref:`app-models-server` 可通过顶点云配备的 :ref:`app-test-client` 手动测试。

.. _app-test-code:

单元测试
--------------

此部分主要涉及几个内置包的单元测试。你可以直接运行 ``test/runtest.sh`` 或 ``test/runtest.bat`` 来激活全部单元测试。

``authenticate`` 和 ``cstruct`` 两个包的单元测试比较简单，均采用简单的输入-输出样例比对测试。

``transmit`` 包由一个微型测试服务器和一个微型测试客户端并发进行单元测试，其中涉及到 ``authenticate`` 包的部分功能，因此也可视作认证模块。

下面主要介绍 ``transmit`` 包的单元测试。

.. _app-test-transmit:

传输器测试
>>>>>>>>>>>>

传输器的测试由一个微型服务器和配套的微型客户端实现。大致逻辑如下：

- 微型服务器在指定测试 IP 和端口启动
- 微型客户端在新线程中启动并尝试连接服务器以获取服务
- 服务器向客户端发送指定测试文件
- 服务器向客户端发送指定测试字符串
- 客户端接收完毕后退出
- 服务器发送结束后等待一段时间，认为客户端已经退出后检查客户端接收到的文件/字符串是否正确，正确则测试通过

传输器的测试代码位于 ``authenticate/authenticate_test.go`` 。测试代码主要包含两个函数，声明如下：

.. code-block:: go

   func TestTransmission(t *testing.T) 
   func client_test(t *testing.T) 
  
函数 ``TestTransmission`` 用于启动微型服务器、为微型客户端提供支持以及检查传输是否正确。函数 ``client_test`` 用于延时启动微型客户端并接收服务器的传输请求。

默认测试使用的传输文件名为 ``test_in.txt`` ，顶点云提供的默认测试文件大小为 2.34MB。你可以在测试代码中替换 ``test_in_filename`` 为你自己的测试传输文件路径。

.. _app-test-client:

测试客户端
----------------

服务器逻辑功能较复杂，很难使用单元测试逐一覆盖，并且用户在使用中通常具有随机性。因此顶点云没有为服务器的每一个接口、用户代理的每一项处理函数添加单元测试，而是编写了测试客户端以手动测试。

测试用客户端代码位于 ``client/client.go`` ，共约 500 行， *client* 类主要的方法有：

* *Run* ：启动测试客户端并提供与用户的交互
* *Connect* ：负责客户端与服务器建立连接
* *Authenticate* ：在 *Connect* 成功之后负责与服务器建立认证
* *ThreadConnect* ：用于与服务器之间建立一个新传输器，并交付数据传输处理函数使用
* *getFile* ：用于处理用户的下载请求
* *putFile* ：用于处理用户的上传请求

测试客户端的界面相对专门设计的 GUI 客户端不是那么友好，但它确实是非常简单有效的测试工具。用户使用测试客户端时使用的指令需要严格按照 :ref:`app-protocal-command` 的要求，参数之间的分隔符要与 ``config/config.go`` 中 *SEPERATER* 项指定的字符（串）相同。

例如，你可以按照 :ref:`app-quickstart-runtest-client` 中的样例使用测试客户端。

.. _app-test-client-modify:

修改测试客户端
-------------------

这里主要介绍如何修改测试客户端以适应新的需求。

在测试客户端扩展功能与向用户代理添加功能类似。如果要添加的功能与数据传输相关，那么你需要在 *Run* 函数中添加转发逻辑，之后实现你的处理函数。

例如，在 :ref:`app-quickstart` 中我们为用户代理添加了新的功能。如果添加的功能不是简单的获取用户名，而是某个需要特殊处理流程的功能（如命令云主机处理一幅上传的图片并返回处理后的结果），则需要在 ``client/client.go`` 的第 230 行后插入转发逻辑：

.. code-block:: go
   
   case len(input) > 3 && strings.ToUpper(input[:3]) == "PUT":
       // 上传文件
	   go c.putFile(input)
   case len(input) > 8 && strings.ToUpper(input[:3]) == "GENERATE":
       // 插入新的转发逻辑，命令云存储服务器处理一幅上传的图片并返回处理后的内容
	   go c.generateImage(input)
   default:
       // 简单命令交互
	   
之后我们需要实现自定义处理函数 ``generateImage`` ，该函数应当被添加到 ``client.go`` 的任意位置。其大致格式如下所示：

.. code-block:: go

   func (c *Client) generateImage(input string){
       // 验证指令合法
	   // ...
	   newThread := c.ThreadConnect(c.ip, c.port)
	   // ...
       // 剩余自定义业务逻辑
   }
   
接下来请您阅读 :ref:`app-proxy` 。