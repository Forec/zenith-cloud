/*
author: Forec
last edit date: 2016/12/3
email: forec@bupt.edu.cn
LICENSE
Copyright (c) 2015-2017, Forec <forec@bupt.edu.cn>

Permission to use, copy, modify, and/or distribute this code for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
*/

package cstruct

import (
	"bufio"
	auth "cloud-storage/authenticate"
	conf "cloud-storage/config"
	trans "cloud-storage/transmit"
	"database/sql"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

// 下载资源记录结构
type downloadItem struct {
	cfileid  int    // 实体文件编号
	filename string // 文件名
	size     int    //文件大小
}

// DealWithTransmission：用户传输请求转发函数
func (u *cuser) DealWithTransmission(db *sql.DB, t trans.Transmitable) {
	fmt.Println("用户" + u.username + " 启动传输线程")

	// 传输结束后从用户传输列表移除线程
	defer u.RemoveTransmit(t)
	recvB, err := t.RecvBytes()
	if err != nil {
		u.RemoveTransmit(t)
		return
	}
	command := string(recvB)
	fmt.Println("用户请求传输指令：", command)
	switch {
	case len(command) >= 3 && strings.ToUpper(command[:3]) == "GET":
		// 下载请求
		u.get(db, command, t)
	case len(command) >= 3 && strings.ToUpper(command[:3]) == "PUT":
		// 上传请求
		u.put(db, command, t)
	default:
		// 指令无法识别
		t.SendBytes(auth.Int64ToBytes(300))
		fmt.Println("指令无法识别！")
	}
	fmt.Println("用户" + u.username + "传输完成")
}

// get：下载请求处理函数
func (u *cuser) get(db *sql.DB, command string, t trans.Transmitable) {
	// 指令格式: GET<SEP>文件uid<SEP>提取码
	var err error
	var isdir, private bool
	var uid, valid int = 0, 0
	var recordCount, ownerid, cfileid, parentLength, downloaded int
	var pass, filename, originFilename, path, subpath string
	var queryRow *sql.Row
	var queryRows *sql.Rows
	var fileReader *bufio.Reader
	args := generateArgs(command, 3)
	if args == nil {
		valid = 1 // 无法获取参数，valid = 1：指令不合法
		goto GET_VERIFY
	}
	uid, err = strconv.Atoi(args[1])
	if err != nil || strings.ToUpper(args[0]) != "GET" {
		// 参数格式不正确，指令不合法
		valid = 1
		goto GET_VERIFY
	}
	queryRow = db.QueryRow(fmt.Sprintf(`select isdir, private, ownerid, linkpass, cfileid, filename, path, 
		downloaded from ufile where uid=%d`, uid))
	if queryRow == nil {
		valid = 2 // 数据库查询出错，valid = 2：无法获取记录
		goto GET_VERIFY
	}
	queryRow.Scan(&isdir, &private, &ownerid, &pass, &cfileid, &filename, &path, &downloaded)
	if int64(ownerid) != u.id && pass != args[2] || int64(ownerid) != u.id && private {
		// 用户不是资源所有者且提取码不正确 或 用户不是资源所有者且资源为私有
		valid = 3 // 用户不具有权限，valid = 3：无法下载
		goto GET_VERIFY
	}
GET_VERIFY:
	if valid != 0 {
		// 指令执行失败，发送错误码
		t.SendBytes([]byte("NOTPERMITTED"))
		fmt.Println("下载指令执行失败，错误码为 ", valid)
		return
	} else {
		// 指令被允许执行，发送激活码
		t.SendBytes([]byte("VALID"))
	}

	// 更新待下载资源的下载次数
	db.Exec(fmt.Sprintf(`update ufile set downloaded=%d where uid=%d`, downloaded+1, uid))
	var totalFileLength int = 0
	if !isdir {
		// 仅下载单个文件时，待发送文件数目为 1
		if !t.SendBytes(auth.Int64ToBytes(int64(1))) {
			return
		}
		// 发送待下载文件文件名
		if !t.SendBytes([]byte(filename)) {
			return
		}
		// 发送待下载资源的类型（文件/目录）
		if !t.SendBytes([]byte(auth.Int64ToBytes(int64(0)))) {
			return
		}
		if cfileid < 0 {
			// 文件未引用实体文件，则为空文件
			t.SendFromReader(nil, int64(0))
		} else {
			// 提取实体文件的大小
			queryRow = db.QueryRow(fmt.Sprintf(`select size from cfile where uid=%d`, cfileid))
			if queryRow == nil {
				return
			}
			err = queryRow.Scan(&totalFileLength)
			if err != nil {
				fmt.Println("下载请求，扫描文件大小出错，错误信息：", err.Error())
			}

			// 获取实体文件句柄
			file, err := os.Open(fmt.Sprintf("%s%d", conf.STORE_PATH, cfileid))
			if err != nil {
				fmt.Println("下载请求，无法打开请求资源的实体文件")
				return
			}
			defer file.Close()
			fileReader = bufio.NewReader(file)

			// 启动传输函数
			t.SendFromReader(fileReader, int64(totalFileLength))
		}
	} else {
		// 用户试图下载一个目录，需计算共传输多少文件/目录
		queryRow = db.QueryRow(fmt.Sprintf(`select count (*) from ufile where 
			path like '%s%%' and ownerid=%d`,
			path+filename+"/", u.id))
		originFilename = filename
		if queryRow == nil {
			return
		}
		// 扫描待下载文件数目
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println("下载请求，扫描待下载文件数目出错，错误信息:", err.Error())
			return
		}
		// 增加 1 个待下载数量（根目录）
		recordCount += 1
		// 发送待下载文件数量
		if !t.SendBytes(auth.Int64ToBytes(int64(recordCount))) {
			return
		}
		// 发送根目录名
		if !t.SendBytes([]byte(filename)) {
			return
		}
		// 发送 1（根目录类型为 1，目录）
		if !t.SendBytes(auth.Int64ToBytes(int64(1))) {
			return
		}
		parentLength = len(path)

		// 提取待下载目录下的目录结构
		queryRows, err = db.Query(fmt.Sprintf(`select filename, path from ufile where path like '%s%%' 
			and isdir=1 and ownerid=%d order by length(path)`, path+filename+"/", ownerid))
		if err != nil {
			return
		}
		for queryRows.Next() {
			err = queryRows.Scan(&filename, &subpath)
			if err != nil {
				continue
			}
			filename = subpath[parentLength:] + filename
			// 根据客户端版本决定是否修改路径中的分隔符
			if conf.CLIENT_VERSION == "Windows" {
				filename = strings.Replace(filename, "/", "\\", -1)
			}
			// 发送相对路径名
			if !t.SendBytes([]byte(filename)) {
				return
			}
			// 发送 1（目录类型）
			if !t.SendBytes(auth.Int64ToBytes(int64(1))) {
				return
			}
		}
		// 发送待下载路径下的文件
		queryRow = db.QueryRow(fmt.Sprintf(`select count (*) from ufile where path like '%s%%'
			and isdir=0 and ownerid=%d`, path+originFilename+"/", ownerid))
		if queryRow == nil {
			return
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			return
		}
		// 待下载文件信息列表
		file_list := make([]downloadItem, 0, recordCount)
		var fileItem downloadItem
		queryRows, err = db.Query(fmt.Sprintf(`select filename, path, cfileid from ufile where path like '%s%%' 
			and isdir=0 and ownerid=%d order by length(path)`, path+originFilename+"/", ownerid))
		if err != nil {
			return
		}
		for queryRows.Next() {
			err = queryRows.Scan(&filename, &subpath, &cfileid)
			if err != nil {
				continue
			}
			// 获取实体文件大小，若无实体文件编号则大小为 0
			if cfileid < 0 {
				totalFileLength = 0
			} else {
				queryRow = db.QueryRow(fmt.Sprintf(`select size from cfile where uid=%d`, cfileid))
				if queryRow == nil {
					totalFileLength = 0
					continue
				}
				err = queryRow.Scan(&totalFileLength)
				if err != nil {
					totalFileLength = 0
					continue
				}
			}
			fileItem.size = totalFileLength
			// 生成文件在客户端的相对路径
			filename = subpath[parentLength:] + filename
			// 根据客户端系统替换路径分隔符
			if conf.CLIENT_VERSION == "Windows" {
				filename = strings.Replace(filename, "/", "\\", -1)
			}
			fileItem.filename = filename
			fileItem.cfileid = cfileid
			file_list = append(file_list, fileItem)
		}
		for _, fileItem = range file_list {
			// 发送文件名
			if !t.SendBytes([]byte(fileItem.filename)) {
				break
			}
			fmt.Println("发送文件名: ", fileItem.filename)
			// 发送 0 （文件类型）
			if !t.SendBytes(auth.Int64ToBytes(int64(0))) {
				break
			}
			if fileItem.size > 0 && fileItem.cfileid >= 0 {
				// 待下载文件引用了实体文件，获取实体文件句柄
				file, err := os.Open(fmt.Sprintf("%s%d", conf.STORE_PATH, fileItem.cfileid))
				if err != nil {
					// 发生错误时发送空文件
					fileItem.size = 0
					fmt.Println("下载请求，无法打开实体文件，错误信息：", err.Error())
					fileReader = nil
				} else {
					defer file.Close()
					fileReader = bufio.NewReader(file)
				}
			} else {
				fileReader = nil
			}
			// 发送文件，空文件使 reader 为 nil 即可跳过发送
			t.SendFromReader(fileReader, int64(fileItem.size))
		}
	}
}

