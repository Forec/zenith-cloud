/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：CUser 结构的定义与基本方法实现
*/

package cstruct

import (
	trans "cloud-storage/transmit"
	"database/sql"
	"fmt"
)

// 用户结构
type cuser struct {
	id          int64                // 用户编号
	used        int64                // 用户已使用的云盘容量
	maxm        int64                // 用户可使用的最大云盘容量
	listen      trans.Transmitable   // 与客户端交互命令的连接
	infos       trans.Transmitable   // 向客户端推送消息的连接
	username    string               // 用户邮箱
	nickname    string               // 用户昵称
	token       string               // 用户本次在线使用的 token
	curpath     string               // 用户当前所在的虚拟路径
	avatar_hash string               // 用户头像链接
	pass_hash   string               // 用户密码哈希值
	worklist    []trans.Transmitable // 用户当前活动连接池
}

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
	InfoSend(string) bool
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

// -----------------------------------------------------------------------------
// CUser 结构的工厂方法，产生一个新的 CUser 实例
func NewCUser(username string, uid int64, curpath string) *cuser {
	u := new(cuser)
	u.listen = nil
	u.id = uid
	u.nickname = ""
	u.username = username
	u.curpath = curpath
	u.worklist = nil
	u.token = ""
	return u
}

// 用户编号
func (u *cuser) GetId() int64 {
	return u.id
}

// 用户登录使用名称
func (u *cuser) GetUsername() string {
	return u.username
}

// 用户当前路径
func (u *cuser) SetPath(path string) bool {
	u.curpath = path
	return true
}

// 用户命令交互连接
func (u *cuser) SetListener(t trans.Transmitable) bool {
	u.listen = t
	return true
}

// 用户昵称
func (u *cuser) GetNickname() string {
	return u.nickname
}

func (u *cuser) SetNickname(_nickname string) bool {
	u.nickname = _nickname
	return true
}

// 用户监听线程
func (u *cuser) GetInfos() trans.Transmitable {
	return u.infos
}

func (u *cuser) SetInfos(t trans.Transmitable) bool {
	u.infos = t
	return true
}

// 已使用云盘容量
func (u *cuser) GetUsed() int64 {
	return u.used
}

func (u *cuser) SetUsed(size int64) bool {
	u.used = size
	return true
}

// 最大云盘容量
func (u *cuser) GetMaxm() int64 {
	return u.maxm
}

func (u *cuser) SetMaxm(size int64) bool {
	u.maxm = size
	return true
}

// 用户当前连接使用的 token
func (u *cuser) GetToken() string {
	return u.token
}

func (u *cuser) SetToken(t string) bool {
	u.token = t
	return true
}

// 用户头像链接
func (u *cuser) GetAvatar() string {
	return u.avatar_hash
}

func (u *cuser) SetAvatar(_avatar string) bool {
	u.avatar_hash = _avatar
	return true
}

// 用户密码哈希值
func (u *cuser) GetPassHash() string {
	return u.pass_hash
}

func (u *cuser) SetPassHash(_passhash string) bool {
	u.pass_hash = _passhash
	return true
}

// 用户当前活动连接池
func (u *cuser) GetWorkList() []trans.Transmitable {
	return u.worklist
}

// 发送消息
func (u *cuser) InfoSend(message string) bool {
	return u.infos.SendBytes([]byte(message))
}

// -----------------------------------------------------------------------------
// AddTransmit：向用户活动连接池中加入一个活动连接
func (u *cuser) AddTransmit(t trans.Transmitable) bool {
	if u.worklist == nil {
		u.worklist = make([]trans.Transmitable, 0, 2)
	}
	tempLen := len(u.worklist)
	u.worklist = AppendTransmitable(u.worklist, t)
	return len(u.worklist) != tempLen
}

// -----------------------------------------------------------------------------
// RemoveTransmit：从用户当前活动连接中移除某个连接
func (u *cuser) RemoveTransmit(t trans.Transmitable) bool {
	for i, ut := range u.worklist {
		if ut == t {
			u.worklist = append(u.worklist[:i], u.worklist[i+1:]...)
			t.Destroy()
			return true
		}
	}
	return false
}

// -----------------------------------------------------------------------------
// Logout：将当前用户登出
func (u *cuser) Logout() {
	if u.listen != nil {
		u.listen.Destroy()
	}
	// 销毁每个活动连接
	for _, ut := range u.worklist {
		if ut != nil {
			ut.Destroy()
		}
	}
	// 清空指针指向，垃圾回收
	u.worklist = nil
	u.infos = nil
	u.listen = nil
	fmt.Println("用户 " + u.username + " 登出")
}
