/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：用户代理命令交互处理方法文件
*/

package cstruct

import (
	auth "cloud-storage/authenticate"
	conf "cloud-storage/config"
	"database/sql"
	"fmt"
	"strconv"
	"strings"
	"time"
)

// 资源编号-资源路径结构
type id_path struct {
	u_id   int
	u_path string
}

// 资源路径-资源文件名结构
type path_name struct {
	u_path string
	u_name string
}

// 资源记录结构
type ufile_record struct {
	uid                                                     int
	ownerid, cfileid, shared, downloaded                    int
	private, isdir                                          bool
	linkpass, path, created, filename, perlink, description string
}

// -----------------------------------------------------------------------------
// DealWithRequests：用户命令转发函数
func (u *cuser) DealWithRequests(db *sql.DB) {
	// 发送用户资料
	u.listen.SendBytes([]byte(u.GetNickname()))        // 用户昵称
	u.listen.SendBytes(auth.Int64ToBytes(u.GetUsed())) // 用户已使用的容量
	u.listen.SendBytes(auth.Int64ToBytes(u.GetMaxm())) // 用户云盘最大容量
	avatar_link := u.GetAvatar()
	if avatar_link == "" { // 用户不存在默认头像链接，发送 none
		avatar_link = "none"
	}
	fmt.Println("获取到的头像链接: ", avatar_link)
	if avatar_link[0] == ':' { // 用户存在自定义头像外链，发送用户 id 及后缀
		parts := strings.Split(avatar_link, ".")
		suffix := parts[len(parts)-1]
		u.listen.SendBytes([]byte(
			fmt.Sprintf(`%d.%s`, u.id, suffix)))
		fmt.Println("发送头像链接:", fmt.Sprintf(`%d.%s`, u.id, suffix))
	} else { // 用户不存在自定义头像外链，发送 avatar 头像链接
		u.listen.SendBytes([]byte(u.GetAvatar()))
	}
	u.curpath = "/"
	fmt.Println("用户" + u.username + "开始处理命令")
	for {
		// 监听用户发送的命令
		recvB, err := u.listen.RecvBytes()
		if err != nil {
			return
		}
		command := string(recvB)
		fmt.Println(command)
		switch {
		case len(command) >= 2 && strings.ToUpper(command[:2]) == "RM":
			// 删除资源
			u.rm(db, command)
		case len(command) >= 2 && strings.ToUpper(command[:2]) == "CP":
			// 复制资源
			u.cp(db, command)
		case len(command) >= 2 && strings.ToUpper(command[:2]) == "MV":
			// 移动资源
			u.mv(db, command)
		case len(command) >= 2 && strings.ToUpper(command[:2]) == "LS":
			// 列出资源目录
			u.ls(db, command)
		case len(command) >= 4 && strings.ToUpper(command[:4]) == "SEND":
			// 发送消息
			u.send(db, command)
		case len(command) >= 4 && strings.ToUpper(command[:4]) == "FORK":
			// Fork 资源
			u.fork(db, command)
		case len(command) >= 5 && strings.ToUpper(command[:5]) == "TOUCH":
			// 创建新资源文件
			u.touch(db, command)
		case len(command) >= 5 && strings.ToUpper(command[:5]) == "CHMOD":
			// 改变资源权限
			u.chmod(db, command)
		default:
			// 指令无法识别，返回错误信息
			u.listen.SendBytes([]byte("Invalid Command"))
		}
	}
}

// -----------------------------------------------------------------------------
// generateArgs：根据分隔符将传入的指令划分为 arglen 块字符串
func generateArgs(command string, arglen int) []string {
	args := strings.Split(command, conf.SEPERATER)
	if arglen > 0 && len(args) != arglen {
		return nil
	}
	for i, arg := range args {
		args[i] = strings.Trim(arg, " ")
		args[i] = strings.Replace(args[i], "\r", "", -1)
		args[i] = strings.Replace(args[i], "\n", "", -1)
		if args[i] == "" {
			fmt.Println("生成参数：检测到参数为空")
			return nil
		}
	}
	return args
}

// -----------------------------------------------------------------------------
// generateSubPaths：根据传入的路径生成从根目录到该路径的所有子路径
func generateSubpaths(path string) []path_name {
	if !isPathFormatValid(path) {
		return nil
	}
	var record path_name
	var records []path_name = nil
	records = make([]path_name, 0, strings.Count(path, "/"))
	for {
		cp := strings.LastIndex(path, "/")
		path = path[:cp]
		cp = strings.LastIndex(path, "/")
		if cp < 0 {
			return records
		}
		record.u_name = path[cp+1:]
		record.u_path = path[:cp+1]
		records = append(records, record)
	}
	return records
}

// -----------------------------------------------------------------------------
// send：用户聊天消息处理函数
func (u *cuser) send(db *sql.DB, command string) {
	// 消息格式：SEND<SEP>对方用户昵称<SEP>消息内容
	var uid int
	var message string = ""
	var err error
	var valid bool = true
	var queryRow *sql.Row
	args := generateArgs(command, 0)
	if args == nil || len(args) < 2 {
		valid = false
		goto SEND_VERIFY
	}

	// 根据昵称检索用户
	queryRow = db.QueryRow(fmt.Sprintf(`select uid from cuser where 
		nickname='%s'`, args[1]))
	if queryRow == nil {
		fmt.Println("发送消息：未检索到相关 UID")
		valid = false
		goto SEND_VERIFY
	}

	// 获取消息接收方用户编号
	err = queryRow.Scan(&uid)
	if err != nil {
		fmt.Println("发送消息：扫描用户编号错误，错误信息：", err.Error())
		valid = false
		goto SEND_VERIFY
	}

	// 将参数 2 及之后的参数拼接为消息
	for i := 2; i < len(args); i++ {
		message += (args[i] + " ")
	}

	// 向数据库添加消息
	_, err = db.Exec(fmt.Sprintf(`insert into cmessages values(null, %d, %d, 
		'%s', '%s', 0, 0,0, 0)`, uid, u.id, message,
		time.Now().Format("2006-01-02 15:04:05")))
	if err != nil {
		fmt.Println("消息传递，服务器内部错误，添加数据库消息出错，错误信息：", err.Error())
		valid = false
	}
SEND_VERIFY:
	if !valid {
		// 发送失败返回错误码 400
		u.listen.SendBytes(auth.Int64ToBytes(int64(400)))
	} else {
		// 成功返回状态码 200
		u.listen.SendBytes(auth.Int64ToBytes(int64(200)))
	}
}

