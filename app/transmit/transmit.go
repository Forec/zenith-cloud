/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：云服务器传输器结构定义与方法实现
*/

package transmit

import (
	"bufio"
	auth "cloud-storage/authenticate"
	conf "cloud-storage/config"
	"crypto/cipher"
	"fmt"
	"net"
	"os"
	"regexp"
	"time"
)

// -----------------------------------------------------------------------------
// 可传输接口定义
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

// -----------------------------------------------------------------------------
// 传输器结构定义
type transmitter struct {
	conn    net.Conn     // Socket 连接
	block   cipher.Block // 加密模块
	buf     []byte       // 缓冲区指针
	recvLen int64        // 当前缓冲区内缓存数据长度
	buflen  int64        // 缓冲区总长度
}

// -----------------------------------------------------------------------------
// 传输器工厂方法
func NewTransmitter(tconn net.Conn, tbuflen int64, token []byte) *transmitter {
	t := new(transmitter)
	t.conn = tconn
	if tbuflen < 1 {
		t.buflen = 1
	} else {
		t.buflen = tbuflen
	}
	t.buf = make([]byte, t.buflen)
	// 根据 token 生成新的 AES 模块
	t.block = auth.NewAesBlock(token)
	t.recvLen = 0
	return t
}

// -----------------------------------------------------------------------------
// 传输器缓冲区长度
func (t *transmitter) GetBuflen() int64 {
	return t.buflen
}

func (t *transmitter) SetBuflen(buflen int64) bool {
	// 新缓冲区长度小于原缓冲区长度，截断并启动垃圾回收
	if buflen <= t.buflen {
		t.buflen = buflen
		t.buf = t.buf[:t.buflen]
		return true
	} else {
		// 新缓冲区长度大于原缓冲区长度，重新分配缓冲区并启动垃圾回收
		t.buf = make([]byte, buflen)
		t.buflen = buflen
		return true
	}
}

// -----------------------------------------------------------------------------
// 缓冲区元素获取
func (t *transmitter) GetConn() net.Conn {
	return t.conn
}

func (t *transmitter) GetBlock() cipher.Block {
	return t.block
}

func (t *transmitter) GetBuf() []byte {
	return t.buf
}

// -----------------------------------------------------------------------------
// SendBytes：按协议格式发送维持边界的字节流
func (t *transmitter) SendBytes(toSend []byte) bool {
	if t.buf == nil || t.conn == nil {
		return false
	}
	totalLength := len(toSend)
	// 按协议发送明文总长度
	_, err := t.conn.Write(auth.Int64ToBytes(int64(totalLength)))
	if err != nil {
		return false
	}

	// chRate 控制发送速率，发送端时钟速率要小于接收端时钟速率
	chRate := time.Tick(2e3)
	alSend := 0
	var length int
	for {
		<-chRate
		if totalLength == alSend {
			// 已发送全部数据
			break
		}

		// 保证当前发送的明文长度小于缓冲区长度 1/3 防止加密后溢出
		if totalLength-alSend < int(t.buflen/3) {
			length = totalLength - alSend
		} else {
			length = int(t.buflen / 3)
		}

		// 构造包格式
		copy(t.buf[16:], toSend[alSend:alSend+length])
		copy(t.buf, auth.Int64ToBytes(int64(length)))
		encoded := auth.AesEncode(t.buf[16:length+16], t.block)
		copy(t.buf[8:], auth.Int64ToBytes(int64(len(encoded)+16)))
		copy(t.buf[16:], encoded)
		_, err = t.conn.Write(t.buf[:len(encoded)+16])
		if err != nil {
			return false
		}
		alSend += length
	}
	return true
}

// -----------------------------------------------------------------------------
// SendFromReader：从可读结构发送指定长度的数据，接收方可维持边界
func (t *transmitter) SendFromReader(reader *bufio.Reader,
	totalLength int64) bool {
	// 可读结构为空认为发送失败，无需发送
	if t.buf == nil || t.conn == nil {
		return false
	}
	_, err := t.conn.Write(auth.Int64ToBytes(totalLength))
	if err != nil {
		return false
	}
	sendLength := totalLength
	// 控制发送周期为 2000ns
	chRate := time.Tick(2e3)
	var encodeBufLen int64 = t.buflen/3 - 16
	var length int
	for {
		<-chRate
		if sendLength <= 0 {
			// 发送长度已达到要求
			return true
		}
		if sendLength >= encodeBufLen {
			// 待发送长度大于缓冲区长度 1/3，仅读入长度为缓冲区长度 1/3 的数据
			length, err = reader.Read(t.buf[16 : 16+encodeBufLen])
		} else {
			// 待发送长度小于缓冲区长度 1/3，全部读入
			length, err = reader.Read(t.buf[16 : 16+sendLength])
		}
		if err != nil {
			return false
		}

		// 构造包结构
		copy(t.buf, auth.Int64ToBytes(int64(length))) // 前 8 字节本包明文长度
		encoded := auth.AesEncode(t.buf[16:length+16], t.block)
		copy(t.buf[8:], auth.Int64ToBytes(int64(len(encoded)+16)))
		//	后 8 字节为整个包长度
		copy(t.buf[16:], encoded)
		_, err = t.conn.Write(t.buf[:len(encoded)+16])
		if err != nil {
			return false
		}
		sendLength -= int64(length)
		if length == 0 {
			return true
		}
	}
}

