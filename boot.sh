#!/bin/bash
set -e

# 等待数据库就绪
echo "Waiting for SQLite..."
sleep 5

# 初始化数据库迁移
if [ ! -f "migrations/alembic.ini" ]; then
    echo "Initializing database migrations..."
    flask db init
fi

# 执行数据库迁移
echo "Creating database tables..."
flask db migrate -m "Initial migration"
flask db upgrade

# 创建管理员账号(如果不存在)
echo "Creating admin account..."
flask create-admin

# 初始化测试数据（可选）
# echo "Initializing test data..."
# flask init-data

# 使用gunicorn启动应用
echo "Starting Flask application..."
exec gunicorn -b :5000 \
    --access-logfile - \
    --error-logfile - \
    --workers 4 \
    --worker-class gevent \
    --timeout 120 \
    run:app 