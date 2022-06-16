## 介绍

YuBlog 是一款功能强大且高度自由的个人博客应用。

## 常规安装

```bash
$ git clone git@github.com:yokonsan/yublog.git  # 下载项目
$ cd yublog
$ pip install -r requirements.txt  # 安装依赖
```

### 环境准备

安装`mysql`数据库，如需启用`redis`缓存，需安装`redis`。

缓存选项：
- simple: 使用本地`Python`字典缓存，非线程安全。
- redis: 使用`Redis`作为后端存储缓存值
- filesystem: 使用文件系统来存储缓存值

配置文件 [yublog/config.py](yublog/config.py)

私密环境变量配置文件 [.env](.env)


### 启动

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

### 安装Docker

使用官方提供的脚本安装：

```bash
$ curl -fsSL get.docker.com -o get-docker.sh
$ sudo sh get-docker.sh --mirror Aliyun
```

执行`$ docker info`命令查看安装是否成功。

### 安装docker-compose

`Compose`项目是 `Docker` 官方的开源项目，负责实现对 `Docker` 容器集群的快速编排。从功能上看，跟 `OpenStack` 中的 `Heat` 十分类似。由于`docker-compose`是使用 Python 编写的，可以直接使用`pip`安装：

```bash
$ pip install docker-compose
```

### 启动

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

## 配置

博客运行前需要在`config.py`中配置必须信息。YuBlog 采用`mysql`存储，`redis`做部分缓存，需配置数据库信息。linux 的mysql安装配置可参考上方部署方案。

`mysql`的配置需根据使用场景选择配置，开发场景配置`DevelopmentConfig`类中的`SQLALCHEMY_DATABASE_URI `的信息。同样的生产环境的配置在`ProductionConfig`类的`SQLALCHEMY_DATABASE_URI `信息。其中默认的`root:password`为`user：password`，`@localhost:3306/db`为`@<host>:<port>/<db-name>`。

`redis`的配置为：

```python
CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = '127.0.0.1'
CACHE_REDIS_PORT = 6379
CACHE_REDIS_DB = os.getenv('CACHE_REDIS_DB') or ''
CHCHE_REDIS_PASSWORD = os.getenv('CHCHE_REDIS_PASSWORD') or ''
```

其中私密信息建议使用环境变量的形式配置，如`CHCHE_REDIS_PASSWORD`

### 防止csrf攻击配置

```python
CSRF_ENABLED = True
SECRET_KEY = 'you-guess'
```

### 管理员初始设置

```python
# 管理员姓名
ADMIN_NAME = 'yublog'
# 管理员登录信息
ADMIN_LOGIN_NAME = 'yublog'
# 登录密码
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'password'
# 博客名
SITE_NAME = 'yublog'
# 博客标题
SITE_TITLE = 'yublog'
# 管理员简介
ADMIN_PROFILE = '克制力，执行力'
```

同样的`ADMIN_PASSWORD`配置建议使用环境变量，初始设置除了登录名和登录密码，可以直接选择默认，可以在管理页面修改。

### 站点配置

```python
# 发送邮件用户登录
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
# 客户端登录密码非正常登录密码
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_SERVER = os.getenv('MAIL_SERVER') or 'smtp.qq.com'
MAIL_PORT = os.getenv('MAIL_PORT') or '465'

ADMIN_MAIL_SUBJECT_PREFIX = 'blog'
ADMIN_MAIL_SENDER = 'admin.com'
# 接收邮件通知的邮箱
ADMIN_MAIL = os.getenv('ADMIN_MAIL')

# 站点搜索的最小字节
WHOOSHEE_MIN_STRING_LEN = 1
```

### 七牛图床配置

默认使用本地图床。如需使用七牛云存储作为图床，可将`NEED_PIC_BED`配置为`True`。

```python
# 七牛云存储配置
NEED_PIC_BED = False
QN_ACCESS_KEY = os.getenv('QN_ACCESS_KEY') or ''
QN_SECRET_KEY = os.getenv('QN_SECRET_KEY') or ''
# 七牛空间名
QN_PIC_BUCKET = 'bucket-name'
# 七牛外链域名
QN_PIC_DOMAIN = 'domain-url'
```

## 使用

### 编辑文章

后文对网站的编辑操作，只允许有管理员权限的用户操作。

`yublog`支持`markdown`语法，上传图片可使用图床进行上传并获取外链。填写说明：

![write](/image/post0/post.png)

```
分类：技术   # 限制只能写一个分类
标签：docker,nginx  # 标签不限制个数，每个标签之间使用英文的逗号隔开
链接：nginx-and-docker  # 文章的URL，自己可以随意指定，建议有些意义
日期：2018-08-18  # 年月日间需使用-连接

标题：nginx和docker  # 文章标题
```

可以选择保存草稿，待下次编辑，也可以直接发布，当然后续更改也很方便。


### 管理文章

可以对所有发布过的文章进行更新或者删除。

### 审核评论

为了防止垃圾评论污染，用户的评论一律需要自己审核通过还是删除。

### 管理链接

博客支持添加友情链接和社交链接，他们展示在不同的地方。不要搞错了：

![add-link](/image/post0/add-link.png)

### 添加专题

博客支持系列专题功能，专栏一般是一类文章的聚合，比如系列教程或者日记啥的，文章可以自行选择加密或者不加密。


### 侧栏插件

博客支持自定义的侧栏`box`插件：

如果想要保持侧栏固定顶部，需要勾选广告选项。插件支持原生的`html,css,js`语法。但要保持宽度不得超过父元素，建议不超过230px。

```html
<a href="https://www.yokonsan.com" target="_blank">
    <img src="https://yokonsan.com/static/images/baifeng.jpg" alt="yokonsan" style="width:230px;">
</a>
```

前端显示：

![box-demo](/image/post0/box-demo.png)

### 上传文件

由于是个人使用，没有对上传的文件做进一步的过滤操作。建议大家不要随意上传`.php`、`.sh`、`.py`的文件。上传的文件位于静态目录：`app/static/upload`下，可以使用`http://<server-name>/static/upload/<filename>`访问。

### 图床

默认使用本地存储图片。

![pic-bed](/image/post0/pic-bed-demo.png)

#### 七牛云

如需使用七牛图床，需要配置好七牛图床的信息。包括个人的`AccessKey/SecretKey`：

![qiniu](/image/post0/page-qiniu.png)

默认的外链域名为：

![qiniu2](/image/post0/page-qiniu2.png)

空间名是个人创建的仓库名。

![qiniu3](/image/post0/page-qiniu3.png)

七牛图床主要是为了更方便的管理上传于七牛云的图片，目前支持上传，更名，删除等操作。


## TODO

- 更加美观的页面；
- 更加人性化的管理后台；
- 优化新评论邮件通知功能；
- 七牛图床批量操作功能；
- 改进评论系统；
- 更简单的部署方式；
- other


## 最后

这是我个人使用的博客应用，开始只是用着感觉不错，后来有很多朋友说喜欢，发邮件和我说用的很麻烦，有很多疑问。
这怪我在写的时候只按自己的喜好，没有想过太多，如果可能我会一直保持对他的改进。
