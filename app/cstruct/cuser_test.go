/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：CUser 结构的测试代码
*/

package cstruct

import (
	trans "cloud-storage/transmit"
	"testing"
)

// 测试工厂方法
func TestNewCuser(t *testing.T) {
	u := NewCUser("default", 0, ".")
	if u == nil {
		t.Errorf("错误：CUser 工厂方法失败")
	}
}

// 测试获取用户名
func TestGetUsername(t *testing.T) {
	u := NewCUser("default", 0, ".")
	if u == nil || u.GetUsername() != "default" {
		t.Errorf("错误：CUser 获取用户名失败")
	}
}

// 测试获取用户编号
func TestGetId(t *testing.T) {
	u := NewCUser("default", 0, ".")
	if u == nil || u.GetId() != 0 {
		t.Errorf("错误：CUser 获取编号失败")
	}
}

// 测试获取用户 token
func TestGetToken(t *testing.T) {
	u := NewCUser("default", 0, ".")
	if u == nil || u.GetToken() != "" {
		t.Errorf("错误：CUser 获取 token 失败")
	}
}

// 测试增加新活动连接
func TestAddTransmitter(t *testing.T) {
	u := NewCUser("default", 0, ".")
	c := trans.NewTransmitter(nil, 0, nil)
	if u.AddTransmit(c) != true {
		t.Errorf("错误：CUser 增加活动连接失败")
	}
}

// 测试移除活动连接
func TestRemoveTransmitter(t *testing.T) {
	u := NewCUser("default", 0, ".")
	c := trans.NewTransmitter(nil, 0, nil)
	if u.AddTransmit(c) != true || u.RemoveTransmit(c) != true {
		t.Errorf("错误：CUser 移除活动连接失败失败")
	}
}
