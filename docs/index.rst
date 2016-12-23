欢迎来到顶点云
=============================================

.. image:: _static/logo_full.png
   :alt: 顶点云：专为北邮人设计的云存储系统
   :align: right

欢迎阅读顶点云服务器的开发者文档。本文档分为两部分：《 :ref:`zenith-app` 》和《 :ref:`zenith-web` 》。其中，Web 服务器使用 `Flask`_ 框架，应用程序服务器使用 `Golang`_ ，这二者不在本文档的范围之内，如有兴趣请移步：

-	`Flask 文档 <http://flask.pocoo.org/docs/0.11/>`_
-	`Go 语言文档 <https://golang.org/doc/>`_

《 :ref:`zenith-app` 》和《 :ref:`zenith-web` 》均包含对应的部署说明和快速上手指南，我建议您按文档推荐的顺序阅读。

下面简要介绍二者的关系：在提出设计顶点云时就已考虑到设计两个服务器的需求，因此二者相互兼容，可同时运行在一台主机，同时为应用程序客户端和 Web 用户提供服务。顶点云的应用程序服务器早于 Web 服务器开发，开发历时约一个月，Web 服务器根据应用程序服务器复现以提供浏览器支持，耗时约两周。如果您想了解更多顶点云的背景，欢迎阅读 :ref:`forewords` 。


.. _Golang: https://golang.org/
.. _Flask: http://flask.pocoo.org/


.. include:: contents.rst.inc
