.. _app-structual:

框架分析
===========

此部分文档主要介绍顶点云应用程序服务器的框架结构。

顶点云服务器源码文件结构如下：

.. code-block:: shell

   - app
      - authenticate
	    - authenticate.go
		- authenticate_test.go
	  - client
	    - client.go
	  - cloud
	    - cloud.go
		- work.db
	  - config
	    - config.go
	  - cstruct
	    - cuser.go
		- ulist.go
		- cuser_operations.go
		- cuser_transmissions.go
		- ...
	  - server
	    - server.go
	  - transmit
	    - transmit.go
		- transmit_test.go
		
以上几个目录对应的模型结构如下：

* *authenticate* ：对应 :ref:`app-protocal-authentication-procedure` 中的流程以及 API 文档中的 :ref:`app-api-cipher` 。
* *client* ：对应 :ref:`app-test` 中的测试客户端。
* *cloud* ：用于创建和启动 *server* 实例。
* *config* ：对应 :ref:`app-config` 。
* *cstruct* ：对应 :ref:`app-models-class` 。
* *server* ：对应 :ref:`app-models-class` 中的 *server* 类。
* *transmit* ：对应 :ref:`app-protocal-transmitter` 、 :ref:`app-models-transmitter` 。

服务器各模块之间关系如下图所示：

|uml|

接下来请您阅读 :ref:`app-test` 。

.. |uml| image:: _static/uml.png