// put：上传请求处理函数
func (u *cuser) put(db *sql.DB, command string, t trans.Transmitable) {
	// 传输流程:
	// 收取下载指令：PUT<SEP>上传文件uid<SEP>上传文件大小<SEP>上传文件 md5 值
	// 验证指令合法性并回送代码
	// 合法则启动传输，否则结束传输
	var err1, err2, err error
	var uid, _cid, cid, size, _ref, ref int
	var shouldTransmit, valid bool = true, true
	var queryRow *sql.Row
	args := generateArgs(command, 4)
	if args == nil {
		valid = false // 指令不合法，无法获取参数
	} else {
		uid, err1 = strconv.Atoi(args[1])
		size, err2 = strconv.Atoi(args[2])
		if err1 != nil || err2 != nil || strings.ToUpper(args[0]) != "PUT" ||
			// 指令格式错误
			!auth.IsMD5(args[3]) {
			fmt.Println("指令不合法")
			fmt.Println("用户声明的 MD5值为：", auth.IsMD5(args[3]))
			valid = false
		} else {
			// 查找实体文件列表中是否存在相同 md5 值的文件，并获取实体文件引用数
			queryRow = db.QueryRow(fmt.Sprintf(`select uid, ref from cfile 
				where md5='%s' and size=%d`, strings.ToUpper(args[3]), size))
			if queryRow == nil {
				shouldTransmit = true
			} else {
				err = queryRow.Scan(&cid, &ref)
				if err == nil {
					shouldTransmit = false
				} else {
					fmt.Println("上传请求，扫描cid 和引用数出错，错误信息：", err.Error())
				}
			}
		}
	}

	// 判断是否启动传输
	fmt.Println(shouldTransmit)
	if valid != true {
		// 指令不合法或文件不存在时发送 300 错误码
		t.SendBytes(auth.Int64ToBytes(300))
		fmt.Println("指令不合法，返回 300 错误码")
		return
	} else if shouldTransmit {
		// 启动传输返回 201 错误码
		t.SendBytes(auth.Int64ToBytes(201))
		fmt.Println("启动上传，返回 201")
		// 使用 md5 值创建临时文件并获取待临时文件句柄
		file, err := os.OpenFile(conf.STORE_PATH+args[3], os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0666)
		if err != nil {
			fmt.Println("Cannot Open File ", conf.STORE_PATH+args[3])
			t.SendBytes(auth.Int64ToBytes(500))
			fmt.Println("server internal error: cannot create openfile, ", err.Error())
			return
		}

		// 启动数据传输函数
		fileWriter := bufio.NewWriter(file)
		if t.RecvToWriter(fileWriter) {
			fmt.Println("上传请求，文件传输完成")
		} else {
			t.SendBytes(auth.Int64ToBytes(203))
			fmt.Println("上传请求，文件传输失败")
			return
		}
		_, err = db.Exec(fmt.Sprintf(`insert into cfile values(null, '%s', %d, 0, '%s')`,
			strings.ToUpper(args[3]), size, time.Now().Format("2006-01-02 15:04:05")))
		if err != nil {
			t.SendBytes(auth.Int64ToBytes(500))
			fmt.Println("上传请求，服务器错误，无法写入数据库请求，错误信息：", err.Error())
			return
		}
		// 获取新加入实体文件的编号
		queryRow = db.QueryRow(`select max(uid) from cfile`)
		if queryRow == nil {
			t.SendBytes(auth.Int64ToBytes(500))
			fmt.Println("上传请求，服务器错误，无法获取最大实体文件记录值")
			return
		} else {
			err = queryRow.Scan(&cid)
			if err != nil {
				t.SendBytes(auth.Int64ToBytes(500))
				fmt.Println("上传请求，服务器错误，无法扫描最大实体文件记录值，错误信息：", err.Error())
				return
			}
		}
		file.Close()

		// 修改临时文件名为实体文件编号
		err = os.Rename(conf.STORE_PATH+args[3], fmt.Sprintf("%s%d", conf.STORE_PATH, cid))
		if err != nil {
			t.SendBytes(auth.Int64ToBytes(500))
			fmt.Println("上传请求，服务器内部错误，无法修改文件名，错误信息：", err.Error())
			return
		}
		// 获取实体文件句柄，计算 MD5 以验证用户提供的 MD5 值是否合法
		file, err = os.Open(fmt.Sprintf("%s%d", conf.STORE_PATH, cid))
		if err != nil {
			t.SendBytes(auth.Int64ToBytes(500))
			fmt.Println("上传请求，计算MD5前无法获取文件句柄，错误信息：", err.Error())
			return
		}
		fileReader := bufio.NewReader(file)
		_md5 := auth.CalcMD5ForReader(fileReader)
		file.Close()
		if _md5 == nil {
			// 计算 MD5 值失败
			t.SendBytes(auth.Int64ToBytes(500))
			fmt.Println("上传请求，服务器内部错误，无法计算MD5值")
			return
		}
		if strings.ToUpper(string(args[3])) != strings.ToUpper(string(_md5)) {
			// 用户声明的 MD5 值和服务器计算的 MD5 值不一致
			fmt.Println(strings.ToUpper(string(args[3])), strings.ToUpper(string(_md5)))
			t.SendBytes(auth.Int64ToBytes(403))
			fmt.Println("上传请求，用户声明的 MD5 值不合法！")
			// 从数据库删除实体文件记录，并从文件存储路径删除实体文件
			db.Exec(fmt.Sprintf("delete from cfile where uid=%d", cid))
			os.Remove(fmt.Sprintf("%s%s", conf.STORE_PATH, cid))
			return
		}
		ref = 0
	}
	fmt.Println("上传请求，无需传输 或 已经传输结束")

	// 检查用户是否已创建要上传的文件
	queryRow = db.QueryRow(fmt.Sprintf(`select cfileid from ufile where uid=%d and ownerid=%d`,
		uid, u.id))
	if queryRow == nil {
		t.SendBytes(auth.Int64ToBytes(301))
		fmt.Println("上传请求，用户尚未创建要上传的文件")
		return
	} else {
		err = queryRow.Scan(&_cid)
		if err != nil {
			t.SendBytes(auth.Int64ToBytes(500))
			fmt.Println("上传请求，服务器内部错误，无法扫描待上传文件对应的实体文件编号，错误信息：", err.Error())
			return
		}
	}

	// 用户文件引用的实体文件未发生变化，实体文件引用数不需更新
	if _cid == cid {
		// 向客户端发送 200 代码，确认传输结束
		t.SendBytes(auth.Int64ToBytes(200))
		fmt.Println("上传请求，文件传输结束，无需更新原资源信息")
		return
	}

	// 获取实体文件的引用记录数
	queryRow = db.QueryRow(fmt.Sprintf(`select ref from cfile where uid=%d`, _cid))
	if _cid > 0 && queryRow != nil {
		err = queryRow.Scan(&_ref)
		if err == nil {
			if _ref != 1 {
				db.Exec(fmt.Sprintf(`update cfile set ref=%d where uid=%d`, _ref-1, _cid))
			} else {
				db.Exec(fmt.Sprintf(`delete from cfile where uid=%d`, _cid))
			}
		}
	}

	// 更新资源文件引用的实体文件编号
	_, err = db.Exec(fmt.Sprintf(`update ufile set cfileid=%d where uid=%d and ownerid=%d`,
		cid, uid, u.id))
	if err != nil {
		t.SendBytes(auth.Int64ToBytes(500))
		fmt.Println("上传请求，服务器内部错误，更新引用实体文件编号失败，错误信息：", err.Error())
		return
	}
	// 更新实体文件的引用记录数
	_, err = db.Exec(fmt.Sprintf(`update cfile set ref=%d where uid=%d`,
		ref+1, cid))
	if err != nil {
		t.SendBytes(auth.Int64ToBytes(500))
		fmt.Println("服务器内部错误，无法更新实体文件引用数，错误信息：", err.Error())
	} else {
		u.used += int64(size)
		db.Exec(fmt.Sprintf(`update cuser set used=%d where uid=%d`,
			u.used, u.id)) // 更新用户使用云盘容量

		t.SendBytes(auth.Int64ToBytes(200))
		fmt.Println("上传请求，传输操作结束")
	}
}