// -----------------------------------------------------------------------------
// chmod：用户资源权限修改函数
func (u *cuser) chmod(db *sql.DB, command string) {
	// 指令格式：CHMOD<SEP>待修改资源uid<SEP>修改后的权限<SEP>提取码
	var queryRow *sql.Row
	var queryRows *sql.Rows
	var uid, private, ownerid, recordCount int
	var isPrivate, isdir bool
	var valid bool = true
	var originPath, originName string
	var err, err1 error
	var uidList []int

	// 判断指令是否合法
	args := generateArgs(command, 4)
	if args == nil || strings.ToUpper(args[0]) != "CHMOD" {
		valid = false
		goto CHMOD_VERIFY
	}
	uid, err = strconv.Atoi(args[1])
	private, err1 = strconv.Atoi(args[2])
	if err != nil || err1 != nil {
		valid = false
		goto CHMOD_VERIFY
	}

	// 判断当前用户是否合法，以及待修改资源是否存在
	queryRow = db.QueryRow(fmt.Sprintf(`select ownerid, private, path, 
		filename, isdir from ufile where uid=%d`, uid))
	if queryRow == nil {
		valid = false
		goto CHMOD_VERIFY
	}
	err = queryRow.Scan(&ownerid, &isPrivate, &originPath, &originName, &isdir)
	if err != nil {
		valid = false
		fmt.Println(err.Error())
		goto CHMOD_VERIFY
	}

	// 当前用户不是待修改资源所有者，不具有权限
	if int64(ownerid) != u.id {
		valid = false
		goto CHMOD_VERIFY
	}

	// 修改原始资源的权限
	_, err = db.Exec(fmt.Sprintf(`update ufile set private=%d, linkpass='%s' 
		where uid=%d and ownerid=%d`, private, args[3], uid, u.id))
	if err != nil {
		fmt.Println("修改权限请求失败，修改原始文件权限失败，错误信息为：", err.Error())
		valid = false
		goto CHMOD_VERIFY
	}

	// 资源为目录时需递归修改目录下的全部资源
	if isdir {
		// 获取待修改资源目录下的文件数量
		queryRow = db.QueryRow(fmt.Sprintf(`select count (*) from ufile where 
			path like '%s%%' and ownerid=%d`, originPath+originName+"/", u.id))
		if queryRow == nil {
			fmt.Println("修改权限请求错误，获取记录数量失败，查询为空")
			valid = false
			goto CHMOD_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println("修改权限请求错误，扫描记录数量失败，错误信息为：", err.Error())
			valid = false
			goto CHMOD_VERIFY
		}

		// 生成待修改文件编号列表
		uidList = make([]int, 0, recordCount)
		queryRows, err = db.Query(fmt.Sprintf(`select uid from ufile where path 
			like '%s%%' and ownerid=%d`, originPath+originName+"/", u.id))
		defer queryRows.Close()
		if err != nil {
			valid = false
			fmt.Println("修改权限请求错误，查询失败，错误信息为：", err.Error())
			goto CHMOD_VERIFY
		}
		for queryRows.Next() {
			err = queryRows.Scan(&uid)
			if err != nil {
				fmt.Println("修改权限请求错误，资源记录格式不整齐，错误信息为：", err.Error())
				valid = false
				goto CHMOD_VERIFY
			}
			uidList = append(uidList, uid)
		}

		// 对每条待修改资源更新其权限和提取码
		for _, uid := range uidList {
			_, err = db.Exec(fmt.Sprintf(`update ufile set private=%d, 
				linkpass='%s' where uid=%d and ownerid=%d`,
				private, args[3], uid, u.id))
			if err != nil {
				valid = false
				fmt.Println("修改权限请求错误，更新资源权限失败，错误信息为：", err.Error())
				goto CHMOD_VERIFY
			}
		}
	}
CHMOD_VERIFY:
	if !valid {
		// 权限修改成功返回 400
		u.listen.SendBytes(auth.Int64ToBytes(int64(400)))
	} else {
		// 权限修改失败返回 200
		u.listen.SendBytes(auth.Int64ToBytes(int64(200)))
	}
}

