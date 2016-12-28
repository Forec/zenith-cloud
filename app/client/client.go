/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：与云服务器配套的测试用客户端结构定义与实现
*/

package main

import (
	"bufio"
	auth "cloud-storage/authenticate"
	conf "cloud-storage/config"
	trans "cloud-storage/transmit"
	"fmt"
	"net"
	"os"
	"strconv"
	"strings"
	"time"
)

// 客户端结构
type Client struct {
	remote   trans.Transmitable
	info     trans.Transmitable
	level    uint8
	username string
	ip       string
	port     int
	worklist []trans.Transmitable
	token    []byte
}

// -----------------------------------------------------------------------------
// 客户端工厂方法，创建一个新的客户端实例
func NewClient(level int) *Client {
	c := new(Client)
	c.level = uint8(level)
	c.worklist = make([]trans.Transmitable, conf.MAXTRANSMITTER)
	c.token = make([]byte, conf.TOKEN_LENGTH(c.level))
	c.remote = nil
	return c
}

// -----------------------------------------------------------------------------
// RemoveWork：从当前客户端的工作列表中移除一个活动线程
func (c *Client) RemoveWork(t trans.Transmitable) bool {
	for i, ts := range c.worklist {
		if ts == t {
			c.worklist = append(c.worklist[:i], c.worklist[i+1:]...)
			return true
		}
	}
	return false
}

// -----------------------------------------------------------------------------
// MessageListening：消息监听线程
func (c *Client) MessageListening() {
	c.info = c.ThreadConnect(c.ip, c.port)
	if c.info == nil {
		return
	}
	for {
		infos, err := c.info.RecvBytes()
		if err != nil {
			fmt.Println("监听线程出错，错误信息为：", err.Error())
			return
		}
		fmt.Println("服务器消息：", string(infos))
	}
}

// -----------------------------------------------------------------------------
// ThreadConnect：开启一个新线程，与目标主机创建一个新的活动连接
func (c *Client) ThreadConnect(ip string, port int) trans.Transmitable {
	// 验证目标主机地址合法
	if !trans.IsIpValid(ip) || !trans.IsPortValid(port) {
		return nil
	}

	// 连接目标主机端口
	conn, err := net.Dial("tcp", fmt.Sprintf("%s:%d", ip, port))
	if err != nil {
		fmt.Println("连接远程失败，错误信息为：", err.Error())
		return nil
	}

	// 接收目标主机返回的 token
	init := 0
	buf := make([]byte, conf.TOKEN_LENGTH(c.level)*2)
	chR := time.Tick(1e3)
	for {
		if init >= conf.TOKEN_LENGTH(c.level) {
			break
		}
		<-chR
		length, err := conn.Read(buf[init:])
		if err != nil {
			fmt.Println("异常：传输出现错误！")
			return nil
		}
		init += length
	}

	// 创建新的 transmitter，按协议与服务器交互认证
	transmitter := trans.NewTransmitter(conn,
		conf.BUFLEN,
		buf[:conf.TOKEN_LENGTH(c.level)])
	temptoken := make([]byte, conf.TOKEN_LENGTH(c.level))
	copy(temptoken, buf[:conf.TOKEN_LENGTH(c.level)])
	encoded := auth.AesEncode([]byte(c.username+string(c.token)),
		transmitter.GetBlock())
	buf = make([]byte, 24+len(encoded))
	copy(buf, auth.Int64ToBytes(int64(len(c.username+string(c.token)))))
	copy(buf[8:], auth.Int64ToBytes(int64(len(encoded))))
	copy(buf[16:], auth.Int64ToBytes(int64(len(c.username))))
	copy(buf[24:], encoded)
	_, err = transmitter.GetConn().Write(buf)
	if err != nil {
		return nil
	}

	// 接收服务器返回的加密 token，和之前接收到的比对判断是否登陆成功
	checkInfo, err := transmitter.RecvBytes()
	if err != nil || len(checkInfo) < conf.TOKEN_LENGTH(c.level) {
		return nil
	}
	for i := 0; i < conf.TOKEN_LENGTH(c.level); i++ {
		if checkInfo[i] != temptoken[i] {
			return nil
		}
	}
	return transmitter
}

