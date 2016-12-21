# 顶点云 Web 服务器

[![License](http://7xktmz.com1.z0.glb.clouddn.com/license-UDL.svg)](https://github.com/Forec/cloud-storage-webserver/blob/master/LICENSE) 
[![Build Status](https://travis-ci.org/Forec/cloud-storage-webserver.png)](https://travis-ci.org/Forec/cloud-storage-webserver) 
[![Doc](http://7xktmz.com1.z0.glb.clouddn.com/docs-icon.svg)](http://cloud-storage-webserver.readthedocs.io/zh_CN/latest/)

[**顶点云**](http://cloud.forec.cn) 是我 2016 年的一项课程设计选题，目标是在校园网基础上设计简易、方便的小规模云存储服务。顶点云的结构和实现非常简单，可运行在包括树莓派在内的任何计算机上，目前我将其部署在我的树莓派和一台云服务器上。我对树莓派的对应端口做了 NAT 穿透，因此即使在校外也可以访问存储在顶点云的文件。校内网为顶点云的传输提供了非常好的物理基础，经测试在使用有线网络的 Windows 7 系统下（IPv4协议），顶点云的 [客户端](https://github.com/forec-org/cloud-storage-client)可达到 42 MB/s 的下载速度。

此仓库托管了顶点云的 Web 服务器源码，你可以通过任何设备的浏览器访问顶点云。因为私人签署的证书不被浏览器信任，所以部署时放弃使用 https 协议。在公网部署的顶点云服务器仅作展示用，不提供开发注册或任何实质功能，但你可以使用测试用户登录体验。如果你喜欢并且希望使用使用顶点云，请 [Email](mailto:forec.edu.cn) 我，我会为你在后台开放一个可使用的账户。

顶点云的应用程序服务器托管在仓库 [顶点云 应用服务器](https://github.com/Forec/cloud-storage) 中，使用 Golang 编写。

## 开发者文档

顶点云最新的开发者文档可在 [此处](http://cloud-storage-webserver.readthedocs.io/zh_CN/latest/) 查看。

## 部署

顶点云 Web 服务器使用 Flask 框架，如果你对 Flask 很熟悉，可以很快了解顶点云的结构。

顶点云目录结构大致如下所示：

```
cloud-storage-web
  - app
    - auth
    - main
    - static
      - thumbnail
    - templates
    - ...
    - models.py
  - settings
  - config.py
  - manage.py
  - work.db
```

以下介绍顶点云配置中涉及的关键几个文件：
* `config.py`：顶点云 Web 服务器的全局配置，包括文件实体存储的位置、数据库路径、路径分隔符、管理员邮箱等，每项设置后均有对应的注释说明。详细设置可查看 [顶点云全局配置文件](#)。
* `manage.py`：顶点云 Web 服务器通过 `manage.py` 注册程序控制拓展，该文件提供了几个简单的命令如数据库初始化、测试用户初始化、shell交互等。详细命令可查看 [顶点云控制文件](#)。
* `work.db`：顶点云存储用户信息的数据库，默认使用 SQLITE，你可以通过修改 `config.py` 来更改数据库类型和路径，具体修改方法可查看 [顶点云数据库配置](#)。
* `settings` 目录：该目录包含了一个 Ngrok 配置文件和几个批处理文件，用于部署和启动顶点云服务器。具体配置方法可查看 [顶点云部署](#)。

顶点云服务器可通过以下方式部署（部署前请确保环境变量中已添加 Python3 路径）：
```shell
git clone https://github.com/Forec/cloud-storage-webserver.git
cd cloud-storage-webserver/settings
./setup.sh		# Windows 系统双击执行 setup.bat
```

## 启动
顶点云服务器可通过以下方式启动（请确保启动前已成功部署）。具体的启动方式和参数请查看 [顶点云运行参数配置](#)。
```
cd /path/to/cloud-storage-webserver/settings
./run.sh		# Windows 系统双击执行 run.bat
```

# 许可证
此仓库中的全部代码均受仓库中 [License](https://github.com/Forec/cloud-storage-webserver/blob/master/LICENSE) 声明的许可证保护。
