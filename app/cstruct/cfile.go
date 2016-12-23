/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：CFILE 结构的定义与基本方法实现
*/

package cstruct

import (
	"fmt"
	"strings"
	"time"
)

// -----------------------------------------------------------------------------
// CFILE 结构
type cfile struct {
	id         int64     // 文件实体编号
	ref        int32     // 文件实体引用次数
	size       int64     // 文件实体大小
	downloaded int64     // 文件实体下载次数
	timestamp  time.Time // 文件实体创建时间
	userlist   []*cuser  // 引用此文件实体的用户列表
}

// CFILE 类型接口
type CFile interface {
	GetId() int64
	GetTimestamp() time.Time
	GetSize() int64
	GetRef() int32
	SetId(int64) bool   // 设置文件实体编号
	SetSize(int64) bool // 设置文件实体大小
	AddRef(int32) bool  // 增加引用数
}

// -----------------------------------------------------------------------------
// CFILE 工厂方法
func NewCFile(fid int64, fsize int64) *cfile {
	f := new(cfile)
	f.ref = 0
	f.id = fid
	f.size = fsize
	f.userlist = nil
	f.timestamp = time.Now()
	return f
}

// -----------------------------------------------------------------------------
// CFILE 元素相关方法
func (f *cfile) GetId() int64 {
	return f.id
}

func (f *cfile) GetTimestamp() time.Time {
	return f.timestamp
}

func (f *cfile) GetSize() int64 {
	return f.size
}

func (f *cfile) GetRef() int32 {
	return f.ref
}

func (f *cfile) SetId(fid int64) bool {
	f.id = fid
	return true
}

func (f *cfile) SetSize(fsize int64) bool {
	f.size = fsize
	return true
}

func (f *cfile) AddRef(offset int32) bool {
	f.ref += offset
	return true
}

// -----------------------------------------------------------------------------
// 判定文件名是否合法，公有方法
func isFilenameValid(filename string) bool {
	if len(filename) > 128 ||
		strings.Count(filename, "/") > 0 ||
		strings.Count(filename, "\\") > 0 ||
		strings.Count(filename, "+") > 0 ||
		strings.Count(filename, ":") > 0 ||
		strings.Count(filename, "*") > 0 ||
		strings.Count(filename, "?") > 0 ||
		strings.Count(filename, "<") > 0 ||
		strings.Count(filename, ">") > 0 ||
		strings.Count(filename, "\"") > 0 {
		fmt.Println("警告：文件名称不合法，名称为：", filename)
		return false
	} else {
		return true
	}
}

// -----------------------------------------------------------------------------
// 判定路径是否合法，公有方法
func isPathFormatValid(path string) bool {
	if len(path) < 1 ||
		len(path) > 256 ||
		path[0] != '/' ||
		path[len(path)-1] != '/' ||
		strings.Count(path, "../") > 0 ||
		strings.Count(path, "/..") > 0 ||
		strings.Count(path, "+") > 0 ||
		strings.Count(path, ":") > 0 ||
		strings.Count(path, "*") > 0 ||
		strings.Count(path, "?") > 0 ||
		strings.Count(path, "%") > 0 ||
		strings.Count(path, "<") > 0 ||
		strings.Count(path, ">") > 0 ||
		strings.Count(path, "\"") > 0 {
		fmt.Println("警告：文件路径不合法，路径为：", path)
		return false
	} else {
		return true
	}
}
