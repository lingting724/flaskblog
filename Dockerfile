# 使用官方 Python 3.9 作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /myblog

# 复制 requirements.txt 并安装依赖
COPY requirements.txt /myblog/
RUN pip install -r requirements.txt

# 复制项目文件到工作目录
COPY ./ /myblog/

# 创建必要的目录并设置权限
RUN mkdir -p instance \
    && mkdir -p app/static/uploads/avatars \
    && mkdir -p app/static/uploads/posts \
    && mkdir -p migrations \
    && chown -R www-data:www-data /myblog \
    && chmod -R 755 /myblog

# 设置环境变量
ENV FLASK_APP=run.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1

# 设置启动脚本权限
COPY docker-entrypoint.sh /myblog/
RUN chmod +x /myblog/docker-entrypoint.sh

# 暴露端口
EXPOSE 5000

# 运行启动脚本
CMD ["/myblog/docker-entrypoint.sh"] 



