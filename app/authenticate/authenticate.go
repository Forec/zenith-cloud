/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：云服务器使用的认证方法实现
*/

package authenticate

import (
	"bufio"
	conf "cloud-storage/config"
	"crypto/aes"
	"crypto/cipher"
	"crypto/md5"
	"encoding/base64"
	"encoding/binary"
	"encoding/hex"
	"math/rand"
	"strings"
	"time"
)

// 用于base64编码的字符表
const (
	base64Table = `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/`
)

// 用于 AES CFB 加密的 IV 序列
var commonIV = []byte{0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
	0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f}

// -----------------------------------------------------------------------------
// base64编码器
var coder = base64.NewEncoding(base64Table)

// base64编码
func Base64Encode(plaintext []byte) []byte {
	return []byte(coder.EncodeToString(plaintext))
}

// base64解码
func Base64Decode(ciphertext []byte) ([]byte, error) {
	return coder.DecodeString(string(ciphertext))
}

// -----------------------------------------------------------------------------
// AES 块工厂方法
func NewAesBlock(key []byte) cipher.Block {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil
	}
	return block
}

// AES CFB 加密，接收字节流表示的明文和密文模块，返回字节流表示的密文
func AesEncode(plaintext []byte, block cipher.Block) []byte {
	cfb := cipher.NewCFBEncrypter(block, commonIV)
	ciphertext := make([]byte, len(plaintext))
	cfb.XORKeyStream(ciphertext, plaintext)
	return []byte(ciphertext)
}

// AES CFB 解密，接收密文、明文长度和密文处理模块，返回字节流表示的明文和产生的错误
func AesDecode(cipherText []byte,
	plainLen int64,
	block cipher.Block) ([]byte, error) {
	cfbdec := cipher.NewCFBDecrypter(block, commonIV)
	plaintext := make([]byte, plainLen)
	cfbdec.XORKeyStream(plaintext, cipherText)
	return []byte(plaintext), nil
}

// -----------------------------------------------------------------------------
// Int64 转 8 字节流
func Int64ToBytes(i int64) []byte {
	var buf = make([]byte, 8)
	binary.BigEndian.PutUint64(buf, uint64(i))
	return buf
}

// 8 字节流转 Int64 类型
func BytesToInt64(buf []byte) int64 {
	return int64(binary.BigEndian.Uint64(buf[:8]))
}

// -----------------------------------------------------------------------------
// 根据传入的长度生成随机字符串
func GetRandomString(length int) string {
	str := "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
	bytes := []byte(str)
	result := []byte{}
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	for i := 0; i < length; i++ {
		result = append(result, bytes[r.Intn(len(bytes))])
	}
	return string(result)
}

// -----------------------------------------------------------------------------
// 计算传入字符串的MD5值，以32字节流返回
func MD5(text string) []byte {
	ctx := md5.New()
	ctx.Write([]byte(text))
	return []byte(hex.EncodeToString(ctx.Sum(nil)))
}

// -----------------------------------------------------------------------------
// 判断传入的字符串是否为大写的 MD5 格式
func IsMD5(text string) bool {
	if len(text) != 32 {
		return false
	}
	for _, char := range strings.ToUpper(text) {
		if char < '0' || char > '9' && char < 'A' || char > 'F' {
			return false
		}
	}
	return true
}

// -----------------------------------------------------------------------------
// 根据传入的安全等级生成随机 token
func GenerateToken(level uint8) []byte {
	if level <= 1 { // 128位，16字节
		return MD5(GetRandomString(128))[:16]
	} else if level == 2 { // 192位，24字节
		return MD5(GetRandomString(128))[:24]
	} else { // 256位，32字节
		return MD5(GetRandomString(128))[:32]
	}
}

// -----------------------------------------------------------------------------
// 根据传入的 reader 计算可读对象内容的 MD5 值，每 4MB 作为一块计算一次，拼接后
// 计算拼接字符串的 MD5 值作为结果。
func CalcMD5ForReader(reader *bufio.Reader) []byte {
	if reader == nil {
		return nil
	}
	ctx := md5.New()
	var length int
	buf := make([]byte, 0, conf.BUFLEN)
	midtermBuf := make([]byte, 0, conf.BUFLEN)
	midtermLen := 0
	currentLengthForBuf := 0
	for {
		if currentLengthForBuf == conf.BUFLEN {
			ctx.Write(buf[:conf.BUFLEN])
			copy(midtermBuf[midtermLen:midtermLen+32],
				[]byte(hex.EncodeToString(ctx.Sum(nil))[:32]))
			midtermLen += 32
			currentLengthForBuf = 0
			ctx.Reset()
		}
		length, _ = reader.Read(buf[currentLengthForBuf:conf.BUFLEN])
		currentLengthForBuf += length
		if length == 0 {
			ctx.Write(buf[:currentLengthForBuf])
			copy(midtermBuf[midtermLen:midtermLen+32],
				[]byte(hex.EncodeToString(ctx.Sum(nil))[:32]))
			ctx.Reset()
			midtermLen += 32
			ctx.Write(midtermBuf[:midtermLen])
			return []byte(strings.ToUpper(hex.EncodeToString(ctx.Sum(nil))))
		}
	}
	return nil
}
