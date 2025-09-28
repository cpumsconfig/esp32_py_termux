# server.py
import socket
import time
import os
from ep32.utils import debug_log
from ep32.config import SERVER_PORT
from ep32.led import led_on, led_off
from ep32.file_ops import get_transfer_status, save_transfer_status, delete_transfer_status

# 启动服务器，监听端口5555
def start_server():
    debug_log("启动TCP服务器，监听端口5555")
    try:
        addr = socket.getaddrinfo('0.0.0.0', SERVER_PORT)[0][-1]
        debug_log(f"获取地址信息成功: {addr}")
        
        s = socket.socket()
        debug_log("创建socket成功")
        
        # 设置套接字选项，允许地址重用
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        debug_log("设置socket选项成功")
        
        # 不设置超时时间，使用阻塞模式
        s.bind(addr)
        debug_log(f"绑定地址成功: {addr}")
        
        s.listen(1)
        debug_log('服务器启动成功，正在监听端口 5555...')
        
        # 添加额外的调试信息，确认服务器状态
        import network
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            debug_log(f"Wi-Fi连接状态: 已连接, IP: {ip}")
        else:
            debug_log("Wi-Fi连接状态: 未连接")
            
        return s
    except Exception as e:
        debug_log(f"启动服务器时出错: {str(e)}")
        # 尝试重新启动服务器
        debug_log("尝试重新启动服务器...")
        try:
            if 's' in locals():
                s.close()
            time.sleep(1)
            return start_server()
        except Exception as e2:
            debug_log(f"重新启动服务器失败: {str(e2)}")
            return None

# 分块发送数据
def send_chunked_data(socket, data, chunk_size=1024):
    debug_log(f"分块发送数据，总大小: {len(data)} 字节")
    total_length = len(data)
    # 首先发送数据总长度
    socket.send(str(total_length).encode())
    # 等待客户端确认
    ack = socket.recv(10)
    if ack.decode() != "OK":
        debug_log("分块发送数据失败: 客户端未确认总长度")
        return False
    
    # 分块发送数据
    for i in range(0, total_length, chunk_size):
        chunk = data[i:i+chunk_size]
        socket.send(chunk.encode())
        # 等待客户端确认
        ack = socket.recv(10)
        if ack.decode() != "OK":
            debug_log(f"分块发送数据失败: 客户端未确认块 {i//chunk_size}")
            return False
    
    debug_log("分块发送数据成功")
    return True

# 接收分块数据
def receive_chunked_data(socket, filename=None, resume_position=0):
    debug_log(f"接收分块数据，文件名: {filename}, 恢复位置: {resume_position}")
    # 接收数据总长度
    length_str = socket.recv(1024).decode()
    try:
        total_length = int(length_str)
        debug_log(f"数据总长度: {total_length} 字节")
    except Exception as e:
        debug_log(f"接收数据总长度错误: {str(e)}")
        return None, 0
    
    # 发送确认
    socket.send("OK".encode())
    
    # 如果提供了文件名，则写入文件
    if filename:
        mode = "ab" if resume_position > 0 else "wb"
        debug_log(f"写入文件模式: {mode}")
        with open(filename, mode) as f:
            if resume_position > 0:
                f.seek(resume_position)
                debug_log(f"文件指针移动到位置: {resume_position}")
            
            # 分块接收数据
            received = resume_position
            while received < total_length:
                chunk = socket.recv(1024)
                f.write(chunk)
                received += len(chunk)
                # 发送确认
                socket.send("OK".encode())
                
                # 保存传输状态
                save_transfer_status(filename, received, total_length, 0)
                debug_log(f"已接收: {received}/{total_length} 字节")
            
            # 传输完成，删除状态文件
            delete_transfer_status()
            debug_log(f"文件接收完成: {filename}, 大小: {total_length} 字节")
            return filename, total_length
    else:
        # 如果没有提供文件名，则返回接收到的数据
        data = b""
        received = 0
        while received < total_length:
            chunk = socket.recv(1024)
            data += chunk
            received += len(chunk)
            # 发送确认
            socket.send("OK".encode())
            debug_log(f"已接收: {received}/{total_length} 字节")
        
        debug_log(f"数据接收完成，大小: {total_length} 字节")
        return data.decode(), total_length

# 处理客户端连接
def handle_client_connection(cl, addr, credentials):
    debug_log(f'客户端连接成功，地址: {addr}')

    # 客户端连接成功后，LED常亮
    led_on()
    
    # 发送初始握手消息
    debug_log("发送握手消息...")
    cl.send('y'.encode())
    
    # 等待客户端确认，使用非阻塞方式
    cl.setblocking(False)
    start_time = time.time()
    ack_received = False
    
    debug_log("等待客户端确认...")
    while time.time() - start_time < 5:  # 5秒超时
        try:
            ack = cl.recv(10)
            if ack.decode() == "OK":
                ack_received = True
                debug_log("握手成功")
                break
        except:
            # 非阻塞模式下，没有数据会抛出异常
            time.sleep(0.1)
    
    # 恢复阻塞模式
    cl.setblocking(True)
    
    if not ack_received:
        debug_log("客户端握手超时")
        cl.close()
        led_off()
        return False

    # 接收客户端数据
    debug_log("开始接收客户端数据...")
    return True
