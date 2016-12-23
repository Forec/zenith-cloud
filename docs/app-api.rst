.. _app-api:

应用程序 API 文档
=======================

.. _app-api-cipher:

数字处理模块
---------------

此部分详细介绍数字处理模块中几个 API 的使用方式。此模块主要分为 *AES* 、 *base64* 、 *int2bytes* 、 *md5* 以及 *token* 几部分。

.. _app-api-aes:

AES CFB 模块
>>>>>>>>>>>>>>>>

此部分涉及 AES CFB 对称加密的三个公有函数：

- *NewAesBlock* ：AES 块的工厂方法，根据密钥生成一个新的 AES 加/解密模块。
- *AesEncode* ：使用作为参数的 AES 块加密一段明文。
- *AesDecode* ：使用作为参数的 AES 块和明文长度解密一段密文。

.. _app-api-aes-factory:

NewAesBlock
"""""""""""""""

*NewAesBlock* 用于构造新的 AES 模块，它位于文件 ``authenticate/authenticate.go`` 中，其函数声明如下：

.. code-block:: go

   func NewAesBlock(key []byte) cipher.Block
   
作为参数的 ``key`` 为一串字节，作为生成模块加/解密的密钥。此函数会返回一个满足 ``cipher.Block`` 接口的新 AES 模块。

.. _app-api-aes-encode:

AesEncode
"""""""""""""""""

*AesEncode* 用于对一串明文加密，它位于文件 ``authenticate/authenticate.go`` 中，其函数声明如下：

.. code-block:: go

   AesEncode(plaintext []byte, block cipher.Block) []byte
   
该函数接受两个参数，第一个是待加密的明文字节流，第二个是一个 AES 模块。该函数会以字节切片的形式返回加密的结果。

.. _app-api-aes-decode:

AesDecode
""""""""""""""

*AesDecode* 用于对一串加密的字节解密，它位于文件 ``authenticate/authenticate.go`` 中，其函数声明如下：

.. code-block:: go

	func AesDecode(cipherText []byte, plainLen int64, block cipher.Block) ([]byte, error)
	
该函数接受 3 个参数，第一个参数为待解密的字节流，第二个为解密后的明文长度，第三个为一个 AES 模块。如果该 AES 模块成功解密，则返回结果的第一部分为明文，第二部分为 ``nil`` ，否则任何错误都将通过返回结果的第二部分传回高层函数。高层函数应当判断函数调用结果中是否包含错误以便及时恢复。

.. _app-api-base64:

Base64 模块
>>>>>>>>>>>>>>>>

此部分涉及 Base64 编码/解码的两个公有函数：

* *Base64Encode* ：使用 base64 对字节流编码
* *Base64Decode* ：使用 base64 对字节流解码

.. _app-api-base64-encode:

Base64Encode
"""""""""""""""

*Base64Encode* 可对一段明文使用 base64 编码，它位于 ``authenticate/authenticate.go`` 中，其函数声明如下：

.. code-block:: go

   func Base64Encode(plaintext []byte) []byte
   
该函数接受 1 个参数，该参数为待编码的字节流。该函数将参数编码后的结果以字节切片的形式返回。

.. _app-api-base64-decode:

Base64Decode
""""""""""""""""""

*Base64Decode* 可对一段使用 base64 编码的字节解码。如果传入的待解码字节流不符合 base64 编码格式，则函数返回值中会携带错误。它位于文件 ``authenticate/authenticate.go`` 中，其函数声明如下：

.. code-block:: go

   func Base64Decode(ciphertext []byte) ([]byte, error) 
   
该函数接受 1 个参数，该参数为待解码的字节流。该函数将参数解码后的结果以字节切片的形式返回，如果解码失败则会携带错误。高层函数应当检查此函数的返回值中是否包含错误信息。

.. _app-api-int2bytes:

Int64 与字节转化
>>>>>>>>>>>>>>>>>>

此部分涉及 ``Int64`` 类型和字节数组的转换，包含两个公有函数：

* *Int64ToBytes*  ：将一个 ``Int64`` 类型的数据按大端序转化为 8 个字节。
* *BytesToInt64*  ：将 8 个字节按大端序转化为一个 ``Int64`` 类型的数据。

.. _app-api-int64tobytes:

Int64ToBytes
""""""""""""""""

*Int64ToBytes* 位于文件 ``authenticate/authenticate.go`` 中，其函数声明为：

.. code-block::go
   
   func Int64ToBytes(i int64) []byte
   