// -----------------------------------------------------------------------------
// rm：用户资源删除请求处理函数
func (u *cuser) rm(db *sql.DB, command string) {
	// 命令格式：RM<SEP>待删除文件uid

	var queryRow *sql.Row
	var queryRows *sql.Rows
	var ref, recordCount, uid int
	var record ufile_record
	var crecords []int
	var valid int = -1
	var err error
	var tempSize int = 0

	// 判断指令合法性
	args := generateArgs(command, 2)
	if args == nil || strings.ToUpper(args[0]) != "RM" {
		valid = 0 // valid = 0：指令不合法
		goto RM_VERIFY
	}
	uid, err = strconv.Atoi(args[1])
	if err != nil {
		valid = 0
		goto RM_VERIFY
	}

	// 查询待删除资源状态信息
	queryRow = db.QueryRow(fmt.Sprintf(`select * from ufile where uid=%d 
		and ownerid=%d`, uid, u.id))
	if queryRow == nil {
		valid = 1 // 资源记录不存在
		goto RM_VERIFY
	}

	err = queryRow.Scan(&record.uid, &record.ownerid, &record.cfileid,
		&record.path, &record.perlink, &record.created, &record.shared,
		&record.downloaded, &record.filename, &record.private,
		&record.linkpass, &record.isdir, &record.description)
	fmt.Println("删除资源请求，资源所有者uid：", record.ownerid, "  资源uid：", uid)
	if err != nil || int64(record.ownerid) != u.id {
		valid = 2 // 当前用户不具有删除资源的权限
		fmt.Println("删除资源请求，当前用户不具有删除资源的权限，错误信息为：", err.Error())
		goto RM_VERIFY
	}

	// 执行删除操作
	_, err = db.Exec(fmt.Sprintf(`delete from ufile where uid=%d and 
		ownerid=%d`, uid, u.id))
	if err != nil {
		fmt.Println("删除资源请求，删除资源执行失败，错误信息：", err.Error())
		valid = 4 // 数据库操作异常
		goto RM_VERIFY
	}

	// 待删除资源为文件时，更新引用的实体文件引用数
	if !record.isdir {
		if record.cfileid >= 0 {
			queryRow = db.QueryRow(fmt.Sprintf(`select ref, size from cfile 
				where uid=%d`, record.cfileid))
			if queryRow == nil {
				valid = 1 // 删除文件引用的实体文件不存在
				fmt.Println("删除资源请求，无法找到待删除资源对应的实体文件")
				goto RM_VERIFY
			}
			err = queryRow.Scan(&ref, &tempSize)
			if err != nil {
				fmt.Println("删除资源请求，扫描实体文件引用值和大小失败，错误信息为：", err.Error())
				valid = 2 // 数据库记录格式有误
				goto RM_VERIFY
			}

			// 更新当前用户已使用网盘空间
			u.used -= int64(tempSize)

			if ref == 1 {
				// 删除的资源记录唯一引用了实体文件，可删除实体文件
				_, err = db.Exec(fmt.Sprintf(`delete from cfile where uid=%d`,
					record.cfileid))
				if err != nil {
					valid = 4 // 数据库操作执行失败
					goto RM_VERIFY
				}
			} else {
				// 删除的资源记录引用的实体文件仍被其他资源记录引用，减少引用数
				_, err = db.Exec(fmt.Sprintf(`update cfile set ref=%d where 
					uid=%d`, ref-1, record.cfileid))
				if err != nil {
					valid = 4 // 数据库操作执行失败
					goto RM_VERIFY
				}
			}
		}
	} else {
		// 处理待删除资源为目录的清空
		queryRow = db.QueryRow(fmt.Sprintf(`select count (*) from ufile where 
			path like '%s%%' and ownerid=%d`,
			record.path+record.filename+"/", u.id))
		if queryRow == nil {
			valid = 1 // 查询待删除资源目录下文件数量失败
			fmt.Println("错误：删除请求，查询待删除资源目录下文件数量失败")
			goto RM_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println("错误：删除请求，扫描待删除资源目录文件数量失败，错误信息：", err.Error())
			valid = 2 // 数据库记录格式错误
			goto RM_VERIFY
		}

		// 生成待删除资源编号列表，资源必须为引用了实体文件的记录
		crecords = make([]int, 0, recordCount)
		queryRows, err = db.Query(fmt.Sprintf(`select cfileid from ufile where 
			path like '%s%%' and ownerid=%d and cfileid>=0 and isdir=0`,
			record.path+record.filename+"/", u.id))
		defer queryRows.Close()
		if err != nil {
			fmt.Println("错误：删除请求，查询对应实体文件失败，错误信息：", err.Error())
			valid = 5 // 数据库查询失败
			goto RM_VERIFY
		}
		for queryRows.Next() {
			err = queryRows.Scan(&ref)
			if err != nil {
				fmt.Println("错误：删除请求，扫描待删除文件对应实体失败，错误信息：", err.Error())
				valid = 2 // 数据库记录格式不正确
				goto RM_VERIFY
			}
			crecords = append(crecords, ref)
		}

		// 删除待删除目录目录下所有资源
		_, err = db.Exec(fmt.Sprintf(`delete from ufile where path like '%s%%' 
			and ownerid=%d`, record.path+record.filename+"/", u.id))
		if err != nil {
			fmt.Println("错误：从数据库中删除指定资源失败，错误信息：", err.Error())
			valid = 4 // database operate error
			goto RM_VERIFY
		}

		// 遍历此前生成的待删除文件列表，更新被引用的文件实体引用数
		for _, cid := range crecords {
			queryRow = db.QueryRow(fmt.Sprintf(`select ref, size from cfile
				where uid=%d`, cid))
			if queryRow == nil {
				continue
			}
			err = queryRow.Scan(&ref, &tempSize)
			if err != nil {
				fmt.Println("错误：删除请求，扫描引用文件实体数和大小时失败，错误信息：", err.Error())
				valid = 2 // 数据库记录格式错误
				goto RM_VERIFY
			}

			// 更新用户实用的云盘大小
			u.used -= int64(tempSize)

			if ref == 1 {
				// 文件实体引用数为 1，可删除
				_, err = db.Exec(
					fmt.Sprintf(`delete from cfile where uid=%d`, cid))
				if err != nil {
					fmt.Println("错误：删除文件实体时出错，错误信息：", err.Error())
					valid = 4 // 数据库操作错误
					goto RM_VERIFY
				}
			} else {
				// 文件实体仍然需要被引用
				_, err = db.Exec(fmt.Sprintf(`update cfile set ref=%d where 
					uid=%d`, ref-1, cid))
				if err != nil {
					valid = 4 // 数据库操作错误
					goto RM_VERIFY
				}
			}
		}
	}

	db.Exec(fmt.Sprintf(`update cuser set used=%d where uid=%d`,
		u.used, u.id)) // 更新用户使用云盘容量
RM_VERIFY:
	if valid != -1 {
		// 删除操作失败返回错误码
		u.listen.SendBytes(auth.Int64ToBytes(int64(valid)))
		fmt.Println("用户删除操作执行失败，错误码：", valid)
	} else {
		// 成功返回 200 状态码
		u.listen.SendBytes(auth.Int64ToBytes(int64(200)))
	}
}

