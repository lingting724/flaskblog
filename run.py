from app import create_app

app = create_app()

if __name__ == '__main__':
    # host='0.0.0.0' 表示监听所有网络接口
    # port=5000 是默认端口号
    app.run(host='0.0.0.0', port=5000) 