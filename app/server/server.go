/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：服务器 Server 结构的定义与实现
*/

package server

import (
	auth "cloud-storage/authenticate"
	conf "cloud-storage/config"
	cs "cloud-storage/cstruct"
	trans "cloud-storage/transmit"
	"database/sql" // SQL接口
	"fmt"
	_ "github.com/mattn/go-sqlite3" // 第三方 SQLITE 库
	"net"
	"strings"
	"time"
)

type Server struct {
	listener      net.Listener // 请求监听线程
	loginUserList []cs.User    // 已登陆用户列表
	db            *sql.DB      // 数据库句柄
}

// InitDB: 程序执行开始时初始化数据库
func (s *Server) InitDB() bool {
	var err error
	s.db, err = sql.Open(conf.DATABASE_TYPE, conf.DATABASE_PATH)
	if err != nil {
		return false
	}
	// 创建用户表
	s.db.Exec(`create table cuser (uid INTEGER PRIMARY KEY AUTOINCREMENT,
		email VARCHAR(64), password_hash VARCHAR(32), created DATE, confirmed BOOLEAN,
		nickname VARCHAR(64), avatar_hash VARCHAR(32), about_me VARCHAR(256),
		last_seen DATE, member_since DATE, score INTEGER, role_id INTEGER,
		used INTEGER, maxm INTEGER)`)

	// 创建用户资源记录表
	s.db.Exec(`create table ufile (uid INTEGER PRIMARY KEY AUTOINCREMENT, 
		ownerid INTEGER, cfileid INTEGER, path VARCHAR(256), perlink VARCHAR(128), 
		created DATE, shared INTEGER, downloaded INTEGER, filename VARCHAR(128),
		private BOOLEAN, linkpass VARCHAR(4), isdir BOOLEAN, description VARCHAR(256))`)

	// 创建实体文件记录表
	s.db.Exec(`create table cfile (uid INTEGER PRIMARY KEY AUTOINCREMENT,
		md5 VARCHAR(32), size INTEGER, ref INTEGER, created DATE)`)

	// 创建用户消息表
	s.db.Exec(`create table cmessages (mesid INTEGER PRIMARY KEY AUTOINCREMENT,
		targetid INTEGER, sendid INTEGER, message VARCHAR(512), created DATE, 
		sended Boolean, viewed Boolean, send_delete Boolean, recv_delete Boolean)`)

	// 创建用户操作记录表
	s.db.Exec(`create table coperations (oprid INTEGER PRIMARY KEY AUTOINCREMENT,
		deletedUFileId INTEGER, deletedUFileName VARCHAR(128), 
		deletedUFilePath VARCHAR(256), relatedCFileId INTEGER, time DATE)`)

	return true
}

// CheckLive：保活协程，定时检查用户是否下线
// CHECK_LIVE_SEPERATE 控制检查间隔，单位为秒
func (s *Server) CheckLive() {
	chRate := time.Tick(conf.CHECK_LIVE_SEPERATE * time.Second)
	for {
		<-chRate
		for _, u := range s.loginUserList {
			// 为每个已登陆用户启动一个协程，检查是否仍存在连接
			go func(usr cs.User) {
				if !s.BroadCast(usr, conf.CHECK_LIVE_TAG) {
					usr.Logout()
				}
			}(u)
		}
	}
}

// CheckBoardCast：消息转发协程，定时检查是否存在用户间消息交互
// CHECK_MESSAGE_SEPERATE 控制检查间隔，单位为秒
func (s *Server) CheckBroadCast() {
	chRate := time.Tick(conf.CHECK_MESSAGE_SEPERATE * time.Second)
	var queryRows *sql.Rows
	var queryRow *sql.Row
	var mesid, uid, messageCount int
	var message, created string
	var err error
	for {
		<-chRate
		for _, u := range s.loginUserList {
			// 从数据库抽取当前某个已登录用户作为接收者的尚未发送的消息数量
			queryRow = s.db.QueryRow(fmt.Sprintf(`select count (*) from cmessages where
				targetid=%d and sended=0`, u.GetId()))
			if queryRow == nil {
				continue
			}
			err = queryRow.Scan(&messageCount)
			if err != nil {
				continue
			}
			id_list := make([]int, 0, messageCount)
			// 检索数据库查找当前某个已登录用户作为接收者的尚未发送的消息
			queryRows, err = s.db.Query(fmt.Sprintf(`select mesid, sendid, message, created
				 from cmessages where targetid=%d and sended=0 and recv_delete=0`, u.GetId()))
			if err != nil {
				fmt.Println("错误：无法检索到相关消息，错误信息为：", err.Error())
				continue
			}
			for queryRows.Next() {
				// 通过监听线程发送每条尚未发送的消息
				err = queryRows.Scan(&mesid, &uid, &message, &created)
				if err != nil {
					fmt.Println("错误：扫描消息信息失败，错误信息为：", err.Error())
					break
				}
				if s.BroadCast(u, fmt.Sprintf("%d%s%s%s%s", uid, conf.SEPERATER, message,
					conf.SEPERATER, created)) {
					id_list = append(id_list, mesid)
				} else {
					break
				}
			}
			for _, id := range id_list {
				// 更新数据库中发送成功的消息的发送位
				_, err = s.db.Exec(fmt.Sprintf(`update cmessages set sended=1 where mesid=%d`, id))
				if err != nil {
					fmt.Println("错误：更新消息状态失败，错误信息为：", err.Error())
					continue
				}
			}
		}
	}
}

