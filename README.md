# 顶点云

[![License](http://7xktmz.com1.z0.glb.clouddn.com/license-UDL.svg)](https://github.com/Forec/zenith-cloud/blob/master/LICENSE) 
[![Build Status](https://travis-ci.org/Forec/zenith-cloud.png)](https://travis-ci.org/Forec/zenith-cloud) 
[![Documentation Status](https://readthedocs.org/projects/zenith-cloud/badge/?version=latest)](http://zenith-cloud.readthedocs.io/zh_CN/latest/?badge=latest)

[**顶点云**](http://cloud.forec.cn) 是我 2016 年的一项课程设计选题，目标是在校园网基础上设计简易、方便的小规模云存储服务。顶点云的结构和实现非常简单，可运行在包括树莓派在内的任何计算机上，目前我将其部署在我的树莓派和一台云服务器上。我对树莓派的对应端口做了 NAT 穿透，因此即使在校外也可以访问存储在顶点云的文件。校内网为顶点云的传输提供了非常好的物理基础，经测试在使用有线网络的 Windows 7 系统下（IPv4协议），顶点云的 [客户端](https://github.com/forec-org/cloud-storage-client) 可达到 42 MB/s 的下载速度。

此仓库托管了顶点云的应用程序服务器和 Web 服务器源码，你可以通过 [non1996](https://github.com/non1996) 编写的 [客户端](https://github.com/forec-org/cloud-storage-client) 获取顶点云应用程序服务器支持，也可以使用任何设备的浏览器访问顶点云 Web 服务器。因为私人签署的证书不被浏览器信任，所以顶点云的 Web 服务器部署时放弃使用 https 协议。在公网部署的顶点云服务器仅作展示用，不提供开发注册或任何实质功能，但你可以使用测试用户登录体验。如果你喜欢并且希望使用使用顶点云，请 [Email](mailto:forec.edu.cn) 我，我会为你在后台开放一个可使用的账户。

# 开发者文档

顶点云最新的开发者文档可在 [此处](http://zenith-cloud.readthedocs.io/zh_CN/latest/) 查看，开发者文档提供了对顶点云应用程序服务器和 Web 服务器的详细介绍。

我同时也在博客新建了专栏 [《顶点云设计与实现》](http://blog.forec.cn/columns/zenith-cloud.html)，详细记录了顶点云从构想、设计到具体代码实现的流程。

# 许可证
此仓库中的全部代码均受仓库中 [License](https://github.com/Forec/cloud-storage-webserver/blob/master/LICENSE) 声明的许可证保护。