该函数接受 1 个参数，该参数为待转换的 ``Int64`` 格式数据，函数将转换后的 8 个字节以字节切片的形式返回。

.. _app-api-bytestoint64:

BytesToInt64
""""""""""""""""

*BytesToInt64* 位于文件 ``authenticate/authenticate.go`` 中，其函数声明为：

.. code-block::go
   
   func BytesToInt64(buf []byte) int64
   
该函数接受 1 个参数，该参数为待转换的字节切片，函数会截取该切片的前 8 个字节，将转换后的 ``Int64`` 格式返回。

.. _app-api-md5&token:

MD5 和 token
>>>>>>>>>>>>>>>

此部分涉及 MD5 值和 token 的生成。包含 5 个公有函数，均位于文件 ``authenticate/authenticate.go`` 中：

* *GetRandomString* ：根据给定长度随机生成字符串。
* *MD5* ：计算传入参数的 MD5 值。
* *CalcMD5ForReader* ：计算传入可读结构的 MD5 值。
* *IsMD5* ：判断某个字符串是否为十六进制的 MD5 格式。
* *GenerateToken* ：根据给定的安全等及生成 token。

.. _app-api-getrandomstring:

GetRandomString
""""""""""""""""""""

*GetRandomString* 的函数声明如下：

.. code-block:: go

   func GetRandomString(length int) string
   
此函数接受一个整型数据作为生成随机字符串的长度，并返回生成的随机字符串。随机字符串包含的字符可为数字或字母（区分大小写）。若传入参数小于 0 则返回的字符串长度为 0。

.. _app-api-md5:

MD5
"""""""""""""

*MD5* 的函数声明如下：

.. code-block:: go

   func MD5(text string) []byte
   
此函数接受一个字符串并计算其 MD5 值，以 MD5 值的 16 进制形式返回，16 进制中的字母为大写。可以直接使用 ``string`` 强制转换此函数的返回值，此时即可得到字符串表示的 16 进制 MD5 值。

.. _app-api-calcmd5forreader:

CalcMD5ForReader
""""""""""""""""""""

*CalcMD5ForReader* 的函数声明如下：

.. code-block:: go

   func CalcMD5ForReader(reader *bufio.Reader) []byte
   
此函数接受一个可读结构作为参数，对其包含的全部数据分块计算 MD5 值。分块方法可参考 :ref:`app-protocal-md5` 。函数返回值与 :ref:`app-api-md5` 返回值类型相同。

.. _app-api-ismd5:

IsMD5
""""""""""""

*IsMD5* 的函数声明如下：

.. code-block:: go

   func IsMD5(text string) bool
   
此函数接受一个字符串作为参数，检查其是否符合大写的 16 进制 32 位 MD5 格式，若符合则返回 ``True`` ，否则返回 ``False`` 。

.. _app-api-generatetoken:

GenerateToken
""""""""""""""""

*GenerateToken* 的函数声明如下：

.. code-block:: go

   func GenerateToken(level uint8) []byte
   
此函数接受一个 ``uint8`` 类型作为参数，按 :ref:`app-config-detailed` 中介绍的 ``TEST_SAFELEVEL`` 项生成对应长度的 token 。大于 3 和小于 1 的参数均会被规整到 1 ～ 3。参数为 1 时返回 16 字节长度的 token，参数为 2 时返回 24 字节长度的 token，参数为 3 时返回 32 字节长度的 token。


.. _app-api-cuser:

User 接口
----------------

*User* 是针对 *cuser* 类设计的接口，其定义如下：

.. code-block::go

   type User interface {
       GetId() int64
	   GetUsed() int64
	   GetMaxm() int64
	   GetToken() string
	   GetAvatar() string
	   GetUsername() string
	   GetNickname() string
	   GetPassHash() string
	   GetInfos() trans.Transmitable
	   GetWorkList() []trans.Transmitable
	   SetAvatar(string) bool
	   SetPassHash(string) bool
	   SetNickname(string) bool
	   SetPath(string) bool
	   SetUsed(int64) bool
	   SetMaxm(int64) bool
	   SetToken(string) bool
	   SetListener(trans.Transmitable) bool              // 设置用户命令交互线程
	   SetInfos(trans.Transmitable) bool                 // 设置用户被动监听线程
	   AddTransmit(trans.Transmitable) bool              // 添加一个活动连接到工作池
	   RemoveTransmit(trans.Transmitable) bool           // 移除当前用户某个活动连接
	   DealWithRequests(*sql.DB)                         // 处理用户命令交互请求
	   DealWithTransmission(*sql.DB, trans.Transmitable) // 处理用户长数据流传输请求
	   Logout()                                          // 登出当前用户
   }

