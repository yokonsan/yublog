# YuBlog

## 介绍

功能强大的个人博客，功能齐全的管理后台，简洁大气的前端页面，集成`markdown`编辑器，优雅美观的评论栏。~~集成畅言评论~~。

使用`mysql`数据库存储博客数据，`redis`数据库做博客缓存。预览：[here](http://www.yukunweb.com)

部署方案查看：[Ubuntu+uwsgi+Nginx部署Flask应用](http://www.yukunweb.com/2017/12/ubuntu-nginx-uwsgi-flask-app/)


## 本地使用

1. 下载此项目程序，配置`mysql`和`redis`数据库；
2. 安装项目依赖：`pip install -r requirements.txt`；
3. 打开`config.py`配置文件，配置站点信息，设置需要的环境变量；
4. 创建迁移仓库：`python manage.py db init`；
5. 创建迁移脚本：`python manage.py db migrate -m "v1.0"`；
6. 更新仓库：`python manage.py db upgrade`；
7. 创建管理员信息：`python manage.py addAdmin`；
8. 运行程序：`python manage.py runserver --host 0.0.0.0`

## 其他

- 个人使用博客，计划长期更新改进；
- 欢迎`pull requests`，提供建议；
- 如果喜欢欢迎`star`和`fork`。


## ToDo

- 更加美观的页面；
- 自定义侧栏插件；
- 独立个性的评论系统；✔
- 站点音乐播放器。