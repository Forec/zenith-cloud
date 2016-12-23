/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：UFILE 结构的测试代码
*/

package cstruct

import (
	"testing"
)

// -----------------------------------------------------------------------------
// 测试 UFILE 工厂方法
func TestNewUFile(t *testing.T) {
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil {
		t.Errorf("错误：UFile 工厂方法失败")
	}
}

// -----------------------------------------------------------------------------
// 测试 UFILE 元素获取方法
func TestGetFilename(t *testing.T) {
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil || uf.GetFilename() != "userfile" {
		t.Errorf("错误：UFile 获取文件名失败")
	}
}

func TestGetPath(t *testing.T) {
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil || uf.GetPath() != "./user/files/" {
		t.Errorf("错误：UFile 获取文件路径失败")
	}
}

func TestGetShared(t *testing.T) {
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil || uf.GetShared() != 0 {
		t.Errorf("错误：UFile 获取分享数失败")
	}
}

func TestGetDownloaded(t *testing.T) {
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil || uf.GetDownloaded() != 0 {
		t.Errorf("错误：UFile 获取下载量失败")
	}
}

func TestGetOwner(t *testing.T) {
	c := NewCUser("forec", int64(10086), "../")
	uf := NewUFile(nil, c, "userfile", "./user/files/")
	if uf == nil || uf.GetOwner() == nil ||
		uf.GetOwner().GetId() != c.GetId() {
		t.Errorf("错误：UFile 获取所有者失败")
	}
}

func TestGetPointer(t *testing.T) {
	f := NewCFile(int64(10086), int64(1000000))
	uf := NewUFile(f, nil, "userfile", "./user/files/")
	if uf == nil || uf.GetPointer() == nil ||
		uf.GetPointer().GetId() != f.GetId() {
		t.Errorf("错误：UFile 获取引用实体文件失败")
	}
}

func TestGetPerlink(t *testing.T) {
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil || uf.SetPerlink("https://127.0.0.1/test") != true ||
		uf.GetPerlink() != "https://127.0.0.1/test" {
		t.Errorf("错误：UFile 获取外链失败")
	}
}

// -----------------------------------------------------------------------------
// 测试 UFILE 元素修改方法
func TestIncShared(t *testing.T) {
	f := NewCFile(int64(10086), int64(1000000))
	uf := NewUFile(f, nil, "userfile", "./user/files/")
	if uf == nil || uf.IncShared() != true || uf.GetShared() != 1 {
		t.Errorf("错误：UFile 修改分享数失败")
	}
}

func TestIncDownloaded(t *testing.T) {
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil || uf.IncDowned() != true || uf.GetDownloaded() != 1 {
		t.Errorf("错误：UFile 修改下载量失败")
	}
}

// -----------------------------------------------------------------------------
// 测试 UFile 元素设置方法
func TestSetOwner(t *testing.T) {
	c := NewCUser("forec", int64(10086), "../")
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil || uf.SetOwner(c) != true ||
		uf.GetOwner() == nil || uf.GetOwner().GetId() != c.GetId() {
		t.Errorf("错误：UFile 设置所有者失败")
	}
}

func TestSetPointer(t *testing.T) {
	f := NewCFile(int64(10086), int64(1000000))
	uf := NewUFile(nil, nil, "userfile", "./user/files/")
	if uf == nil || uf.SetPointer(f) != true ||
		uf.GetPointer() == nil || uf.GetPointer().GetId() != f.GetId() {
		t.Errorf("错误：UFile 设置文件引用失败")
	}
}