.. _app-api-cuser-factory:

NewCUser
>>>>>>>>>>>>>

*NewCUser* 是 *cuser* 类的工厂方法，其声明如下：

.. code-block:: go

   func NewCUser(username string, uid int64, curpath string) *cuser
   
你需要传入新建用户的用户名、用户编号以及用户当前路径（此参数传入 ``/`` 即可，在顶点云的默认配置中，此参数未启用）。例如：

.. code-block:: go

   u := NewCUser("Forec", 1, "/")
   

公有方法
>>>>>>>>>>>>

这里只介绍除元素获取和设置的其他方法。

.. _app-api-setlistener:

SetListener
""""""""""""""""""""

*SetListener* 用于为用户设置交互式传输器，通常在服务器认证首次登录用户时使用，返回值为 ``True`` 。该函数位于文件 ``cstruct/cuser.go`` 中，声明如下：

.. code-block:: go

   SetListener(trans.Transmitable) bool

.. _app-api-setinfos:

SetInfos
"""""""""""""""""

*SetInfos* 用于为用户设置被动监听传输器，在用户第一个长数据流连接到来时调用，返回值为 ``True`` 。该函数位于文件 ``cstruct/cuser.go`` 中，声明如下：

.. code-block:: go

   SetInfos(trans.Transmitable) bool
   
.. _app-api-addtransmit:

AddTransmit
""""""""""""""""""

*AddTransmit* 用于向用户活动工作池中添加一个新的传输器，添加成功则返回 ``True`` ，若工作池中的活动连接数目已经达到了 ``MAXTRANSMITTER`` 则返回 ``False`` 。该函数位于文件 ``cstruct/cuser.go`` 中，声明如下：

.. code-block:: go
   
   AddTransmit(trans.Transmitable) bool
   
.. _app-api-removetransmit:

RemoveTransmit
""""""""""""""""""""""

*RemoveTransmit* 用于从用户活动工作池中移除一个指定的传输器，通常在用户活动连接工作执行完成后由用户代理调用，若未找到指定的传输器返回 ``False`` ，否则返回 ``True`` 。该函数位于文件 ``cstruct/cuser.go`` 中，声明如下：

.. code-block:: go

   RemoveTransmit(trans.Transmitable) bool
   
.. _app-api-logout:

Logout
"""""""""""""""""""

*Logout* 用于登出当前用户，销毁当前用户在内存中的记录，销毁交互式传输器以及其他任何属于该用户的活动/非活动的传输器。该函数位于文件 ``cstruct/cuser.go`` 中，声明如下：

.. code-block:: go
   
   Logout()
	
.. _app-api-dealwithrequests:

DealWithRequests
"""""""""""""""""""""

*DealWithRequests* 函数负责索引并转交远程用户发送的交互式命令，将交互式命令转发给各对应执行函数。在用户在线期间，该函数始终存活，在 *DealWithRequests* 函数结束后，服务器将自动执行用户登出操作。传入参数为服务器维护的数据库句柄。该函数位于文件 ``cstruct/cuser_operations.go`` 中，声明如下：

.. code-block:: go
   
   DealWithRequests(*sql.DB)
   
此方法将在 :ref:`app-proxy` 中详细介绍。它是服务器处理用户请求的核心，能够方便的扩展功能。
   
.. _app-api-dealwithtransmission:

DealWithTransmission
"""""""""""""""""""""""""

*DealWithTransmission* 函数负责索引并转交远程用户发送的文件传输命令，将文件传输命令转发给各对应执行函数。在某个传输执行期间，该函数始终存活。在 *DealWithTransmission* 函数结束后，用户代理会自动移除作为函数参数的传输器。传入参数为服务器维护的数据库句柄和本次传输使用的 :ref:`app-api-transmitter` 。该函数位于文件 ``cstruct/cuser_transmissions.go`` 中，声明如下：
   
.. code-block:: go

   DealWithTransmission(*sql.DB, trans.Transmitable)
   
此方法将在 :ref:`app-proxy` 中详细介绍。它是服务器处理用户请求的核心，能够方便的扩展功能。
   
.. _app-api-transmitter:

传输器
---------------

此部分详细介绍 :ref:`app-models-transmitter` 提供方法的使用方式。传输器无法直接使用结构生成，只可以通过工厂方法 :ref:`app-api-transmitter-factory` 生成。传输器提供了一个对外的公有接口 :ref:`app-api-transmitable` 。

.. _app-api-transmitable:

Transmitable
>>>>>>>>>>>>>>>>

*Transmitable* 是 :ref:`app-models-transmitter` 的公共接口，其定义如下：

.. code-block:: go

   type Transmitable interface {
	   GetConn() net.Conn                        // 获取 Socket 连接
	   GetBuf() []byte                           // 获取缓冲区指针
	   GetBuflen() int64                         // 获取缓冲区长度
	   GetBlock() cipher.Block                   // 获取加密模块
	   SetBuflen(int64) bool                     // 设置缓冲区长度
	   SendBytes([]byte) bool                    // 按协议格式发送字节流，可维持边界
	   SendFromReader(*bufio.Reader, int64) bool // 从可读结构发送字节流
	   RecvUntil(int64, int64, <-chan time.Time) (int64, error)
	   // 接收数据直到达到设定数量
	   RecvBytes() ([]byte, error)      // 按协议格式接收字节流，维持边界
	   RecvToWriter(*bufio.Writer) bool // 按协议格式接收字节流并写入可写结构
	   Destroy()                        // 销毁此传输接口
   }

.. _app-api-transmitter-factory:

NewTransmitter
>>>>>>>>>>>>>>>>>

*NewTransmitter* 是 :ref:`app-models-transmitter` 的工厂方法，其函数声明如下：

.. code-block:: go

   func NewTransmitter(tconn net.Conn, tbuflen int64, token []byte) *transmitter
   
你需要传入一个 Socket 连接、传输器使用的缓冲区大小以及此传输器加密模块使用的密钥来生成一个新的传输器。例如，当前用户新加入一个连接 ``conn` ，需要使用 1024 字节缓冲区，密钥使用 ``12345678901234567890123456789012`` ，则通过以下代码创建传输器：

.. code-block:: go

   t := NewTransmitter(conn, 1024, "12345678901234567890123456789012")
   

公有方法
>>>>>>>>>>>>

传输器模块是整个顶点云最核心的模块之一，它提供了如下几个非常重要的公有方法：

* *GetConn* ：获取传输器封装的 Socket 连接
* *GetBuf* ：获取传输器内部的缓冲区指针
* *GetBuflen* ：获取传输器内部的缓冲区长度
* *GetBlock* ：获取传输器内部的加密模块
* *SetBuflen* ：设置传输器使用的缓冲区长度
* *SendBytes* ：使用此传输器按协议格式发送字节流，可维持边界
* *SendFromReader* ：使用此传输器从可读结构发送字节流
* *RecvUntil* ：使用此传输器接收数据直到达到设定数量
* *RecvBytes* ：使用此传输器按协议格式接收字节流，维持边界
* *RecvToWriter* ：使用此传输器按协议格式接收字节流并写入可写结构
* *Destroy* ：销毁此传输器

下面主要介绍 *SendBytes* 、 *SendFromReader* 、 *RecvUntil* 、 *RecvBytes* 、 *RecvToWriter* 以及 *Destroy* 方法。

在阅读之前，请确保您了解传输器的基本原理，否则请先阅读 :ref:`app-protocal-transmitter` 。

.. _app-api-sendbytes:

SendBytes
""""""""""""""""""""""

*SendBytes* 函数发送一串字节流交与远程传输器，其声明如下：

.. code-block:: go

   func (t *transmitter) SendBytes(toSend []byte) bool
   
发送成功时此函数返回 ``True`` ，在发送过程中出现任何异常均会返回 ``False`` 。因为 AES CFB 算法加密后生成的密文长度较明文长度更长，但通常在明文长度的 2 倍以下。因此 *SendBytes* 函数在发送过程中会拆分待发送的字节数组，保证发出的每个包内的明文长度不超过传输器缓冲区的 1/3，因此加密后的长度不会超过缓冲区长度。

.. _app-api-sendfromreader:

SendFromReader
""""""""""""""""""""""

*SendFromReader* 函数从一个可读结构中读取指定长度的数据交与远程传输器，其声明如下：

.. code-block:: go

   func (t *transmitter) SendFromReader(reader *bufio.Reader, totalLength int64) bool
   
此函数接受两个参数，第一个为可读结构，传输器从此参数中读取数据；第二个为待发送数据的长度。发送成功时此函数返回 ``True`` ，在发送过程中出现任何异常均会返回 ``False`` 。此函数发送方式与 *SendBytes* 类似，但若可读结构中的数据长度少于指定的数据长度（传入的第二个参数），则此函数将返回 ``False`` ，否则只读到指定长度位置便停止发送并返回。

.. _app-api-recvuntil:

RecvUntil
""""""""""""""""""""""

