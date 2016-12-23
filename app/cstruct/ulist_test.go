/*
作者: Forec
最后编辑日期: 2016/12/20
邮箱：forec@bupt.edu.cn
关于此文件：服务器涉及结构列表方法测试代码
*/

package cstruct

import (
	trans "cloud-storage/transmit"
	"testing"
)

// -----------------------------------------------------------------------------
// 测试 UFile 列表元素附加
func TestAppendElements(t *testing.T) {
	testUFSlice := make([]UFile, 0, 10)
	for i := 0; i < 20; i++ {
		uf := NewUFile(NewCFile(int64(i),
			int64(i+12345)),
			nil,
			"test1",
			"../files/test")
		testUFSlice = AppendUFile(testUFSlice, uf)
	}
	if len(testUFSlice) != 20 {
		t.Errorf("错误：UList 附加单个文件失败")
	}
	testUFSlice = AppendUFile(testUFSlice, testUFSlice...)
	if len(testUFSlice) != 40 {
		t.Errorf("错误：UList 附加列表失败")
	}
}

// -----------------------------------------------------------------------------
// 测试传输列表附加
func TestAppendTransmitable(t *testing.T) {
	testTransmitableSlice := make([]trans.Transmitable, 19, 19)
	ts1 := trans.NewTransmitter(nil, 0, nil)
	ts2 := trans.NewTransmitter(nil, 0, nil)
	testTransmitableSlice = AppendTransmitable(testTransmitableSlice, ts1)
	if len(testTransmitableSlice) != 20 {
		t.Errorf("错误：未满时附加连接后，连接线程池数量应为 20，实际为 %d",
			len(testTransmitableSlice))
	}
	testTransmitableSlice = AppendTransmitable(testTransmitableSlice, ts2)
	if len(testTransmitableSlice) != 20 {
		t.Errorf("错误：满时附加连接后，线程池数量应为 20，实际为 %d",
			len(testTransmitableSlice))
	}
}

// -----------------------------------------------------------------------------
// 测试 UFile 列表附加
func TestUFileIndexById(t *testing.T) {
	testUFSlice := make([]UFile, 0, 10)
	f := NewCFile(int64(0), int64(12345))
	for i := 0; i < 20; i++ {
		uf := NewUFile(f, nil, "test1", "../files/test")
		testUFSlice = AppendUFile(testUFSlice, uf)
	}
	testIndexSlice := UFileIndexById(testUFSlice, int64(0))
	if testIndexSlice == nil || len(testIndexSlice) != 20 {
		t.Errorf("错误：UFile 列表附加失败，应为20，实际为 %d", len(testIndexSlice))
	}
}
