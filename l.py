import socket
import time
import os
import sys
import json

class ESP32Client:
    def __init__(self, host, port=5555):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self, timeout=15):
        """连接到ESP32服务器"""
        try:
            print(f"尝试连接到 {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)  # 设置超时时间
            self.socket.connect((self.host, self.port))
            print(f"已建立TCP连接，等待握手...")
            
            # 握手协议
            start_time = time.time()
            while time.time() - start_time < 10:  # 增加到10秒
                try:
                    # 设置较短的接收超时，以便更频繁地检查连接状态
                    self.socket.settimeout(1)
                    handshake = self.socket.recv(1024)
                    if handshake:
                        print(f"收到握手消息: {handshake.decode()}")
                        if handshake.decode() == 'y':
                            print("发送确认...")
                            self.socket.send('OK'.encode())
                            self.connected = True
                            print(f"已成功连接到ESP32服务器 {self.host}:{self.port}")
                            return True
                        else:
                            print(f"收到意外的握手信号: {handshake.decode()}")
                            return False
                except socket.timeout:
                    print("等待握手消息中...")
                    continue
                except Exception as e:
                    print(f"握手过程中出错: {str(e)}")
                    return False
            
            print("握手超时")
            return False
        except socket.timeout:
            print(f"连接超时，无法在{timeout}秒内连接到服务器")
            return False
        except ConnectionRefusedError:
            print("连接被拒绝，服务器可能未运行或防火墙阻止了连接")
            return False
        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False
    
    def test_connection(self):
        """测试连接是否可达"""
        print(f"测试到 {self.host} 的网络连接...")
        # 使用ping测试连接
        response = os.system(f"ping -n 1 -w 2000 {self.host} > nul")
        if response == 0:
            print(f"可以ping通 {self.host}")
            return True
        else:
            print(f"无法ping通 {self.host}")
            return False
    
    def test_port(self):
        """测试端口是否开放"""
        print(f"测试端口 {self.port} 是否开放...")
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(2)
            result = test_socket.connect_ex((self.host, self.port))
            test_socket.close()
            
            if result == 0:
                print(f"端口 {self.port} 是开放的")
                return True
            else:
                print(f"端口 {self.port} 不可达或被阻止")
                return False
        except Exception as e:
            print(f"测试端口时出错: {str(e)}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.connected = False
            print("已断开连接")
    
    def send_command(self, command):
        """发送命令并接收响应"""
        if not self.connected:
            print("未连接到服务器")
            return None
            
        try:
            print(f"发送命令: {command}")
            self.socket.send(command.encode())
            print("等待响应...")
            
            # 设置接收超时
            self.socket.settimeout(10)
            response = self.socket.recv(4096)
            print(f"收到响应: {response.decode()}")
            return response.decode()
        except socket.timeout:
            print("等待响应超时")
            return None
        except Exception as e:
            print(f"发送命令失败: {str(e)}")
            return None
    
    def interactive_mode(self):
        """交互模式"""
        print("进入交互模式，输入'help'查看可用命令，输入'exit'退出")
        
        while self.connected:
            try:
                command = input("> ")
                if not command:
                    continue
                    
                if command.lower() in ["exit", "quit"]:
                    self.send_command("exit")
                    break
                
                # 普通命令
                response = self.send_command(command)
                if response:
                    print(response)
            except KeyboardInterrupt:
                print("\n使用'exit'命令退出")
            except Exception as e:
                print(f"错误: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("用法: python esp32_client.py <ESP32_IP地址> [端口]")
        return
    
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
    
    client = ESP32Client(host, port)
    
    # 首先测试网络连接
    if not client.test_connection():
        print("网络连接测试失败，请检查IP地址和网络连接")
        return
    
    # 然后测试端口
    if not client.test_port():
        print("端口测试失败，请检查ESP32服务器是否正在运行以及端口是否开放")
        return
    
    # 尝试连接
    if client.connect():
        try:
            # 连接成功后发送一个测试命令
            response = client.send_command("hello")
            if response:
                print("测试命令成功!")
            else:
                print("测试命令失败!")
            
            # 进入交互模式
            client.interactive_mode()
        finally:
            client.disconnect()
    else:
        print("无法连接到ESP32服务器")

if __name__ == "__main__":
    main()
