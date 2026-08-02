# 这里的 @body.json 表示从文件中读取内容发送
curl.exe -X POST http://127.0.0.1:8000/chat `
-H "Content-Type: application/json" `
-d "@body.json"