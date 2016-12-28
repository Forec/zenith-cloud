/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：云服务器的程序执行入口
*/

package main

import (
	"bufio"
	conf "cloud-storage/config"
	cloud "cloud-storage/server"
	"flag"
	"fmt"
	"os"
)

// 开放服务器的 IP 地址
var address_h = flag.String("h", conf.TEST_IP,
	"将服务器绑定到指定IP，默认为 "+conf.TEST_IP)

// 开放服务器的端口号
var port_p = flag.Int("p", conf.TEST_PORT,
	fmt.Sprintf("将服务器绑定到指定端口，默认为 %d", conf.TEST_PORT))

func main() {
	s := new(cloud.Server)
	flag.Parse()     // 解析参数
	if !s.InitDB() { // 初始化数据库
		fmt.Println("db ERROR")
	} else {
		// 启动服务器
		go s.Run(*address_h, *port_p, conf.TEST_SAFELEVEL)
		// 启动服务器消息转发协程
		go s.CheckBroadCast()
	}
	inputReader := bufio.NewReader(os.Stdin)
	for {
		input, err := inputReader.ReadString('\n')
		if err != nil {
			fmt.Println("无法获取输入\n")
			continue
		}
		// 将服务器的输入广播给全部用户
		s.BroadCastToAll(input)
	}
}