// -----------------------------------------------------------------------------
// fork：用户资源 Fork 请求处理函数
func (u *cuser) fork(db *sql.DB, command string) {
	// 指令格式：Fork<SEP>待fork文件uid<SEP>文件提取码<SEP>待fork到的路径
	var uid, recordCount, ref int
	var isdir_int int = 0
	var valid int = -1
	var err error
	var originPath, queryString string
	var subpaths []path_name
	var queryRow *sql.Row
	var queryRows *sql.Rows
	var tempSize int = 0
	var record ufile_record
	var recordList []ufile_record

	// 验证命令格式是否合法
	args := generateArgs(command, 4)
	if args == nil {
		valid = 0
		goto FORK_VERIFY
	}
	uid, err = strconv.Atoi(args[1])
	if err != nil || !isPathFormatValid(args[3]) ||
		strings.ToUpper(args[0]) != "FORK" {
		valid = 0
		goto FORK_VERIFY
	}

	// 从数据库检索待 Fork 文件的状态信息
	queryRow = db.QueryRow(fmt.Sprintf(`select * from ufile where uid=%d`, uid))
	if queryRow == nil {
		valid = 1 // 待 Fork 的文件记录不存在
		fmt.Println("错误：fork请求，待 Fork 的文件记录不存在")
		goto FORK_VERIFY
	}
	err = queryRow.Scan(&record.uid, &record.ownerid, &record.cfileid,
		&record.path, &record.perlink, &record.created, &record.shared,
		&record.downloaded, &record.filename, &record.private,
		&record.linkpass, &record.isdir, &record.description)
	if err != nil {
		fmt.Println("错误：fork请求，扫描待fork文件信息失败，错误信息：", err.Error())
		valid = 2 // 数据库记录格式错误
		goto FORK_VERIFY
	}

	// 资源私有 或 资源共享但提取码不正确 或用户为资源所有人
	if record.private ||
		!record.private && record.linkpass != args[2] && record.linkpass != "" ||
		int64(record.ownerid) == u.id {
		fmt.Println("错误：用户无法 Fork，资源私有 或 提取码不正确 或 用户已拥有资源")
		valid = 3 // 用户不具有 Fork 资格
		goto FORK_VERIFY
	}

	// 检查要 Fork 到的路径的子路径是否均已被创建
	subpaths = generateSubpaths(args[3])
	for _, subpath := range subpaths {
		queryRow = db.QueryRow(fmt.Sprintf(`select count(*) from ufile 
			where ownerid=%d and filename='%s' and path='%s' and isdir=1`,
			u.id, subpath.u_name, subpath.u_path))
		if queryRow == nil {
			valid = 5 // 数据库查询出错
			goto FORK_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println(err.Error())
			valid = 2 // 数据库记录格式错误
			goto FORK_VERIFY
		}

		// 用户试图 Fork 到的目录不存在
		if recordCount <= 0 {
			_, err = db.Exec(fmt.Sprintf(`insert into ufile values(null, %d, 
				-1, '%s', '', '%s', 0, 0, '%s', 1, '', 1, '')`,
				u.id, subpath.u_path, time.Now().Format("2006-01-02 15:04:05"),
				subpath.u_name))
			if err != nil {
				fmt.Println("错误：fork请求，数据库写入失败，错误信息：", err.Error())
				valid = 4 // 数据库写入失败
			}
		}
	}

	// 判断用户待 Fork 的资源为文件还是目录
	if record.isdir {
		isdir_int = 1
	}
	originPath = record.path

	// 插入 Fork 根目录/文件的记录
	_, err = db.Exec(fmt.Sprintf(`insert into ufile values(null, %d, %d, '%s',
		 '', '%s', 0, 0, '%s', 1, '', %d, '')`, u.id, record.cfileid, args[3],
		time.Now().Format("2006-01-02 15:04:05"), record.filename, isdir_int))
	if err != nil {
		fmt.Println("错误：fork请求，数据库写入操作失败，错误信息：", err.Error())
		valid = 4 // 数据库写入失败
		goto FORK_VERIFY
	}

	// 更新原始资源的分享数
	_, err = db.Exec(fmt.Sprintf(`update ufile set shared=%d where uid=%d`,
		record.shared+1, record.uid))
	if err != nil {
		fmt.Println("错误：fork请求，更新原始资源分享数失败，错误信息：", err.Error())
		valid = 4 // 数据库写入失败
		goto FORK_VERIFY
	}

	// 更新原始资源引用的实体文件引用数
	if !record.isdir && record.cfileid > 0 {
		queryRow = db.QueryRow(fmt.Sprintf(`select ref, size from 
			cfile where uid=%d`, record.cfileid))
		if queryRow == nil {
			fmt.Println("错误：fork请求，实体文件记录不存在")
			valid = 1 // 数据库记录不存在
			goto FORK_VERIFY
		}
		err = queryRow.Scan(&ref, &tempSize)
		if err != nil {
			fmt.Println("错误：fork请求，扫描实体文件引用数和大小时出错，错误信息：", err.Error())
			valid = 2 // 数据库记录格式不合法
			goto FORK_VERIFY
		}

		// 更新用户已使用的云盘容量
		u.used += int64(tempSize)

		// 更新实体文件引用数
		_, err = db.Exec(fmt.Sprintf(`update cfile set ref=%d where uid=%d`,
			ref+1, record.cfileid))
		if err != nil {
			fmt.Println("错误：fork请求，更新实体文件应用数出错，错误信息：", err.Error())
			valid = 4 // 数据库写入操作失败
			goto FORK_VERIFY
		}
	}

	if record.isdir {
		// 用户试图 Fork 一个目录，需递归 Fork 目录下的所有子目录
		queryRow = db.QueryRow(fmt.Sprintf(`select count (*) from ufile where 
			path like '%s%%' and ownerid=%d`, record.path+record.filename+"/",
			record.ownerid))
		if queryRow == nil {
			valid = 5 // 数据库搜索失败
			goto FORK_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println("错误：fork请求，获取待Fork资源数量失败，错误信息：", err.Error())
			valid = 2 // 数据库记录格式错误
			goto FORK_VERIFY
		}

		// 获取根目录下的所有待 Fork 资源
		queryString = fmt.Sprintf(`select * from ufile where path like '%s%%' 
			and ownerid=%d`, record.path+record.filename+"/", record.ownerid)
		fmt.Println(queryString)
		queryRows, err = db.Query(queryString)
		defer queryRows.Close()
		if err != nil {
			fmt.Println("错误：fork请求，查询待 Fork 资源信息失败，错误信息：", err.Error())
			valid = 5 // 数据库搜索失败
			goto FORK_VERIFY
		}

		// 生成待 Fork 子资源列表
		recordList = make([]ufile_record, 0, recordCount)
		for queryRows.Next() {
			err = queryRow.Scan(&record.uid, &record.ownerid, &record.cfileid,
				&record.path, &record.perlink, &record.created, &record.shared,
				&record.downloaded, &record.filename, &record.private,
				&record.linkpass, &record.isdir, &record.description)
			if err != nil {
				fmt.Println("错误：fork请求，扫描待 Fork 资源信息失败，错误信息：", err.Error())
				valid = 2 // 数据库记录格式错误
				goto FORK_VERIFY
			}
			recordList = append(recordList, record)
		}

		// 插入每个待 Fork 资源的副本
		for _, record = range recordList {
			if record.isdir {
				isdir_int = 1
			} else {
				isdir_int = 0
			}
			_, err = db.Exec(fmt.Sprintf(`insert into ufile values(null, %d,
			 	%d, '%s', '', '%s', 0, 0, '%s', 1, '', %d, '')`, u.id,
				record.cfileid, args[2]+record.path[len(originPath):],
				time.Now().Format("2006-01-02 15:04:05"),
				record.filename, isdir_int))
			if err != nil {
				fmt.Println("错误：fork请求，数据库插入记录失败，错误信息：", err.Error())
				valid = 4 // 数据库写操作失败
				goto FORK_VERIFY
			}

			// 更新原始资源文件的分享数
			_, err = db.Exec(fmt.Sprintf(`update ufile set shared=%d where 
				uid=%d`, record.shared+1, record.uid))
			if err != nil {
				valid = 4 // 数据库写入操作失败
				goto FORK_VERIFY
			}

			// 更新被引用实体文件的引用数
			if record.cfileid >= 0 && !record.isdir {
				queryRow = db.QueryRow(fmt.Sprintf(`select ref, size from 
					cfile where uid=%d`, record.cfileid))
				if queryRow == nil {
					valid = 1 // 数据库记录不存在
					goto FORK_VERIFY
				}
				err = queryRow.Scan(&ref, &tempSize)
				if err != nil {
					valid = 2 // 数据库记录格式错误
					goto FORK_VERIFY
				}

				// 更新用户已使用的云盘容量
				u.used += int64(tempSize)
				_, err = db.Exec(fmt.Sprintf(`update cfile set ref=%d where 
					uid=%d`, ref+1, record.cfileid))
				if err != nil {
					valid = 4 // 数据库写入失败
					goto FORK_VERIFY
				}
			}
		}
	}

	db.Exec(fmt.Sprintf(`update cuser set used=%d where uid=%d`,
		u.used, u.id)) // 更新用户使用云盘容量
FORK_VERIFY:
	if valid != -1 {
		// Fork 失败时返回错误码
		u.listen.SendBytes(auth.Int64ToBytes(int64(valid)))
	} else {
		// 成功时返回 200 状态码
		u.listen.SendBytes(auth.Int64ToBytes(int64(200)))
	}
}

