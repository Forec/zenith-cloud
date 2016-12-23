/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：云服务器传输器测试代码
*/

package transmit

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"testing"
	"time"
)

// 测试用缓冲区长度
const BUFSIZE int64 = 4096 * 1024

// 测试用传输文件相对路径
const test_in_filename string = "test_in.txt"

// 测试用输出文件相对路径
const test_out_filename string = "test_out.txt"

// 测试用传输客户端
func client_test(t *testing.T) {
	time.Sleep(time.Second)
	cconn, err := net.Dial("tcp", "127.0.0.1:10086")
	if err != nil {
		fmt.Println("错误：连接服务器期间断开", err.Error())
		return
	}
	defer cconn.Close()

	// 打开接收文件句柄
	file, err := os.OpenFile(test_out_filename,
		os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0666)
	if err != nil {
		fmt.Println("错误：无法获取接收到文件的句柄")
		return
	}
	defer file.Close()
	fileWriter := bufio.NewWriter(file)
	ts := NewTransmitter(cconn, BUFSIZE, []byte("1234567890123456"))
	ts.RecvToWriter(fileWriter)
	recvB, err := ts.RecvBytes()
	if err != nil {
		t.Errorf("错误：接收数据期间异常断开")
		return
	}
	if string(recvB) != "helloworld" {
		t.Errorf("错误：接收到的字节流与原字节流不同")
		return
	}
	return
}

// 测试用传输服务器
func TestTransmission(t *testing.T) {
	// 获取待发送文件句柄
	file, err := os.Open(test_in_filename)
	if err != nil {
		t.Errorf("传输错误：无法获取待发送文件句柄")
		return
	}
	defer file.Close()

	// 获取本地待发送文件大小
	fileReader := bufio.NewReader(file)
	totalFileLength, err := GetFileSize(test_in_filename)
	if err != nil {
		t.Errorf("传输错误：无法获取本地文件大小")
		return
	}

	// 启动传输服务器
	listener, err := net.Listen("tcp", "127.0.0.1:10086")
	if err != nil {
		fmt.Println("错误：测试服务器遇到了问题，即将宕机")
		return
	}
	defer listener.Close()

	// 启动客户端测试协程
	go client_test(t)
	sconn, err := listener.Accept()
	if err != nil {
		fmt.Println("错误：接收连接期间失败，错误信息：", err.Error())
		return
	}
	fmt.Println("接收到连接请求，来自 ", sconn.RemoteAddr().String())

	// 测试 128 位 AES 模块传输
	tr := NewTransmitter(sconn, BUFSIZE, []byte("1234567890123456"))
	tr.SendFromReader(fileReader, int64(totalFileLength))
	tr.SendBytes([]byte("helloworld"))
	time.Sleep(time.Second * 2)
	file.Close()

	// 校验接收和发送的文件一致
	vfile, err := os.Open(test_out_filename)
	if err != nil {
		t.Errorf("传输错误：无法获取接收到文件的句柄")
		return
	}
	defer vfile.Close()
	rfile, err := os.Open(test_in_filename)
	if err != nil {
		t.Errorf("传输错误：无法获取发送文件的句柄")
		return
	}
	defer rfile.Close()

	vfileReader := bufio.NewReader(vfile)
	rfileReader := bufio.NewReader(rfile)

	for {
		rbyte, err1 := rfileReader.ReadByte()
		vbyte, err2 := vfileReader.ReadByte()
		if err1 != nil && err2 != nil {
			break
		} else if err != nil || err2 != nil || rbyte != vbyte {
			t.Errorf("传输错误：接收到的文件和发送的文件不同")
			break
		}
	}
}