*RecvBytes* 函数从远程传输器接收满指定长度的数据，其声明如下：

.. code-block:: go

   func (t *transmitter) RecvUntil(until int64, init int64, chR <-chan time.Time) (int64, error) 
   
此函数传入参数较多，下面详细介绍各个参数含义：

- *until* ：缓冲区中接收到的数据长度超过（含） *until* 时退出此函数
- *init* ：缓冲区当前已经接收到的数据长度
- *chR* ：接收速率

此函数返回值包含一个 ``Int64`` 类型数据和可能出现的错误。若接收成功则返回值的 ``Int64`` 数据表示当前传输器缓冲区中存储的数据长度，否则返回值中包含错误。如果远程传输器迟迟没有发送数据，此函数会阻塞。

此函数通常在 :ref:`app-api-recvbytes` 和 :ref:`app-api-recvtowriter` 中调用，用于分别接收包头以及每个包体。如果你对此函数的意义不是很了解，请查阅 :ref:`app-protocal-transmitter` 。

.. _app-api-recvbytes:

RecvBytes
""""""""""""""""""""""

*RecvBytes* 函数从远程传输器接收符合一个消息边界的字节流，其声明如下：

.. code-block:: go

   func (t *transmitter) RecvBytes() ([]byte, error)
   
接收成功时此函数返回接收到的字节数组和 ``nil`` ，若在发送过程中出现任何异常，则返回值中将包含错误 。

.. _app-api-recvtowriter:

RecvToWriter
""""""""""""""""""""""

*RecvToWriter* 函数从远程传输器接收一定长度的数据并写入一个可读结构，其函数声明如下：

.. code-block:: go

   func (t *transmitter) RecvToWriter(writer *bufio.Writer) bool
   
此函数接受一个可写结构，传输器从远程传输器读取数据，并且写入到可写结构中。接收成功时此函数返回 ``True`` ，在接收过程中出现任何异常均会返回 ``False`` 。此函数接收方式与 *RecvBytes* 类似。如果你尚不了解接收原理，请查阅 :ref:`app-protocal-transmitter` 。

.. _app-api-server:

服务器类
-------------

此部分详细介绍 *server* 类方法的使用方式。

*server* 类包含如下几个公有方法：

* *InitDB* ：初始化数据库函数，在创建服务器实例后调用以修复不存在的表。
* *CheckBroadCast* ：消息转发函数，此函数通常在一个独立的协程中执行，负责用户通讯。
* *Run* ：启动函数，将服务器实例开放在指定 IP 地址和端口。
* *Communicate* ：用户代理函数，每个在线用户均有一个对应的 *Communicate* 函数运行在独立协程中提供服务。
* *Login* ：连接认证函数，负责新连接的认证和转发。

公有方法
>>>>>>>>>>>>>>

.. _app-api-server-initdb:

InitDB
""""""""""""""""

*InitDB* 函数位于 ``server/server.go`` 中，用于修复数据库中缺失的表。你可以在创建 *server* 类实例后 *s* 后调用 ``s.InitDB()`` 。

.. _app-api-server-checkbroadcast:

CheckBroadCast
""""""""""""""""""

*CheckBroadCast* 函数位于 ``server/server.go`` 中，用于转发用户通讯消息。你可以在初始化 *server* 类实例 *s* 后通过 ``go s.CheckBroadCast()`` 启动一个守护线程来执行转发逻辑 。

.. _app-api-server-run:

Run
""""""""""""""""

*Run* 函数位于 ``server/server.go`` 中，用于启动服务器。你可以在初始化 *server* 类实例 *s* ，并确保所有运行前逻辑均已调用完成的情况下调用 ``s.Run()`` 来启动服务器。此函数内部由 ``for`` 循环阻塞，如果此函数退出则整个服务器程序都将结束。

.. _app-api-server-communicate:

Communicate
""""""""""""""""

*Communicate* 函数位于 ``server/server.go`` 中，用于为每个用户提供服务。此函数在服务器的 *Run* 方法中调用，每当一个新的连接请求到来，服务器将启动一个新的协程执行 *Communicate* 函数，并处理用户请求。

*Communicate* 会根据用户请求的类型决定将请求转交给 :ref:`app-proxy` ，或者创建一个新的用户代理。

.. _app-api-server-login:

Login
""""""""""""""""

*Login* 函数位于 ``server/server.go`` 中，用于认证用户请求的合法性。此函数在服务器的 *Communicate* 方法中调用，*Communicate* 根据 *Login* 的返回值决定如何处理用户请求。