// BroadCastToAll：广播，向所有在线用户投放消息
func (s *Server) BroadCastToAll(message string) {
	for _, u := range s.loginUserList {
		s.BroadCast(u, message)
	}
}

// BroadCast：单播，向指定用户投放消息
func (s *Server) BroadCast(u cs.User, message string) bool {
	if u.GetInfos() == nil {
		return false
	}
	return u.GetInfos().SendBytes([]byte(message))
}

// AddUser：向在线列表添加用户
func (s *Server) AddUser(u cs.User) {
	s.loginUserList = cs.AppendUser(s.loginUserList, u)
}

// RemoveUser：从在线列表移除用户
func (s *Server) RemoveUser(u cs.User) bool {
	for i, uc := range s.loginUserList {
		if uc == u {
			s.loginUserList = append(s.loginUserList[:i], s.loginUserList[i+1:]...)
			return true
		}
	}
	return false
}

// Login：接受一个 transmitter 并校验该连接登录信息是否合法
func (s *Server) Login(t trans.Transmitable) (cs.User, int) {
	// mode : failed=-1, new=0, transmission=1
	chRate := time.Tick(1e3)
	var recvL int64 = 0
	var err error
	recvL, err = t.RecvUntil(int64(24), recvL, chRate)
	if err != nil {
		fmt.Println("用户登录过程异常，错误原因：", err.Error())
		return nil, -1
	}
	// 前 8 字节为明文总长度，中间 8 字节为密文总长度， 后 8 字节为明文用户名长度
	srcLength := auth.BytesToInt64(t.GetBuf()[:8])
	encLength := auth.BytesToInt64(t.GetBuf()[8:16])
	nmLength := auth.BytesToInt64(t.GetBuf()[16:24])
	recvL, err = t.RecvUntil(encLength, recvL, chRate)
	if err != nil {
		fmt.Println("2 error:", err.Error())
		return nil, -1
	}

	// 解析用户名和密码
	var nameApass []byte
	nameApass, err = auth.AesDecode(t.GetBuf()[24:24+encLength], srcLength, t.GetBlock())
	if err != nil {
		fmt.Println("decode error:", err.Error())
		return nil, -1
	}
	fmt.Println("新登录的用户名：", string(nameApass[:nmLength]))
	fmt.Println("此用户传输的密文部分：", string(nameApass[nmLength:]))

	username := string(nameApass[:nmLength])
	pc := cs.UserIndexByName(s.loginUserList, string(nameApass[:nmLength]))

	// 该连接由已登陆用户建立
	if pc != nil {
		fmt.Println("该用户已登陆，用户名为: ", pc.GetUsername())

		if strings.ToUpper(string(nameApass[nmLength:])) == pc.GetPassHash() {
			// 若新登录用户的密码部分为用户的密钥哈希值，则认为该连接为登录连接
			// 需提醒原用户异地登陆并登出原用户、登录新用户
			s.BroadCast(pc, "您的账号在另一台机器上登录，如果不是您本人所为，请尽快修改密码！")
			pc.Logout()
		} else if pc.GetToken() != string(nameApass[nmLength:]) {
			// 此连接为传输线程，但验证的 token 不符
			fmt.Println("无法通过 token 验证，远程主机不合法")
			return nil, -1
		} else {
			if pc.GetInfos() == nil {
				// 若当前用户尚未有被动监听线程，则将此连接作为被动监听线程
				pc.SetInfos(t)
				return pc, 2 // 模式 2 代表被动监听线程
			} else {
				// 否则作为长数据流传输线程
				return pc, 1 // 模式 1 代表长数据流传输线程
			}
		}
	}

	// 该连接来自新用户
	row := s.db.QueryRow(fmt.Sprintf("SELECT uid, password_hash FROM cuser where email='%s'", username))
	if row == nil {
		fmt.Println("错误：认证请求，在数据库中无法检索到用户，错误信息为：", err.Error())
		return nil, -1
	}
	var uid int
	var spassword, avatar_hash string

	err = row.Scan(&uid, &spassword)
	if err != nil || spassword != strings.ToUpper(string(nameApass[nmLength:])) {
		if err != nil {
			fmt.Println("错误：认证请求，扫描用户uid和密码失败，错误信息为：", err.Error())
		}
		// 数据库读取错误 或 用户认证信息不正确
		return nil, -1
	}

	// 创建新用户
	rc := cs.NewCUser(string(nameApass[:nmLength]), int64(uid), "/")
	if rc == nil {
		return nil, -1
	}
	// 为新用户分配交互连接
	rc.SetListener(t)
	row = s.db.QueryRow(fmt.Sprintf("SELECT used, maxm, nickname FROM cuser where uid=%d", uid))
	if err != nil {
		fmt.Println("错误：认证请求，无法在数据库中检索到相关用户，错误信息为：", err.Error())
		return nil, -1
	}
	used := 0
	maxm := 0
	nickname := ""
	err = row.Scan(&used, &maxm, &nickname)
	if err != nil {
		fmt.Println("错误：认证请求，扫描用户记录出错，错误信息为：", err.Error())
		return nil, -1
	}

	// 检索用户头像链接，可能失败
	row = s.db.QueryRow(fmt.Sprintf("SELECT avatar_hash FROM cuser where uid=%d", uid))
	if err != nil {
		avatar_hash = ""
	} else {
		err = row.Scan(&avatar_hash)
		if err != nil {
			avatar_hash = ""
		}
	}

	// 为新用户设定各项资料
	rc.SetAvatar(avatar_hash)
	rc.SetPassHash(spassword)
	rc.SetUsed(int64(used))
	rc.SetMaxm(int64(maxm))
	rc.SetNickname(nickname)
	return rc, 0 // 模式 0 代表登录成功
}

