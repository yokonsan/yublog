## Let's Encrypt配置https

推荐站点配置`https`证书，不然`Chrome`会将站点标记为不安全。开始前先在[get_cert.sh](get_cert.sh)和[renew_cert.sh](renew_cert.sh)文件中配置邮箱和域名：

```
DOMAIN=example.com
DOMAIN2=www.example.com
EMAIL=example@email.com
```

### 启动容器前第一次获取证书

```
$ chmod +x get_cert.sh renew_cert.sh
$ bash get_cert.sh
```

### 配置自动更新证书

Let's Encrypt 证书的有效时间时三个月，我们需要配置定时任务，自动更新证书，Ubuntu下：

查看`cron`服务是否运行：`pgrep cron`

```bash
/usr/sbin/service crond start  # 启动服务 
/usr/sbin/service crond stop  # 关闭服务 
/usr/sbin/service crond restart  # 重启服务 
/usr/sbin/service crond reload  # 重新载入配置
```

配置任务`crontab -e`：

```bash
0 0 1 * * /home/kyu/YuBlog/certbot/renew_cert.sh /home/kyu/YuBlog &
0 1 1 * * docker exec yublog_proxy nginx -s reload &
```

意思是每个月的1号，更新 https 证书，并且在一分钟后，重启 nginx 服务。