// -----------------------------------------------------------------------------
// cp：用户资源复制请求处理函数
func (u *cuser) cp(db *sql.DB, command string) {
	//指令格式：CP<SEP>待复制资源uid<SEP>复制到的新路径
	var valid, isdir, uprivate bool = true, false, true
	var uid, recordCount, isdir_int, ref int
	var err error
	var path, parentPath, originName, queryString string
	var uownerid, cfileid, ushared, udownloaded int
	var upath, uperlink, ufilename, ulinkpass, ucreated, udescription string
	var queryRow *sql.Row
	var queryRows *sql.Rows
	var recordList []id_path
	var record id_path
	var subpaths []path_name

	// 判断指令格式是否合法
	args := generateArgs(command, 3)
	if args == nil {
		valid = false
		goto CP_VERIFY
	}
	uid, err = strconv.Atoi(args[1])
	if err != nil || !isPathFormatValid(args[2]) ||
		strings.ToUpper(args[0]) != "CP" {
		valid = false
		goto CP_VERIFY
	}

	// 检索待复制的原始文件
	queryRow = db.QueryRow(fmt.Sprintf(`select * from ufile where uid=%d`, uid))
	if queryRow == nil {
		valid = false
		goto CP_VERIFY
	}
	err = queryRow.Scan(&uid, &uownerid, &cfileid, &parentPath, &uperlink,
		&ucreated, &ushared, &udownloaded, &originName,
		&uprivate, &ulinkpass, &isdir, &udescription)
	if err != nil || int64(uownerid) != u.id {
		valid = false
		goto CP_VERIFY
	}

	// 检查是否要拷贝到的路径的左右子路径均已创建
	subpaths = generateSubpaths(args[2])
	for _, subpath := range subpaths {
		queryRow = db.QueryRow(fmt.Sprintf(`select count(*) from ufile where 
			ownerid=%d and filename='%s' and path='%s' and isdir=1`,
			u.id, subpath.u_name, subpath.u_path))
		if queryRow == nil {
			valid = false
			goto CP_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println("错误：拷贝请求，扫描子路径时出错，错误信息：", err.Error())
			valid = false
			goto CP_VERIFY
		}

		// 存在子路径未创建则加入该路径
		if recordCount <= 0 {
			_, err = db.Exec(fmt.Sprintf(`insert into ufile values(null, %d, 
				-1, '%s', '', '%s', 0, 0, '%s', 1, '', 1, '')`, u.id,
				subpath.u_path, time.Now().Format("2006-01-02 15:04:05"),
				subpath.u_name))
			if err != nil {
				fmt.Println("错误：拷贝请求，插入数据记录出错，错误信息：", err.Error())
				valid = false
			}
		}
	}

	// 判断待复制的资源是否为目录
	if isdir {
		isdir_int = 1
	} else {
		isdir_int = 0
	}

	// 待复制资源为单个文件
	if !isdir && cfileid >= 0 {
		queryRow = db.QueryRow(fmt.Sprintf(`select ref from cfile where 
			uid=%d`, cfileid))
		if queryRow == nil {
			valid = false
			fmt.Println("错误：拷贝请求，查询引用值为空")
			goto CP_VERIFY
		}
		err = queryRow.Scan(&ref)
		if err != nil {
			valid = false
			fmt.Println("错误：拷贝请求，扫描引用值失败，错误信息：", err.Error())
			goto CP_VERIFY
		}

		// 更新引用实体的引用数
		_, err = db.Exec(fmt.Sprintf(`update cfile set ref=%d where 
			uid=%d`, ref+1, cfileid))
		if err != nil {
			valid = false
			fmt.Println("错误：拷贝请求，更新引用值失败，错误信息：", err.Error())
			goto CP_VERIFY
		}
	}

	// 无论待拷贝的为目录/文件，均需将根目录/文件拷贝到新路径
	_, err = db.Exec(fmt.Sprintf(`insert into ufile values(null, %d, %d, '%s',
		 '', '%s', 0, 0, '%s', 1, '', %d, '')`, u.id, cfileid, args[2],
		time.Now().Format("2006-01-02 15:04:05"), originName, isdir_int))
	if err != nil {
		fmt.Println("错误：拷贝请求，根目录拷贝失败，错误信息：", err.Error())
		valid = false
		goto CP_VERIFY
	}

	// 待拷贝的资源为目录
	if isdir {
		// 待拷贝的目录下的所有子资源需要被递归拷贝
		queryRow = db.QueryRow(fmt.Sprintf(`select count (*) from ufile where 
			path like '%s%%' and ownerid=%d`, parentPath+originName+"/", u.id))
		if queryRow == nil {
			valid = false
			goto CP_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println("错误：拷贝请求，扫描记录数量出错，错误信息：", err.Error())
			valid = false
			goto CP_VERIFY
		}

		// 得到所有子资源列表
		queryString = fmt.Sprintf(`select uid, path from ufile where path 
			like '%s%%' and ownerid=%d`, parentPath+originName+"/", u.id)
		queryRows, err = db.Query(queryString)
		if err != nil {
			fmt.Println("错误：拷贝请求，查询目录下资源出错，错误信息：", err.Error())
			valid = false
			goto CP_VERIFY
		}
		defer queryRows.Close()

		// 生成待拷贝资源列表
		recordList = make([]id_path, 0, recordCount)
		for queryRows.Next() {
			err = queryRows.Scan(&uid, &path)
			if err != nil {
				fmt.Println("错误：拷贝请求，扫描目录id和路径，错误信息：", err.Error())
				valid = false
				goto CP_VERIFY
			}
			record.u_id = uid
			record.u_path = path
			recordList = append(recordList, record)
		}

		// 逐条插入拷贝记录
		for _, record = range recordList {
			queryRow = db.QueryRow(fmt.Sprintf(`select * from ufile where 
				uid=%d and ownerid=%d`, uid, u.id))
			if queryRow == nil {
				valid = false
				goto CP_VERIFY
			}
			err = queryRow.Scan(&uid, &uownerid, &cfileid, &upath, &uperlink,
				&ucreated, &ushared, &udownloaded, &ufilename, &uprivate,
				&ulinkpass, &isdir, &udescription)
			if err != nil {
				fmt.Println("错误：拷贝请求，扫描记录状态出错，错误信息：", err.Error())
				valid = false
				goto CP_VERIFY
			}
			if isdir {
				isdir_int = 1
			} else {
				isdir_int = 0
			}
			_, err = db.Exec(fmt.Sprintf(`insert into ufile values(null, %d, 
				%d, '%s', '', '%s', 0, 0, '%s', 1, '', %d, '')`, u.id, cfileid,
				args[2]+record.u_path[len(parentPath):],
				time.Now().Format("2006-01-02 15:04:05"), ufilename, isdir_int))
			if err != nil {
				fmt.Println("错误：拷贝请求，插入新记录出错，错误信息：", err.Error())
				valid = false
				goto CP_VERIFY
			}

			// 更新引用实体引用数
			if !isdir && cfileid >= 0 {
				queryRow = db.QueryRow(fmt.Sprintf(`select ref from cfile 
					where uid=%d`, cfileid))
				if queryRow == nil {
					valid = false
					fmt.Println("错误：拷贝请求，无法获取指定引用实体的引用数")
					goto CP_VERIFY
				}
				err = queryRow.Scan(&ref)
				if err != nil {
					valid = false
					fmt.Println("错误：拷贝请求，扫描引用数出错", err.Error())
					goto CP_VERIFY
				}
				_, err = db.Exec(fmt.Sprintf(`update cfile set ref=%d where 
					uid=%d`, ref+1, cfileid))
				if err != nil {
					valid = false
					fmt.Println("错误：拷贝请求，更新引用数出错，错误信息：", err.Error())
					goto CP_VERIFY
				}
			}
		}
	}

	db.Exec(fmt.Sprintf(`update cuser set used=%d where uid=%d`,
		u.used, u.id)) // 更新用户使用的云盘容量

CP_VERIFY:
	if !valid {
		// 拷贝请求失败返回 400 错误码
		u.listen.SendBytes(auth.Int64ToBytes(int64(400)))
	} else {
		// 拷贝请求成功返回 200 状态码
		u.listen.SendBytes(auth.Int64ToBytes(int64(200)))
	}
}