// -----------------------------------------------------------------------------
// RecvUntil 使传输器按照给定速率一直接收满指定长度的数据，保存在传输器缓冲区内
func (t *transmitter) RecvUntil(until int64,
	init int64,
	chR <-chan time.Time) (int64, error) {
	for {
		if init >= until {
			break
		}
		<-chR
		length, err := t.conn.Read(t.buf[init:])
		if err != nil {
			fmt.Println("错误：传输期间意外中断")
			return -1, err
		}
		init += int64(length)
	}
	return init, nil
}

// -----------------------------------------------------------------------------
// RecvBytes：接收一段字节流，并保证按协议格式维持边界
func (t *transmitter) RecvBytes() ([]byte, error) {
	var err error
	if t.buf == nil || t.conn == nil {
		return nil, err
	}
	// 设定接收周期为 1000ns
	chRate := time.Tick(1e3)
	// 接收 8 个字节的长度标识
	length, err := t.RecvUntil(8, t.recvLen, chRate)
	if err != nil {
		fmt.Println("错误：接收长度期间传输意外断开")
		return nil, err
	}
	// 截断前 8 字节获取明文长度
	totalLength := auth.BytesToInt64(t.buf[:8])
	var toRecvLength int64 = totalLength
	var plength int64 = 0
	var elength int64 = 0
	var pRecv int64 = length - 8
	copy(t.buf, t.buf[8:length])
	returnBytes := make([]byte, 0, conf.AUTHEN_BUFSIZE)
	for {
		// 待接收长度为 0 时更新缓冲区数据长度，并退出
		if toRecvLength == int64(0) {
			t.recvLen = pRecv
			return returnBytes, nil
		}
		pRecv, err = t.RecvUntil(int64(16), pRecv, chRate)
		if err != nil {
			return nil, err
		}

		// 前 8 字节为明文长度，后 8 字节为本包长度
		plength = auth.BytesToInt64(t.buf[:8])
		elength = auth.BytesToInt64(t.buf[8:16])
		pRecv, err = t.RecvUntil(elength, pRecv, chRate)
		if err != nil {
			return nil, err
		}
		receive, err := auth.AesDecode(t.buf[16:elength], plength, t.block)
		if err != nil {
			fmt.Println("错误：AES 无法使用已知的 token 解码！")
			return nil, err
		}
		returnBytes = append(returnBytes, receive...)
		// 更新待接收长度
		toRecvLength -= plength
		// 更新缓冲区数据位置
		copy(t.buf, t.buf[elength:pRecv])
		// 更新缓冲区当前数据末尾位置
		pRecv -= elength
	}
}

// -----------------------------------------------------------------------------
// RecvToWriter：接收维持协议格式边界的数据并输出到可写结构
func (t *transmitter) RecvToWriter(writer *bufio.Writer) bool {
	var err error
	if t.buf == nil || t.conn == nil {
		return false
	}
	chRate := time.Tick(1e3)
	length, err := t.RecvUntil(8, t.recvLen, chRate)
	if err != nil {
		fmt.Println("错误：接收长度期间传输意外断开")
		return false
	}
	totalLength := auth.BytesToInt64(t.buf[:8])
	var recvLength int64 = 0
	var plength int64 = 0
	var elength int64 = 0
	var pRecv int64 = length - 8
	copy(t.buf, t.buf[8:length])
	for {
		if recvLength == int64(totalLength) {
			t.recvLen = pRecv
			err = writer.Flush()
			if err != nil {
				fmt.Println("错误：写出到文件时异常，错误信息：", err.Error())
				return false
			}
			return true
		}
		pRecv, err = t.RecvUntil(int64(16), pRecv, chRate)
		if err != nil {
			fmt.Println("错误：接收包头期间异常，错误信息：", err.Error())
			return false
		}
		plength = auth.BytesToInt64(t.buf[:8])
		elength = auth.BytesToInt64(t.buf[8:16])
		pRecv, err = t.RecvUntil(elength, pRecv, chRate)
		if err != nil {
			fmt.Println("错误：接收包体期间异常，错误信息：", err.Error())
			return false
		}
		receive, err := auth.AesDecode(t.buf[16:elength], plength, t.block)
		if err != nil {
			fmt.Println("错误：无法使用已知的 token 解码")
			return false
		}
		outputLength, outputError := writer.Write(receive)
		if outputError != nil || outputLength != int(plength) {
			fmt.Println("错误：无法写入本地文件")
			return false
		}
		recvLength = recvLength + plength
		copy(t.buf, t.buf[elength:pRecv])
		pRecv -= elength
	}
}

// -----------------------------------------------------------------------------
// 销毁传输器，关闭 Socket 连接，启动垃圾回收
func (t *transmitter) Destroy() {
	if t.conn != nil {
		t.conn.Close()
	}
}

// -----------------------------------------------------------------------------
// 地址、端口合法性校验
func IsIpValid(ip string) bool {
	ip_ok, _ := regexp.MatchString(
		"^(25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)(\\.(25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)){3}$", ip)
	if !ip_ok {
		return false
	}
	return true
}

func IsPortValid(port int) bool {
	return 0 <= port && port <= 65535
}

// -----------------------------------------------------------------------------
// 获取本地文件大小，公有方法
func GetFileSize(path string) (size int64, err error) {
	fileInfo, err := os.Stat(path)
	if err != nil {
		return -1, err
	}
	fileSize := fileInfo.Size()
	return fileSize, nil
}
