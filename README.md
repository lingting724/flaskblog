# Flask Blog

一个基于 Flask 的开源博客系统，支持一键部署。

## 快速开始

### 方式一：直接拉取镜像（推荐）

```bash
# 下载 docker-compose.yml
$ curl -o docker-compose.yml https://raw.githubusercontent.com/lingting724/flaskblog/master/docker-compose.yml
$ curl -o nginx.conf https://raw.githubusercontent.com/lingting724/flaskblog/master/nginx.conf

# 启动服务
$ docker-compose up -d

# 创建管理员账号（用户名：admin，密码：123456）
$ docker-compose exec web flask create-admin --auto

# 生成测试数据（可选）
$ docker-compose exec web flask init-data
```

### 方式二：从源码构建

```bash
# 克隆项目
$ git clone https://github.com/lingting724/flaskblog.git
$ cd flaskblog

# 构建并启动
$ docker-compose up -d --build
```

## 访问

- 博客前台：http://localhost
- 管理后台：http://localhost/admin

## 默认管理员账号
- 用户名：admin
- 密码：123456
- 邮箱：2729538090@qq.com

## 维护命令

```bash
# 查看日志
$ docker-compose logs -f

# 重启服务
$ docker-compose restart

# 停止服务
$ docker-compose down

# 清理数据（慎用）
$ docker-compose down -v
```

## 数据持久化
- myblog-data：数据库文件
- myblog-uploads：上传的文件
- redis-data：Redis 数据

## 安装依赖

```bash
$ pip install -r requirements.txt
```

## 数据库迁移
```bash
$ flask db init  # 如果 migrations 目录不存在
$ flask db migrate -m "Initial migration"
$ flask db upgrade
```


## docker 启动
```bash
# 启动
$ docker-compose up -d
# 停止服务
$ docker-compose down
# 清理未使用的镜像和构建缓存
$ docker system prune -a
# 重启
$ docker-compose restart
# 查看日志
$ docker-compose logs -f
# 删除数据卷
$ docker-compose down -v
# 执行内部命令
$ docker-compose exec web flask create-admin --auto # 创建管理员
$ docker-compose exec web flask init-data # 初始化数据
# 启动
$ docker-compose exec web flask run
```


## 部署自己的博客系统
```bash
# 下载编排文件
$ curl -o docker-compose.yml https://raw.githubusercontent.com/lingting724/flaskblog/master/docker-compose.yml
$ curl -o nginx.conf https://raw.githubusercontent.com/lingting724/flaskblog/master/nginx.conf
# 启动
$ docker-compose up -d
# 停止
$ docker-compose down
```