// -----------------------------------------------------------------------------
// mv：用户资源移动请求处理函数
func (u *cuser) mv(db *sql.DB, command string) {
	//指令格式: MV<SEP>待移动资源uid<SEP>新资源名<SEP>新路径
	var valid, isdir bool = true, false
	var uid, recordCount, ownerid int
	var err error
	var path, parentPath, originName, queryString string
	var queryRow *sql.Row
	var queryRows *sql.Rows
	var recordList []id_path
	var record id_path
	var subpaths []path_name

	// 验证传入命令格式是否合法
	args := generateArgs(command, 4)
	if args == nil {
		valid = false
		goto MV_VERIFY
	}
	uid, err = strconv.Atoi(args[1])
	if err != nil || !isFilenameValid(args[2]) ||
		!isPathFormatValid(args[3]) ||
		strings.ToUpper(args[0]) != "MV" {
		valid = false
		goto MV_VERIFY
	}

	// 检索待移动原始资源
	queryRow = db.QueryRow(fmt.Sprintf(`select ownerid, isdir, filename, 
		path from ufile where uid=%d`, uid))
	if queryRow == nil {
		valid = false
		goto MV_VERIFY
	}
	err = queryRow.Scan(&ownerid, &isdir, &originName, &parentPath)
	if err != nil || int64(ownerid) != u.id {
		valid = false
		goto MV_VERIFY
	}

	// 检查待移动目录的全部子路径是否均已被创建
	subpaths = generateSubpaths(args[3])
	for _, subpath := range subpaths {
		queryRow = db.QueryRow(fmt.Sprintf(`select count(*) from ufile where 
			ownerid=%d and filename='%s' and path='%s' and isdir=1`,
			u.id, subpath.u_name, subpath.u_path))
		if queryRow == nil {
			valid = false
			goto MV_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println("错误：移动请求，扫描子路径数目失败，错误信息：", err.Error())
			valid = false
			goto MV_VERIFY
		}

		// 存在子路径尚未创建
		if recordCount <= 0 {
			_, err = db.Exec(fmt.Sprintf(`insert into ufile values(null, %d, 
				-1, '%s', '', '%s', 0, 0, '%s', 1, '', 1, '')`,
				u.id, subpath.u_path, time.Now().Format("2006-01-02 15:04:05"),
				subpath.u_name))
			if err != nil {
				fmt.Println("错误：移动请求，插入子路径失败，错误信息：", err.Error())
				valid = false
			}
		}
	}

	// 无论待移动资源为目录/文件，均需更新信息
	_, err = db.Exec(fmt.Sprintf(`update ufile set path='%s' , 
		filename='%s' where uid=%d`, args[3], args[2], uid))
	if err != nil {
		valid = false
		goto MV_VERIFY
	}

	// 待移动资源为目录，需递归更新子目录的信息
	if isdir {
		queryRow = db.QueryRow(fmt.Sprintf(`select count (*) from ufile where
			 path like '%s%%' and ownerid=%d`, parentPath+originName+"/", u.id))
		if queryRow == nil {
			valid = false
			goto MV_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			valid = false
			goto MV_VERIFY
		}
		queryString = fmt.Sprintf(`select uid, path from ufile where path like 
			'%s%%' and ownerid=%d`, parentPath+originName+"/", u.id)
		queryRows, err = db.Query(queryString)
		if err != nil {
			fmt.Println("错误：移动请求，查找子目录信息失败，错误信息：", err.Error())
			valid = false
			goto MV_VERIFY
		}
		defer queryRows.Close()

		// 生成待移动资源列表
		recordList = make([]id_path, 0, recordCount)
		for queryRows.Next() {
			err = queryRows.Scan(&uid, &path)
			if err != nil {
				valid = false
				goto MV_VERIFY
			}
			record.u_id = uid
			record.u_path = path
			recordList = append(recordList, record)
		}

		// 更新待移动资源信息
		for _, record = range recordList {
			_, err = db.Exec(fmt.Sprintf(`update ufile set path='%s' where 
				uid=%d and ownerid=%d`, args[3]+args[2]+"/"+
				record.u_path[len(parentPath)+1+len(originName):],
				record.u_id, u.id))
			if err != nil {
				valid = false
				goto MV_VERIFY
			}
		}
	}
MV_VERIFY:
	if !valid {
		// 移动请求失败返回 400 错误码
		u.listen.SendBytes(auth.Int64ToBytes(int64(400)))
	} else {
		// 移动请求成功返回 200 状态码
		u.listen.SendBytes(auth.Int64ToBytes(int64(200)))
	}
}

