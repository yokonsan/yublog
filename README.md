# YuBlog

## 介绍

[使用文档](https://www.yukunweb.com/page/YuBlog-document/)

功能强大的个人博客，功能齐全的管理后台，简洁大气的前端页面。
支持`markdown`文章编辑，代码高亮以及优雅美观的评论栏。

使用`mysql`数据库存储博客数据，`redis`数据库做博客缓存。预览：[here](http://www.yukunweb.com)

部署方案查看：[Ubuntu+uwsgi+Nginx部署Flask应用](http://www.yukunweb.com/2017/12/ubuntu-nginx-uwsgi-flask-app/)

推荐Docker-Compose 部署： 
0. 推荐站点配置`https`证书，不然`Chrome`会将站点标记为不安全，不配置证书则需要将[default.conf](nginx/conf.d/default.conf)配置改为：
    ```yaml
    server {
        listen      80;
        # set your domain or ip address
        server_name example.com;
        charset     utf-8;
        client_max_body_size 75M;

        location / {
            uwsgi_pass web:9001;
            uwsgi_read_timeout 600;
            uwsgi_connect_timeout 600;
            uwsgi_send_timeout 600;
            include uwsgi_params; # the uwsgi_params file you installed
        }

    }
    ```
1. 配置`config.py`文件应用信息，敏感信息建议在`.env`文件中配置，
2. 启动`docker-compose up -d`
3. 停止`docker-compose down`

## 本地使用

默认不使用七牛图床功能，如想使用，需要在`config.py`配置对应信息，并将`NEED_PIC_BED`改为`True`。

0. 下载此项目程序，配置`mysql`和`redis`数据库；
1. 进入应用文件夹：`cd source`
2. 安装项目依赖：`pip install -r requirements.txt`；
3. 打开`config.py`配置文件，配置站点信息，设置需要的环境变量；
4. 创建迁移仓库：`python manage.py db init`；
5. 创建迁移脚本：`python manage.py db migrate -m "v1.0"`；
6. 更新仓库：`python manage.py db upgrade`；
7. 创建管理员信息：`python manage.py add_admin`；
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
- 更方便的七牛云图床管理; ✔
- 优化邮件功能；✔
- 完善测试程序；
- 添加详细文档；
- 更加简单的管理界面；

## 更新

1. 集成[editor.md](https://github.com/pandao/editor.md)编辑器，所见即所得。提交日志：[f33c33](https://github.com/Blackyukun/YuBlog/tree/f33c33bdbe192c1f4749cb736e9fe161dcaa19ca) 下载即用
2. 弃用`editor.md`编辑器，使用`markdown`库支持编写文章。
3. 加入系列文章功能，记录某一主题系列文章。
4. 添加侧栏插件功能，可添加广告插件和普通插件，需要自己编写前端样式。
5. 使用轻量[simplemde-markdown-editor](https://github.com/sparksuite/simplemde-markdown-editor)编辑器，在线编辑文章更加优雅。
6. 集成七牛官方sdk，编辑简洁美观的七牛图床，上传以及操作图片更加方便。
7. 添加`Docker`一键部署.。
8. 添加获取`letsencrypt`提供免费`http`证书的脚本。


## Enjoy it.
