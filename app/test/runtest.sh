cd ../authenticate
go test
cd ../transmit
go test
rm test_out.txt
cd ../cstruct
go test
cd ..
echo 测试完成，按任意键继续
read -n1 var