// -----------------------------------------------------------------------------
// Connect：主线程尝试连接远程服务器
func (c *Client) Connect(ip string, port int) bool {
	if !trans.IsIpValid(ip) || !trans.IsPortValid(port) {
		return false
	}
	conn, err := net.Dial("tcp", fmt.Sprintf("%s:%d", ip, port))
	if err != nil {
		fmt.Println("错误：连接远程主机时发生异常，错误信息为：", err.Error())
		return false
	}

	// 接收远程主机发送的 token
	init := 0
	buf := make([]byte, conf.TOKEN_LENGTH(c.level)*2)
	chR := time.Tick(1e3)
	for {
		if init >= conf.TOKEN_LENGTH(c.level) {
			break
		}
		<-chR
		length, err := conn.Read(buf[init:])
		if err != nil {
			fmt.Println("连接错误：传输过程中意外断开")
			return false
		}
		init += length
	}

	// 启动新的 transmitter
	c.remote = trans.NewTransmitter(conn, conf.AUTHEN_BUFSIZE,
		buf[:conf.TOKEN_LENGTH(c.level)])
	copy(c.token, buf[:conf.TOKEN_LENGTH(c.level)])
	fmt.Println("接收到远程主机 token：", string(c.token))
	c.ip = ip
	c.port = port
	return true
}

// -----------------------------------------------------------------------------
// Authenticate：与远程主机交互认证并登录
func (c *Client) Authenticate(username string, passwd string) bool {
	// 按协议发送/接收认证信息和回送消息
	md5Ps := string(auth.MD5(passwd))
	fmt.Println("send ,", username+md5Ps)
	encoded := auth.AesEncode([]byte(username+md5Ps), c.remote.GetBlock())
	buf := make([]byte, 24+len(encoded))
	copy(buf, auth.Int64ToBytes(int64(len(username+md5Ps))))
	copy(buf[8:], auth.Int64ToBytes(int64(len(encoded))))
	copy(buf[16:], auth.Int64ToBytes(int64(len(username))))
	copy(buf[24:], encoded)
	_, err := c.remote.GetConn().Write(buf)
	if err != nil {
		return false
	}
	checkInfo, err := c.remote.RecvBytes()
	if err != nil || len(checkInfo) < conf.TOKEN_LENGTH(c.level) {
		return false
	}
	for i := 0; i < conf.TOKEN_LENGTH(c.level); i++ {
		if checkInfo[i] != c.token[i] {
			return false
		}
	}
	c.username = username
	return true
}

// -----------------------------------------------------------------------------
// Run：客户端启动函数，进入工作状态
func (c *Client) Run() {
	// 用户交互输入流
	inputReader := bufio.NewReader(os.Stdin)

	// 读取服务器发送的用户信息
	for i := 0; i < 4; i++ {
		c.remote.RecvBytes()
	}

	for {
		fmt.Print("请输入命令：")
		// 读取用户输入命令
		input, err := inputReader.ReadString('\n')
		if err != nil {
			fmt.Println("无法获取你的输入命令\n")
			continue
		}
		switch {
		case len(input) > 3 && strings.ToUpper(input[:3]) == "GET":
			// 下载文件
			go c.getFile(input)
		case len(input) > 3 && strings.ToUpper(input[:3]) == "PUT":
			// 上传文件
			go c.putFile(input)
		default:
			// 简单命令交互
			c.remote.SendBytes([]byte(input))
			recvB, err := c.remote.RecvBytes()
			if err != nil {
				// 连接异常，注销登陆
				fmt.Println("错误：无法获取远程服务器回送消息")
				c.remote.Destroy()
				if c.info != nil {
					c.info.Destroy()
				}
				return
			}
			// 输出服务器回送消息
			fmt.Println(string(recvB))
		}
	}
}

