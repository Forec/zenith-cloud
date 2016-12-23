/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：服务器使用相关结构列表方法
*/

package cstruct

import (
	conf "cloud-storage/config"
	trans "cloud-storage/transmit"
)

// -----------------------------------------------------------------------------
// 向用户列表添加新用户，按 2 的指数拓展内存，减少分配次数
func AppendUser(slice []User, data ...User) []User {
	m := len(slice)
	n := m + len(data)
	if n > cap(slice) {
		// 长度不足时拓展一倍长度
		newSlice := make([]User, (n+1)*2)
		copy(newSlice, slice)
		slice = newSlice
	}
	slice = slice[0:n]
	copy(slice[m:n], data)
	return slice
}

// -----------------------------------------------------------------------------
// 向 UFile 列表添加新的文件记录，按 2 的指数拓展内存，减少分配次数
func AppendUFile(slice []UFile, data ...UFile) []UFile {
	m := len(slice)
	n := m + len(data)
	if n > cap(slice) {
		newSlice := make([]UFile, (n+1)*2)
		copy(newSlice, slice)
		slice = newSlice
	}
	slice = slice[0:n]
	copy(slice[m:n], data)
	return slice
}

// -----------------------------------------------------------------------------
// 向活动连接池附加新的连接（池）
func AppendTransmitable(slice []trans.Transmitable,
	data ...trans.Transmitable) []trans.Transmitable {
	if len(slice)+len(data) >= conf.MAXTRANSMITTER {
		slice = append(slice, data[:conf.MAXTRANSMITTER-len(slice)]...)
	} else {
		slice = append(slice, data...)
	}
	return slice
}

// -----------------------------------------------------------------------------
// 在 UFile 列表中根据路径过滤
func UFileIndexByPath(slice []UFile, path string) []UFile {
	filter := make([]UFile, 0, 10)
	for _, uf := range slice {
		if uf.GetPath() == path {
			filter = AppendUFile(filter, uf)
		}
	}
	return filter
}

// -----------------------------------------------------------------------------
// 在 UFile 列表中根据编号索引
func UFileIndexById(slice []UFile, id int64) []UFile {
	filter := make([]UFile, 0, 10)
	for _, uf := range slice {
		if uf.GetPointer().GetId() == id {
			filter = AppendUFile(filter, uf)
		}
	}
	return filter
}

// -----------------------------------------------------------------------------
// 在用户列表中根据用户名索引
func UserIndexByName(slice []User, name string) User {
	for _, uc := range slice {
		if uc.GetUsername() == name {
			return uc
		}
	}
	return nil
}
