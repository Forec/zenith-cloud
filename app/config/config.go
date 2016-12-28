/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：服务器和测试用客户端的全局配置文件
*/

package config

// 用户根路径
const USER_FOLDER = "/home/cloud/store/"

// 服务器上的文件实体存储路径
const STORE_PATH = "G:\\Cloud\\"

// 测试客户端的文件下载路径
const DOWNLOAD_PATH = "G:\\Cloud\\"

// 测试客户端系统
const CLIENT_VERSION = "Windows"

// 非长数据流传输连接缓冲区大小
const AUTHEN_BUFSIZE = 1024

// 长数据流传输连接缓冲区大小
const BUFLEN = 4096 * 1024

// 每用户最大同时活动连接数
const MAXTRANSMITTER = 20

// 服务器系统使用数据库类型
const DATABASE_TYPE = "sqlite3"

// 服务器系统使用数据库路径
const DATABASE_PATH = "F:\\Develop\\Python\\zenith-cloud\\web\\work.db"

// 服务器系统初始化用户池大小
const START_USER_LIST = 10

// 测试用用户名
const TEST_USERNAME = "forec@bupt.edu.cn"

// 测试用用户密码
const TEST_PASSWORD = "TESTTHISPASSWORD"

// 测试用用户安全等级
const TEST_SAFELEVEL = 3

// 测试用IP地址
const TEST_IP = "10.201.14.176" //"127.0.0.1"

// 测试用端口
const TEST_PORT = 10087

// 标准消息分隔符
const SEPERATER = "+"

// 消息传递间隔
const CHECK_MESSAGE_SEPERATE = 5

// 根据安全级别计算使用的 token 长度（字节）
func TOKEN_LENGTH(level uint8) int {
	if level <= 1 {
		return 16
	} else if level == 2 {
		return 24
	} else {
		return 32
	}
}
