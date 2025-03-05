#!/bin/sh

# 确保目录存在并有正确的权限
mkdir -p /myblog/instance
chown -R www-data:www-data /myblog/instance
chmod 755 /myblog/instance

# 等待数据库就绪
echo "Initializing database..."

# 初始化数据库
flask db init || true  # 如果已经初始化则跳过
flask db migrate -m "Initial migration" || true
flask db upgrade

# 自动创建管理员账号
echo "Creating admin account..."
flask create-admin --auto

# 生成测试数据（可选）
echo "Generating test data..."
flask init-data

# 启动应用
echo "Starting Flask application..."
python run.py 