import socket
import base64

def main():
    while True:
        command = input(">")
        # 检查输入是否为空
        if not command.strip():
            continue  # 如果输入为空，跳过本次循环，不执行任何操作
        if command == "exit":
            s.send(command.encode())  # 发送退出命令
            x = s.recv(1024)
            print(x.decode())  # 显示退出反馈信息
            input("请按回车以继续")  # 提示用户按回车
            s.close()  # 关闭连接
            break
        else:
            s.send(command.encode())  # 发送命令
            x = s.recv(1024)  # 接收命令执行结果
            # 确保在显示结果前等待服务器完全发送数据
            if x:
                print(x.decode())  # 显示命令结果


def verify_2():
    s.send("passwd1024".encode())  # 发送密码验证请求
    passwd = s.recv(1024)
    passwd = passwd.decode()  # 解码从服务器接收到的密码
    passwd_input = input("请输入密码:")  # 获取用户输入的密码
    # 直接比较密码，不使用base64编码
    if passwd == passwd_input:
        main()
    else:
        print("密码错误")
        verify_2()


def verify():
    s.send("user1024".encode())  # 发送用户名验证请求
    user = s.recv(1024)
    user = user.decode()  # 解码从服务器接收到的用户名
    user_input = input("请输入用户名:")  # 获取用户输入的用户名
    # 直接比较用户名，不使用base64编码
    if user == user_input:
        verify_2()
    else:
        print("用户名错误，请重新输入")
        verify()


# 创建TCP连接
def connect_to_esp32():
    global s
    ESP32_IP = input("请输入ip地址:")  # 获取ESP32的IP地址
    ESP32_PORT = 5555  # ESP32的端口
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建socket对象
    s.connect((ESP32_IP, ESP32_PORT))  # 连接到ESP32

    # 接收欢迎信息
    x = s.recv(1024)  # 接收反馈
    print(x.decode())
    if x.decode() == "y":
        verify()  # 进行验证


if __name__ == "__main__":
    connect_to_esp32()  # 启动程序
