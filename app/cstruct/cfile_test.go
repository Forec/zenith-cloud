/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：CFILE 结构的测试代码
*/

package cstruct

import (
	"testing"
	"time"
)

// -----------------------------------------------------------------------------
// 测试工厂方法
func TestNewCFile(t *testing.T) {
	c := NewCFile(int64(12345), int64(1234567))
	if c == nil {
		t.Errorf("错误：CFILE 工厂方法失败")
	}
}

// -----------------------------------------------------------------------------
// 测试增加引用数
func TestAddRef(t *testing.T) {
	c := NewCFile(int64(12345), int64(1234567))
	if c == nil || c.AddRef(100) != true && c.GetRef() != 100 {
		t.Errorf("错误：CFILE 引用数增加失败")
	}
}

// -----------------------------------------------------------------------------
// 测试元素获取方法
func TestGetID(t *testing.T) {
	c := NewCFile(int64(12345), int64(1234567))
	if c.GetId() != 12345 {
		t.Errorf("错误：CFILE 获取 Id 失败")
	}
}

func TestGetSize(t *testing.T) {
	c := NewCFile(int64(12345), int64(1234567))
	if c.GetSize() != 1234567 {
		t.Errorf("错误：CFILE 获取大小失败")
	}
}

func TestGetTimestamp(t *testing.T) {
	c := NewCFile(int64(12345), int64(1234567))
	if time.Now().Sub(c.GetTimestamp()) > time.Second {
		t.Errorf("错误：CFILE 获取创建时间失败")
	}
}

// -----------------------------------------------------------------------------
// 测试元素设置方法
func TestSetId(t *testing.T) {
	c := NewCFile(int64(12345), int64(1234567))
	if c.SetId(777) != true || c.GetId() != 777 {
		t.Errorf("错误：CFILE ID 设置失败")
	}
}

func TestSetSize(t *testing.T) {
	c := NewCFile(int64(12345), int64(1234567))
	if c.SetSize(777) != true || c.GetSize() != 777 {
		t.Errorf("错误：CFILE 大小设置失败")
	}
}
