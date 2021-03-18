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

## Docker

```bash
$ docker-compose up
```

## Enjoy it.
