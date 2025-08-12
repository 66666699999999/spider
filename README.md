# Spider
## 简介
使用FastApi提供接口实现定向url截图推特评论
## 环境
Python3.11
## 运行
启动app文件夹的main，fastapi运行，运行根目录的test文件对twitter截图
```python
# 安装依赖
pip install -r requirements.txt
# 根目录启动程序
python -m app.main

# 访问截图接口填入url
http://127.0.0.1:8000/screenshot?url=https://x.com/__Inty__/status/1954974623302643887
```
