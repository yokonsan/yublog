## Mysql Dockerfile

如果有需要导入mysql容器的sql，则使用该Dockerfile制作MySQL容器

### 导入sql

将sql文件放入该目录，在将docker-compose.yml文件，db容器配置改为：

```yaml
db:
    build: ./mysql
    restart: always
    volumes:
      - ./mysql/my.cnf:/etc/mysql/my.cnf:ro
      - ./mysql/data:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=password
      # - MYSQL_DATABASE=mydb
    ports:
      - "3306:3306"
```

### 导出sql


