## Mysql Dockerfile

为了能更方便控制mysql容器启动时创建web应用需要的数据库，则使用该Dockerfile制作MySQL容器

### 导入sql

将导出的sql文件内容赋值在`init_database.sql`文件内，第一次启动没有sql数据，不用管。

### 导出sql

导出主机上的数据：

```
$ mysqldump -uroot -p mydb > mydb.sql
```

导出容器里的数据：

```bash
$ docker exec yublog_db_1 sh -c 'exec mysqldump --all-databases -uroot -p"$MYSQL_ROOT_PASSWORD" > /var/lib/mysql/all-databases.sql'
```


