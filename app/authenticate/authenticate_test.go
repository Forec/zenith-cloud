/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：云服务器认证方法的测试代码
*/

package authenticate

import (
	"bufio"
	"fmt"
	"os"
	"testing"
)

type testS struct {
	in  string
	out string
}

// base64 模块测试样例（明文：编码）
var testBase64s = []testS{
	{"An Apple A Day", "QW4gQXBwbGUgQSBEYXk="},
	{"Keep Doctor Away  .", "S2VlcCBEb2N0b3IgQXdheSAgLg=="},
	{"+w-s*a/d%4", "K3ctcyphL2QlNA=="},
}

// AES 模块测试样例（明文：密文）
var testAESes = []testS{
	{"An Apple A Day", "\xca\x35\x19\xc8\x90\x0a\xed\x4f\x69\x09\x3e\xb2\x56\x41"},
	{"Keep Doctor Away  .", "\xc0\x3e\x5c\xf9\xc0\x3e\xee\x49\x3d\x27\x6c\xd6\x76\x4f\xed\x74\xeb\x1a\xe4"},
	{"+w-s*a/d%4", "\xa0\x2c\x14\xfa\xca\x1b\xae\x4e\x6c\x7c"},
}

// -----------------------------------------------------------------------------
// 测试模板函数，比较输入输出是否相同
func verify(t *testing.T, testnum int, testcase string,
	input, output, expected []byte, err error) {
	if string(expected) != string(output) || err != nil {
		t.Errorf("%d. %s with input = %s: output %s != %s",
			testnum,
			testcase,
			string(input),
			string(output),
			string(expected))
	}
}

// -----------------------------------------------------------------------------
// 测试 base64 模块
func TestBase64Encoding(t *testing.T) {
	for i, item := range testBase64s {
		s := Base64Encode([]byte(item.in))
		verify(t, i, "Base64Encoding",
			[]byte(item.in),
			[]byte(item.out), s, nil)
	}
}

func TestBase64Decoding(t *testing.T) {
	for i, item := range testBase64s {
		s, err := Base64Decode([]byte(item.out))
		verify(t, i, "Base64Decoding",
			[]byte(item.out),
			[]byte(item.in), s, err)
	}
}

// -----------------------------------------------------------------------------
// 测试 AES 模块
func TestNewAes(t *testing.T) {
	testkey1 := "abcdefghijklmnop"
	c := NewAesBlock([]byte(testkey1))
	if c == nil {
		t.Errorf("NewAesBlock returns nil with 128bits key %s", testkey1)
	}
	testkey2 := "abcdefghijklmnopabcdefgh"
	c = NewAesBlock([]byte(testkey2))
	if c == nil {
		t.Errorf("NewAesBlock returns nil with 192bits key %s", testkey2)
	}
	testkey3 := "abcdefghijklmnopabcdefghijklmnop"
	c = NewAesBlock([]byte(testkey3))
	if c == nil {
		t.Errorf("NewAesBlock returns nil with 256bits key %s", testkey3)
	}
}

func TestAesEncoding(t *testing.T) {
	c := NewAesBlock([]byte("AABCDEFGHIJKLMNOPBCDEFGHIJKLMNOP"))
	for i, item := range testAESes {
		s := AesEncode([]byte(item.in), c)
		verify(t, i, "AesEncoding 256bits",
			[]byte(item.in),
			[]byte(item.out), s, nil)
	}
}

func TestAesDecoding(t *testing.T) {
	c := NewAesBlock([]byte("AABCDEFGHIJKLMNOPBCDEFGHIJKLMNOP"))
	for i, item := range testAESes {
		s, err := AesDecode([]byte(item.out), int64(len(item.in)), c)
		verify(t, i, "AesDecoding 256bits",
			[]byte(item.out),
			[]byte(item.in), s, err)
	}
}

// -----------------------------------------------------------------------------
// 测试随机 token 生成
func TestGenerateToken(t *testing.T) {
	if !(len(GenerateToken(1)) == 16 &&
		len(GenerateToken(2)) == 24 &&
		len(GenerateToken(3)) == 32 &&
		len(GenerateToken(100)) == 32) {
		t.Errorf("生成 token 异常")
	}
}

// -----------------------------------------------------------------------------
// 测试 MD5 计算
func TestMD5File(t *testing.T) {
	file, err := os.Open("test.txt")
	if err != nil {
		fmt.Println("无法打开指定文件")
		return
	}
	defer file.Close()
	fileReader := bufio.NewReader(file)
	md5 := CalcMD5ForReader(fileReader)
	if md5 == nil {
		t.Errorf("生成 MD5 异常")
	}
}
