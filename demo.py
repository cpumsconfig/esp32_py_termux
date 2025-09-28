import socket

def main():
    host = '192.168.10.12'  # ESP32的IP地址
    port = 5555             # ESP32的端口号
    
    try:
        # 创建socket连接
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(f"已连接到 {host}:{port}")
        
        # 发送命令
        while True:
            cmd = input("请输入命令: ")
            if cmd.lower() == 'exit':
                break
            s.send(cmd.encode())
            
            # 接收响应
            response = s.recv(4096)
            print(f"服务器响应: {response.decode()}")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        s.close()
        print("连接已关闭")

if __name__ == "__main__":
    main()