func main() {
	c := NewClient(conf.TEST_SAFELEVEL)
	if !c.Connect(conf.TEST_IP, conf.TEST_PORT) {
		fmt.Println("尝试连接失败")
	} else {
		// 尝试认证
		if c.Authenticate(conf.TEST_USERNAME, conf.TEST_PASSWORD) {
			fmt.Println("服务器认证通过")
		} else {
			fmt.Println("服务器认证失败")
			return
		}
	}
	// 启动消息监听线程
	go c.MessageListening()
	// 启动客户端交互线程
	c.Run()
}

// -----------------------------------------------------------------------------
// makeDir：用于在客户端本地创建文件夹
func (c *Client) makeDir(path string) bool {
	if _, err := os.Stat(path); err == nil {
		return true
	} else {
		err := os.MkdirAll(path, 0711)
		if err != nil {
			fmt.Println(err.Error())
			return false
		}
	}
	if _, err := os.Stat(path); err == nil {
		return true
	}
	return false
}

// -----------------------------------------------------------------------------
// getFile：与服务器交互处理客户端 GET 请求
func (c *Client) getFile(input string) {
	// 命令格式: GET<SEP>待下载资源uid
	var filename string
	if c.info == nil {
		fmt.Println("检测到被动监听线程失效，无法启动服务")
		return
	}
	getThread := c.ThreadConnect(c.ip, c.port)
	if getThread == nil {
		fmt.Println("错误：无法启动传输线程")
		return
	}
	getThread.SendBytes([]byte(input))

	// 根据服务器回送消息验证指令是否可执行
	recv, err := getThread.RecvBytes()
	if err != nil {
		fmt.Println("错误：连接传输中被意外断开")
		return
	}

	// 远程服务器回送消息不成功
	if string(recv) != "VALID" {
		fmt.Println("错误：远程服务器拒绝了连接请求")
		return
	}

	// 验证通过，按协议接收文件
	c.worklist = append(c.worklist, getThread)
	recv, err = getThread.RecvBytes()
	if err != nil || len(recv) != 8 {
		fmt.Println("错误：连接接收文件信息时被意外中断")
		return
	}

	// 获取待接收文件数量
	fileCount := auth.BytesToInt64(recv[:8])
	var isdir_int int64
	for i := 0; i < int(fileCount); i++ {
		// 获取当前文件名
		recv, err = getThread.RecvBytes()
		if err != nil {
			fmt.Println("错误：获取文件名时意外中断")
			break
		}
		filename = string(recv)
		fmt.Println("获取到文件名：", filename)

		// 获取文件类型
		recv, err = getThread.RecvBytes()
		if err != nil {
			fmt.Println("错误：获取文件类型时意外中断，错误信息为：", err.Error())
			break
		}
		isdir_int = auth.BytesToInt64(recv[:8])
		if isdir_int == 1 {
			// 接收资源为文件夹
			if !c.makeDir(conf.DOWNLOAD_PATH + filename) {
				fmt.Println("错误：无法创建目录")
			}
			continue
		}
		file, err := os.OpenFile(conf.DOWNLOAD_PATH+filename,
			os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0666)
		if err != nil {
			fmt.Println("错误：无法创建文件，错误信息为：", err.Error())
			continue
		}
		defer file.Close()

		// 启动传输函数接收数据
		fileWriter := bufio.NewWriter(file)
		if getThread.RecvToWriter(fileWriter) {
			fmt.Println("文件 ", filename, " 已被下载")
		} else {
			fmt.Println("错误：文件 ", filename, " 下载失败")
		}
	}
	// 移除执行此次传输命令的线程
	c.RemoveWork(getThread)
}

