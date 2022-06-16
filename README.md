# YuBlog

## 介绍

[使用文档](https://www.yukunweb.com/page/YuBlog-document/)

功能强大的个人博客，功能齐全的管理后台，简洁大气的前端页面。
支持`markdown`文章编辑，代码高亮以及优雅美观的评论栏。

...

## 安装

```bash
$ git clone git@github.com:yokonsan/yublog.git  # 下载项目
$ cd yublog
$ pip install -r requirements.txt  # 安装依赖
```

## 环境准备

安装`mysql`数据库，如需启用`redis`缓存，需安装`redis`。

缓存选项：
- simple: 使用本地`Python`字典缓存，非线程安全。
- redis: 使用`Redis`作为后端存储缓存值
- filesystem: 使用文件系统来存储缓存值

配置文件 [yublog/config.py](yublog/config.py)

私密环境变量配置文件 [.env](.env)


## 启动

```bash
$ flask init-db  # 初始化数据库
$ flask deploy  # 生成默认数据
$ flask run  # 启动
```

默认地址：[127.0.0.1:5000](http://127.0.0.1:5000)

管理后台地址：[127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)

账户密码：
```
账户：如未配置，默认 yublog
密码：如未配置，默认 password
```

## Docker

```bash
$ docker-compose up -d
```

默认地址：[127.0.0.1:9001](http://127.0.0.1:9001)

管理后台地址：[127.0.0.1:9001/admin](http://127.0.0.1:9001/admin)

账户密码：
```
账户：如未配置，默认 yublog
密码：如未配置，默认 password
```

**停止运行：**

```bash
$ docker-compose down
```

**查看日志：**

```bash
$ docker-compose logs  # 查看总的容器日志
$ docker-compose logs yublog_web  # 查看web应用运行日志
```

## 安装示例

[yublog-installation-example](https://github.com/yokonsan/yublog-installation-example)

## Enjoy it.
