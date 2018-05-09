# YuBlog

## 介绍

功能强大的个人博客，功能齐全的管理后台，简洁大气的前端页面。
支持`markdown`文章编辑，代码高亮以及优雅美观的评论栏。

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
8. 运行程序：`python manage.py runserver --host 0.0.0.0`；
9. 管理后台：`/admin`

## 其他

- 个人使用博客，计划长期更新改进；
- 欢迎`pull requests`，提供建议；
- 如果喜欢欢迎`star`和`fork`。


## ToDo

- 更加美观的页面；
- 自定义侧栏插件；✔
- 独立个性的评论系统；✔
- 更方便的七牛云图床管理

## 更新

1. 集成[editor.md](https://github.com/pandao/editor.md)编辑器，所见即所得。提交日志：[f33c33](https://github.com/Blackyukun/YuBlog/tree/f33c33bdbe192c1f4749cb736e9fe161dcaa19ca) 下载即用
2. 弃用`editor.md`编辑器，使用`markdown`库支持编写文章。
3. 加入系列文章功能，记录某一主题系列文章。
4. 添加侧栏插件功能，可添加广告插件和普通插件，需要自己编写前端样式。
5. 使用轻量[simplemde-markdown-editor](https://github.com/sparksuite/simplemde-markdown-editor)编辑器，在线编辑文章更加优雅。