// -----------------------------------------------------------------------------
// putFile：与服务器处理客户端 PUT 请求
func (c *Client) putFile(input string) {
	// 用户输入指令格式：put<SEP>待上传文件uid<SEP>本地待上传文件路径
	// 客户端发送指令格式：put<SEP>待上传文件uid<SEP>待上传文件大小<SEP>待上传文件MD5值
	args := generateArgs(input, 3)
	var uid int
	var size int64
	var err error
	var filepath string

	// 检查用户输入命令合法性
	if args == nil || strings.ToUpper(args[0]) != "PUT" {
		fmt.Println("错误：您的输入不合法")
		return
	}
	if uid, err = strconv.Atoi(args[1]); err != nil {
		fmt.Println("错误：您的输入不合法，错误信息：", err.Error())
		return
	}
	if c.info == nil {
		fmt.Println("错误：被动监听线程未活动，无法启动传输")
		return
	}

	// 获取待发送文件大小
	filepath = fmt.Sprintf("%s%s", conf.DOWNLOAD_PATH, args[2])
	if size, err = trans.GetFileSize(filepath); err != nil {
		fmt.Println("错误：无法获取本地文件大小，错误信息：", err.Error())
		return
	}

	// 获取待发送文件句柄
	file, err := os.Open(filepath)
	if err != nil {
		fmt.Println("错误：无法获取本地文件句柄，错误信息：", err.Error())
		return
	}

	// 计算待发送文件 MD5 值
	fileReader := bufio.NewReader(file)
	md5 := auth.CalcMD5ForReader(fileReader)
	defer file.Close()
	if md5 == nil {
		fmt.Println("错误：无法计算本地文件 MD5 值")
		return
	}

	// 启动传输线程
	putThread := c.ThreadConnect(c.ip, c.port)
	if putThread == nil {
		fmt.Println("错误：无法创建传输线程")
		return
	}

	// 构造远程服务器接收指令
	targetCommand := fmt.Sprintf("put%s%d%s%d%s%s", conf.SEPERATER,
		uid, conf.SEPERATER, size, conf.SEPERATER, md5)
	putThread.SendBytes([]byte(targetCommand))
	recv, err := putThread.RecvBytes()
	if err != nil || len(recv) != 8 {
		fmt.Println("错误：接收远程服务器回送状态码时意外断开连接")
		return
	}
	returnCode := auth.BytesToInt64(recv[:8])

	// 状态码 201 开始传输
	if returnCode == 201 {
		fmt.Println("接收到远程服务器回送码，开始传输")
		_, err = file.Seek(0, 0)
		if err != nil {
			return
		}
		fileReader = bufio.NewReader(file)
		putThread.SendFromReader(fileReader, size)

		recv, err = putThread.RecvBytes()
		if err != nil || len(recv) != 8 {
			fmt.Println("错误：接收远程服务器回送状态码时意外断开")
			return
		}
		returnCode = auth.BytesToInt64(recv[:8])
	} else if returnCode != 200 {
		// 接收到 200 以外的状态码，传输失败
		fmt.Println("错误：远程服务器拒绝传输，错误代码：", returnCode)
		return
	}

	// 传输成功
	if returnCode == 200 {
		fmt.Println("上传传输结束")
	}

	// 删除本次传输使用的活动连接线程
	c.RemoveWork(putThread)
}

// -----------------------------------------------------------------------------
// generateArgs：按分隔符将给定命令划分为 arglen 块字符串
func generateArgs(command string, arglen int) []string {
	args := strings.Split(command, conf.SEPERATER)
	if arglen > 0 && len(args) != arglen {
		return nil
	}
	for i, arg := range args {
		args[i] = strings.Trim(arg, " ")
		args[i] = strings.Replace(args[i], "\r", "", -1)
		args[i] = strings.Replace(args[i], "\n", "", -1)
		if args[i] == "" {
			fmt.Println("got invalid arg")
			return nil
		}
		fmt.Printf("%s ", args[i])
	}
	fmt.Println()
	return args
}
