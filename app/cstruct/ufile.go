/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：UFILE 结构定义与方法实现
*/

package cstruct

import (
	"time"
)

// -----------------------------------------------------------------------------
// UFILE 结构
type ufile struct {
	pointer    *cfile
	owner      *cuser
	filename   string
	path       string
	perlink    string
	timestamp  time.Time
	shared     int32
	downloaded int32
}

// UFILE 接口
type UFile interface {
	GetFilename() string
	GetShared() int32
	GetDownloaded() int32
	GetPath() string
	GetPerlink() string
	GetTime() time.Time
	GetPointer() *cfile
	GetOwner() *cuser
	IncShared() bool
	IncDowned() bool
	SetPath(string) bool
	SetPerlink(string) bool
	SetPointer(*cfile) bool
	SetOwner(*cuser) bool
}

// -----------------------------------------------------------------------------
// UFILE 工厂方法
func NewUFile(upointer *cfile,
	uowner *cuser,
	uname string,
	upath string) *ufile {
	u := new(ufile)
	u.downloaded = 0
	u.shared = 0
	u.pointer = upointer
	u.owner = uowner
	u.filename = uname
	u.path = upath
	u.timestamp = time.Now()
	u.perlink = ""
	if upointer != nil {
		upointer.AddRef(1)
	}
	return u
}

// -----------------------------------------------------------------------------
// UFILE 元素获取方法
func (u *ufile) GetFilename() string {
	return u.filename
}

func (u *ufile) GetShared() int32 {
	return u.shared
}

func (u *ufile) GetTime() time.Time {
	return u.timestamp
}

func (u *ufile) GetDownloaded() int32 {
	return u.downloaded
}

func (u *ufile) GetPath() string {
	return u.path
}

func (u *ufile) GetPerlink() string {
	return u.perlink
}

func (u *ufile) GetPointer() *cfile {
	return u.pointer
}

func (u *ufile) GetOwner() *cuser {
	return u.owner
}

// -----------------------------------------------------------------------------
// UFILE 元素设置方法
func (u *ufile) SetPath(upath string) bool {
	u.path = upath
	return true
}

func (u *ufile) SetPerlink(uperlink string) bool {
	u.perlink = uperlink
	return true
}

func (u *ufile) SetPointer(upointer *cfile) bool {
	u.pointer = upointer
	return true
}

func (u *ufile) SetOwner(uowner *cuser) bool {
	u.owner = uowner
	return true
}

// -----------------------------------------------------------------------------
// UFILE 元素修改方法
func (u *ufile) IncShared() bool {
	u.shared++
	return true
}

func (u *ufile) IncDowned() bool {
	u.downloaded++
	return true
}