// Communicate：服务器和远程客户端完成登录认证前后的交互函数，在整个
//  用户存活期间均保持，用户下线后函数执行结束
func (s *Server) Communicate(conn net.Conn, level uint8) {
	var err error
	s_token := auth.GenerateToken(level)
	// 向远程用户发送随机 token
	length, err := conn.Write([]byte(s_token))
	fmt.Println("向远程主机发送token：", string(s_token))
	if length != conf.TOKEN_LENGTH(level) ||
		err != nil {
		return
	}

	// 生成新的 transmitter
	mainT := trans.NewTransmitter(conn, conf.AUTHEN_BUFSIZE, s_token)
	rc, mode := s.Login(mainT)
	fmt.Println("远程主机登录模式：", mode)
	if rc == nil || mode == -1 {
		// 认证失败
		mainT.Destroy()
		return
	}
	if !mainT.SendBytes(s_token) {
		// 验证通过后向客户端回送 token 验证
		return
	}
	if mode == 0 {
		// 新登录用户
		rc.SetToken(string(s_token))
		s.AddUser(rc)
		rc.DealWithRequests(s.db)
		rc.Logout()
		s.RemoveUser(rc)
	} else if mode == 1 && mainT.SetBuflen(conf.BUFLEN) && rc.AddTransmit(mainT) {
		// 被动监听线程
		rc.DealWithTransmission(s.db, mainT)
	} else if mode != 2 {
		// 认证失败
		mainT.Destroy()
		fmt.Println("远程主机认证失败")
	}
}

// Run：服务器运行函数，监听接入的 Socket 连接
func (s *Server) Run(ip string, port int, level int) {
	var err error
	if !trans.IsIpValid(ip) || !trans.IsPortValid(port) {
		return
	}

	// 在指定IP 和端口开放服务器
	s.listener, err = net.Listen("tcp", fmt.Sprintf("%s:%d", ip, port))
	if err != nil {
		fmt.Println("服务器启动失败，即将宕机")
		return
	}
	defer s.listener.Close()
	s.loginUserList = make([]cs.User, 0, conf.START_USER_LIST)
	for {
		sconn, err := s.listener.Accept()
		if err != nil {
			fmt.Println("错误：接受请求失败，错误信息为：", err.Error())
			continue
		}
		fmt.Println("收到请求来自 ",
			sconn.RemoteAddr().String())
		// 接入请求后启动新协程转交处理
		go s.Communicate(sconn, uint8(level))
	}
}