// -----------------------------------------------------------------------------
// touch：用户资源创建请求处理函数
func (u *cuser) touch(db *sql.DB, command string) {
	// 指令格式：TOUCH<SEP>创建文件名<SEP>创建路径<SEP>资源类型（是否为目录）
	var valid bool = true
	var execString string
	var subpaths []path_name
	var queryRow *sql.Row
	var isdir, recordCount, uid int
	var err error

	// 判断指令格式是否合法
	args := generateArgs(command, 4)
	if args == nil {
		fmt.Println("错误：创建请求，指令格式错误")
		valid = false
		goto TOUCH_VERIFY
	}
	isdir, err = strconv.Atoi(args[3])
	if err != nil || strings.ToUpper(args[0]) != "TOUCH" ||
		!isFilenameValid(args[1]) || !isPathFormatValid(args[2]) ||
		isdir != 0 && isdir != 1 {
		if err != nil {
			fmt.Println("错误：创建请求，指令转换出错，错误信息：", err.Error())
		}
		valid = false
		goto TOUCH_VERIFY
	}

	// 生成子路径并验证目标路径是否存在
	subpaths = generateSubpaths(args[2])
	for _, subpath := range subpaths {
		queryRow = db.QueryRow(fmt.Sprintf(`select count(*) from ufile where 
			ownerid=%d and filename='%s' and path='%s' and isdir=1`,
			u.id, subpath.u_name, subpath.u_path))
		if queryRow == nil {
			valid = false
			goto TOUCH_VERIFY
		}
		err = queryRow.Scan(&recordCount)
		if err != nil {
			fmt.Println("错误：创建请求，扫描子路径数目错误，错误信息：", err.Error())
			valid = false
			goto TOUCH_VERIFY
		}
		if recordCount <= 0 {
			_, err = db.Exec(fmt.Sprintf(`insert into ufile values(null, %d, 
				-1, '%s', '', '%s', 0, 0, '%s', 1, '', 1, '')`,
				u.id, subpath.u_path, time.Now().Format("2006-01-02 15:04:05"),
				subpath.u_name))
			if err != nil {
				fmt.Println("错误：创建请求，插入子路径失败，错误信息：", err.Error())
				valid = false // 数据库写入失败
			}
		}
	}

	// 插入新建资源记录
	execString = fmt.Sprintf(`insert into ufile values(null, %d, -1, '%s',
	 	'', '%s', 0, 0, '%s', 1, '', %d, '')`, u.id, args[2],
		time.Now().Format("2006-01-02 15:04:05"), args[1], isdir)
	_, err = db.Exec(execString)
	if err != nil {
		fmt.Println("错误：创建请求，插入创建资源记录失败，错误信息：", err.Error())
		valid = false
	}
	queryRow = db.QueryRow(fmt.Sprintf(`select uid from ufile where path='%s' 
		and filename='%s'`, args[2], args[1]))
	if queryRow == nil {
		fmt.Println("错误：创建请求，无法查询到创建的记录")
		valid = false
	}
	err = queryRow.Scan(&uid)
	if err != nil {
		fmt.Println("错误：创建请求，扫描创建记录uid失败，错误信息：", err.Error())
		valid = false
	}
TOUCH_VERIFY:
	if !valid {
		// 创建不成功，返回 16 字节，前 8 字节为 400 错误码，后 8 字节填充
		codeBytes := auth.Int64ToBytes(int64(400))
		uidBytes := auth.Int64ToBytes(int64(0))
		codeBytes = append(codeBytes, uidBytes...)
		u.listen.SendBytes(codeBytes)
	} else {
		// 创建成功，返回 16 字节，前 8 字节为 200 状态码，后 8 字节为新创建资源 uid
		fmt.Println("创建成功，文件uid为：", uid)
		codeBytes := auth.Int64ToBytes(int64(200))
		uidBytes := auth.Int64ToBytes(int64(uid))
		codeBytes = append(codeBytes, uidBytes...)
		u.listen.SendBytes(codeBytes)
	}
}

