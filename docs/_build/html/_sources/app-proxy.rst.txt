.. _app-proxy:

用户代理
==========

此部分文档主要介绍用户代理的一些逻辑处理函数。这部分函数是顶点云功能实现的主体，但无法将具体的实现逻辑一一梳理。这里只会简单介绍各个逻辑处理函数的功能。

.. _app-proxy-requests:

交互式命令处理
------------------

此部分相关代码均位于 ``cstruct/cuser_operations.go`` 中，该代码文件中的函数结构如下所示：

.. code-block:: go
   
   DealWithRequests
	- ls
	- touch
	- rm
	- cp
	- mv
	- fork
	- send
	- chmod
	
只有 ``DealWithRequests`` 为公有方法，用于命令-逻辑转发，其他函数均为逻辑处理函数，不对其他包开放。

你可以参考这些逻辑处理函数实现的流程来模仿实现更多的自定义处理函数。顶点云应用程序服务器目前提供的交互式命令有限，仍有很多功能尚未提供，欢迎你为顶点云扩展更多自定义功能。新拓展的功能可以以独立文件形式提供，只要保证同属于 ``cstruct`` 包即可。

.. _app-proxy-transmission:

数据传输命令处理
--------------------

此部分相关代码均位于 ``cstruct/cuser_transmissions.go`` 中，该代码文件中的函数结构如下图所示：

.. code-block:: go
   
   DealWithTransmissions:
	- get
	- put
	 
只有 ``DealWithTransmissions`` 为公有方法，用于命令-逻辑转发，其他函数均为逻辑处理函数，不对其他包开放。

与数据传输命令相关的连接均会加入到当前用户的活动连接池中。当前用户的活动连接池需要由 ``DealWithTransmissions`` 方法维护，在处理完当前转发的逻辑处理函数后，``DealWithTransmissions`` 在销毁前会移除当前结束的活动连接。

添加代理
----------------

添加代理的方式可以参考 :ref:`app-quickstart-expand` 以及 :ref:`app-test-client-modify` 。

接下来您可以阅读 :ref:`app-tutorials` 。