// -----------------------------------------------------------------------------
// ls：用户获取资源列表请求处理函数
func (u *cuser) ls(db *sql.DB, command string) {
	// 指令格式：LS<SEP>是否递归查询<SEP>查询路径<SEP>搜索参数
	var queryString string
	var returnString string = fmt.Sprintf(`UID%sPATH%sFILE%sCREATED TIME%sSIZE
		%sSHARED%sMODE`, conf.SEPERATER, conf.SEPERATER, conf.SEPERATER,
		conf.SEPERATER, conf.SEPERATER, conf.SEPERATER)
	var uid, ownerid, cfileid, shared, downloaded, cuid, csize, cref int
	var private, isdir bool
	var path, perlink, filename, linkpass, created, cmd5, ccreated string
	var err error
	var ufilelist *sql.Rows
	var recurssive int

	// 验证指令格式是否合法
	args := generateArgs(command, 0)
	valid := true
	argAll := "%"
	if args == nil || len(args) < 3 ||
		strings.ToUpper(args[0]) != "LS" ||
		!isPathFormatValid(args[2]) {
		valid = false
		goto LS_VERIFY
	}
	recurssive, err = strconv.Atoi(args[1])
	if err != nil || recurssive != 0 && recurssive != 1 {
		valid = false
		goto LS_VERIFY
	}
	for i := 3; i < len(args); i++ {
		if args[i] != "" {
			argAll += (args[i] + "%")
		}
	}

	// 调整当前用户所在的目录
	u.curpath = args[2]

	// 根据参数决定是否递归搜索
	if recurssive == 0 {
		queryString = fmt.Sprintf(`select uid, ownerid, cfileid, path, perlink, 
			created, shared, downloaded, filename, private, linkpass, isdir 
			from ufile where ownerid=%d and path='%s' and filename like '%s'`,
			u.id, u.curpath, argAll)
	} else {
		queryString = fmt.Sprintf(`select uid, ownerid, cfileid, path, perlink, 
			created, shared, downloaded, filename, private, linkpass, isdir 
			from ufile where ownerid=%d and path like '%s%%' and filename 
			like '%s'`, u.id, u.curpath, argAll)
	}
	ufilelist, err = db.Query(queryString)
	if err != nil {
		fmt.Println("错误：获取资源列表请求，错误信息：", err.Error())
		valid = false
		goto LS_VERIFY
	}

	// 将资源列表中的资源信息依次格式化为字符串
	for ufilelist.Next() {
		err = ufilelist.Scan(&uid, &ownerid, &cfileid, &path, &perlink, &created,
			&shared, &downloaded, &filename, &private, &linkpass, &isdir)
		if err != nil {
			fmt.Println("错误：获取资源列表请求，扫描资源记录失败，错误信息：", err.Error())
			valid = false
			break
		}

		// 若引用实体文件则获取实体文件大小
		if cfileid >= 0 {
			tcfile := db.QueryRow(fmt.Sprintf(`SELECT uid, md5, size, ref, 
				created FROM cfile where uid='%d'`, cfileid))
			if tcfile == nil {
				fmt.Println("警告：获取资源列表请求，实体文件记录不存在")
				continue
			}
			err = tcfile.Scan(&cuid, &cmd5, &csize, &cref, &ccreated)
			if err != nil {
				fmt.Println("警告：获取资源列表请求，扫描实体文件记录失败，错误信息：", err.Error())
				continue
			}
		} else {
			csize = 0
		}
		// 添加格式化信息
		returnString += fmt.Sprintf("\n%d%s%s%s%s%s%s%s%d%s%d%s", uid,
			conf.SEPERATER, path, conf.SEPERATER, filename, conf.SEPERATER,
			created, conf.SEPERATER, csize, conf.SEPERATER, shared, conf.SEPERATER)

		// 根据是否为目录添加类型后缀
		if isdir {
			returnString += "DIR"
		} else {
			returnString += "FILE"
		}
	}
LS_VERIFY:
	if !valid {
		// 请求失败时返回错误信息
		u.listen.SendBytes([]byte("error happens when querying files"))
		return
	}
	// 请求成功返回格式化的信息
	u.listen.SendBytes([]byte(returnString))
}
