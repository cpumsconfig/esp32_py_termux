import network
import socket
import bluetooth
import time
import machine
import os
import json
import urequests
import ustruct
import gc

# 配置Wi-Fi连接信息
SSID = "CU-C1E0"
PASSWORD = "26782811"

# 配置GPIO引脚，用于控制LED灯（假设2号灯连接到GPIO2）
led_pin = machine.Pin(2, machine.Pin.OUT)

# 用户名和密码文件路径
USERPASS_FILE = "userpass.txt"

# 天气API配置
WEATHER_API_KEY = "YOUR_API_KEY"  # 替换为您的天气API密钥
WEATHER_CITY = "Beijing"  # 默认城市

# 传输状态文件路径
TRANSFER_STATUS_FILE = "transfer_status.txt"

# 初始化用户名和密码
def init_userpass():
    # 检查文件是否存在
    if not USERPASS_FILE in os.listdir():
        # 创建默认用户名和密码
        default_credentials = {
            "username": "root",
            "password": "123456"
        }
        # 写入文件
        with open(USERPASS_FILE, "w") as f:
            json.dump(default_credentials, f)
        print("已创建默认用户名和密码文件")
        return default_credentials
    else:
        # 读取现有用户名和密码
        with open(USERPASS_FILE, "r") as f:
            credentials = json.load(f)
        return credentials

# 更新用户名和密码
def update_userpass(username, password):
    credentials = {
        "username": username,
        "password": password
    }
    with open(USERPASS_FILE, "w") as f:
        json.dump(credentials, f)
    print("用户名和密码已更新")
    return credentials

# 获取网络时间
def get_ntp_time():
    NTP_SERVER = "ntp1.aliyun.com"
    NTP_DELTA = 3155673600  # 1970-1900年的秒数
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(NTP_SERVER, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = ustruct.unpack("!I", msg[40:44])[0]
    return val - NTP_DELTA

# 格式化时间
def format_time(timestamp):
    tm = time.localtime(timestamp)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(tm[0], tm[1], tm[2], tm[3], tm[4], tm[5])

# 获取天气信息
def get_weather(city=WEATHER_CITY):
    try:
        # 使用OpenWeatherMap API
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = urequests.get(url)
        data = response.json()
        response.close()
        
        if data["cod"] == 200:
            weather = {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"]
            }
            return weather
        else:
            return {"error": "无法获取天气信息"}
    except Exception as e:
        return {"error": f"获取天气信息时出错: {str(e)}"}

# 初始化Wi-Fi连接
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("正在连接Wi-Fi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Wi-Fi连接成功，IP地址:", wlan.ifconfig()[0])
    
    # 同步时间
    try:
        ntp_time = get_ntp_time()
        machine.RTC().datetime(time.localtime(ntp_time)[0:7] + (0,))
        print("时间已同步:", format_time(ntp_time))
    except:
        print("时间同步失败")

# 设置蓝牙
def setup_bluetooth():
    bt = bluetooth.BLE()  # 初始化 BLE
    bt.active(True)  # 激活蓝牙
    # 广播设备信息（设置设备名称等）
    bt.gap_advertise(100, adv_data=b'\x02\x01\x06\x03\x03\xAA\xFE\x0F\x09ESP32')
    return bt

# 启动服务器，监听端口5555
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 5555)[0][-1]
    s = socket.socket()
    # 设置套接字选项，允许地址重用
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print('正在监听端口 5555...')
    return s

# 控制2号灯闪烁
def blink_led(times=1, interval=0.5):
    for _ in range(times):
        led_pin.value(1)  # 开灯
        time.sleep(interval)
        led_pin.value(0)  # 关灯
        time.sleep(interval)

# 列出文件
def list_files():
    files = os.listdir()
    result = "文件列表:\n"
    for f in files:
        try:
            size = os.stat(f)[6]
            result += f"{f} - {size} 字节\n"
        except:
            result += f"{f} - [目录]\n"
    return result

# 读取文件
def read_file(filename):
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        return f"读取文件错误: {str(e)}"

# 写入文件
def write_file(filename, content):
    try:
        with open(filename, "w") as f:
            f.write(content)
        return f"文件 {filename} 已保存"
    except Exception as e:
        return f"写入文件错误: {str(e)}"

# 删除文件
def delete_file(filename):
    try:
        os.remove(filename)
        return f"文件 {filename} 已删除"
    except Exception as e:
        return f"删除文件错误: {str(e)}"

# 保存传输状态
def save_transfer_status(filename, position, total_size, file_hash):
    status = {
        "filename": filename,
        "position": position,
        "total_size": total_size,
        "file_hash": file_hash
    }
    with open(TRANSFER_STATUS_FILE, "w") as f:
        json.dump(status, f)

# 获取传输状态
def get_transfer_status():
    try:
        if TRANSFER_STATUS_FILE in os.listdir():
            with open(TRANSFER_STATUS_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return None

# 删除传输状态
def delete_transfer_status():
    try:
        if TRANSFER_STATUS_FILE in os.listdir():
            os.remove(TRANSFER_STATUS_FILE)
    except:
        pass

# 计算文件哈希
def calculate_hash(data):
    # 简单的哈希计算，实际应用中可以使用更复杂的算法
    hash_value = 0
    for byte in data:
        hash_value = (hash_value * 31 + byte) % (2**32)
    return hash_value

# 分块发送数据
def send_chunked_data(socket, data, chunk_size=1024):
    total_length = len(data)
    # 首先发送数据总长度
    socket.send(str(total_length).encode())
    # 等待客户端确认
    ack = socket.recv(10)
    if ack.decode() != "OK":
        return False
    
    # 分块发送数据
    for i in range(0, total_length, chunk_size):
        chunk = data[i:i+chunk_size]
        socket.send(chunk.encode())
        # 等待客户端确认
        ack = socket.recv(10)
        if ack.decode() != "OK":
            return False
    
    return True

# 接收分块数据
def receive_chunked_data(socket, filename=None, resume_position=0):
    # 接收数据总长度
    length_str = socket.recv(1024).decode()
    try:
        total_length = int(length_str)
    except:
        return None, 0
    
    # 发送确认
    socket.send("OK".encode())
    
    # 如果提供了文件名，则写入文件
    if filename:
        mode = "ab" if resume_position > 0 else "wb"
        with open(filename, mode) as f:
            if resume_position > 0:
                f.seek(resume_position)
            
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
            
            # 传输完成，删除状态文件
            delete_transfer_status()
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
        
        return data.decode(), total_length

# 主程序
def main():
    # 初始化用户名和密码
    credentials = init_userpass()
    
    # 连接Wi-Fi
    connect_wifi()

    # 设置蓝牙
    bt = setup_bluetooth()

    # 启动TCP服务器
    server = start_server()

    # 连接成功后闪烁2号灯
    print("Wi-Fi已连接，开始闪烁2号灯")
    blink_led(times=3)  # Wi-Fi连接成功后，闪烁3次

    while True:
        # 等待客户端连接
        try:
            cl, addr = server.accept()
            print('客户端连接成功，地址:', addr)

            # 客户端连接成功后，2号灯常亮
            led_pin.value(1)  # 常亮
            cl.send('y'.encode())

            # 接收客户端数据
            while True:
                led_pin.value(1)
                try:
                    data = cl.recv(1024)
                    if not data:
                        led_pin.value(0)
                        break
                    print('接收到的数据:', data.decode())
                    if data.decode() == "hello":
                        blink_led(times=1)  # 接收到数据后闪烁一次
                        cl.send('你好，esp32单片机'.encode())
                    elif data.decode() == "exit" or data.decode() == "Exit":
                        blink_led(times=1)
                        cl.send('本服务端即将关闭，请关闭此程序，再次打开服务端，请按esp32上的boot按键即可！'.encode())
                        cl.close()
                        led_pin.value(0)
                        break
                    elif data.decode() == "help":
                        blink_led(times=1)
                        cl.send("""
可用命令:
hello - 测试连接
exit - 退出服务端
help - 显示帮助信息
ledon - 打开LED
ledoff - 关闭LED
blink <次数> <间隔> - 控制LED闪烁
wifistatus - 查询Wi-Fi状态
sysinfo - 显示系统信息
reboot - 重启系统
changepass <新密码> - 修改密码
user1024 - 用户名验证
passwd1024 - 密码验证
time - 显示当前时间
weather [城市] - 查询天气信息
ls - 列出文件
cat <文件名> - 读取文件内容
write <文件名> <内容> - 写入文件
del <文件名> - 删除文件
upload <文件名> - 上传文件
get <文件名> - 下载文件
resume <文件名> - 断点续传
""".encode())
                    elif data.decode() == "ledon":
                        led_pin.value(1)  # 开灯
                        cl.send('LED已打开'.encode())
                    elif data.decode() == "ledoff":
                        led_pin.value(0)  # 关灯
                        cl.send('LED已关闭'.encode())
                    elif data.decode().startswith("blink "):
                        try:
                            # 解析闪烁次数和间隔
                            params = data.decode()[6:].split()
                            times = int(params[0]) if len(params) > 0 else 1
                            interval = float(params[1]) if len(params) > 1 else 0.5
                            blink_led(times, interval)
                            cl.send(f'LED已闪烁{times}次，间隔{interval}秒'.encode())
                        except:
                            cl.send('闪烁参数错误，格式: blink <次数> <间隔(秒)>'.encode())
                    elif data.decode() == "wifistatus":
                        wlan = network.WLAN(network.STA_IF)
                        if wlan.isconnected():
                            status = f"Wi-Fi已连接\nIP地址: {wlan.ifconfig()[0]}\n子网掩码: {wlan.ifconfig()[1]}\n网关: {wlan.ifconfig()[2]}\nDNS: {wlan.ifconfig()[3]}"
                        else:
                            status = "Wi-Fi未连接"
                        cl.send(status.encode())
                    elif data.decode() == "sysinfo":
                        import esp32
                        freq = machine.freq()
                        mem_free = gc.mem_free()
                        mem_alloc = gc.mem_alloc()
                        try:
                            temp = esp32.raw_temperature()
                            temp_info = f"内部温度: {temp} °C"
                        except:
                            temp_info = "内部温度: 不可用"
                        try:
                            hall = esp32.hall_sensor()
                            hall_info = f"霍尔传感器: {hall}"
                        except AttributeError:
                            hall_info = "霍尔传感器: 不可用"
                        info = f"系统信息:\nCPU频率: {freq/1000000} MHz\n空闲内存: {mem_free} 字节\n已分配内存: {mem_alloc} 字节\n{temp_info}\n{hall_info}"
                        cl.send(info.encode())
                    elif data.decode() == "reboot":
                        cl.send('系统将在3秒后重启...'.encode())
                        cl.close()
                        time.sleep(3)
                        machine.reset()
                    elif data.decode().startswith("changepass "):
                        try:
                            # 解析新密码
                            new_password = data.decode()[11:].strip()
                            if new_password:
                                # 更新密码
                                credentials = update_userpass(credentials["username"], new_password)
                                cl.send('密码已更新'.encode())
                            else:
                                cl.send('密码不能为空'.encode())
                        except:
                            cl.send('修改密码失败'.encode())
                    elif data.decode() == "user1024":
                        cl.send(credentials["username"].encode())
                    elif data.decode() == "passwd1024":
                        cl.send(credentials["password"].encode())
                    elif data.decode() == "time":
                        current_time = time.time()
                        cl.send(f"当前时间: {format_time(current_time)}".encode())
                    elif data.decode().startswith("weather "):
                        city = data.decode()[8:].strip()
                        if not city:
                            city = WEATHER_CITY
                        weather = get_weather(city)
                        if "error" in weather:
                            cl.send(weather["error"].encode())
                        else:
                            weather_info = f"城市: {weather['city']}\n温度: {weather['temperature']}°C\n天气: {weather['description']}\n湿度: {weather['humidity']}%\n气压: {weather['pressure']} hPa"
                            cl.send(weather_info.encode())
                    elif data.decode() == "weather":
                        weather = get_weather()
                        if "error" in weather:
                            cl.send(weather["error"].encode())
                        else:
                            weather_info = f"城市: {weather['city']}\n温度: {weather['temperature']}°C\n天气: {weather['description']}\n湿度: {weather['humidity']}%\n气压: {weather['pressure']} hPa"
                            cl.send(weather_info.encode())
                    elif data.decode() == "ls":
                        files = list_files()
                        cl.send(files.encode())
                    elif data.decode().startswith("cat "):
                        filename = data.decode()[4:].strip()
                        if filename:
                            content = read_file(filename)
                            if not content.startswith("读取文件错误"):
                                # 使用分块发送
                                if not send_chunked_data(cl, content):
                                    cl.send('文件发送失败'.encode())
                            else:
                                cl.send(content.encode())
                        else:
                            cl.send('请指定文件名'.encode())
                    elif data.decode().startswith("write "):
                        try:
                            params = data.decode()[6:].split(maxsplit=1)
                            if len(params) >= 2:
                                filename, content = params[0], params[1]
                                result = write_file(filename, content)
                                cl.send(result.encode())
                            else:
                                cl.send('格式: write <文件名> <内容>'.encode())
                        except Exception as e:
                            cl.send(f'写入文件错误: {str(e)}'.encode())
                    elif data.decode().startswith("del "):
                        filename = data.decode()[4:].strip()
                        if filename:
                            result = delete_file(filename)
                            cl.send(result.encode())
                        else:
                            cl.send('请指定文件名'.encode())
                    elif data.decode().startswith("upload "):
                        filename = data.decode()[7:].strip()
                        if filename:
                            # 检查是否已有传输状态
                            transfer_status = get_transfer_status()
                            if transfer_status and transfer_status["filename"] == filename:
                                # 断点续传
                                cl.send(f"RESUME:{transfer_status['position']}:{transfer_status['total_size']}".encode())
                                # 接收文件数据
                                received_filename, received_size = receive_chunked_data(cl, filename, transfer_status["position"])
                                if received_filename:
                                    cl.send(f"文件 {filename} 上传成功，共 {received_size} 字节".encode())
                                else:
                                    cl.send("文件上传失败".encode())
                            else:
                                # 新上传
                                cl.send("READY".encode())
                                # 接收文件数据
                                received_filename, received_size = receive_chunked_data(cl, filename)
                                if received_filename:
                                    cl.send(f"文件 {filename} 上传成功，共 {received_size} 字节".encode())
                                else:
                                    cl.send("文件上传失败".encode())
                        else:
                            cl.send('请指定文件名'.encode())
                    elif data.decode().startswith("get "):
                        filename = data.decode()[4:].strip()
                        if filename:
                            if filename in os.listdir():
                                # 读取文件内容
                                with open(filename, "rb") as f:
                                    content = f.read()
                                # 发送文件大小
                                cl.send(str(len(content)).encode())
                                # 等待客户端确认
                                ack = cl.recv(10)
                                if ack.decode() == "OK":
                                    # 分块发送文件内容
                                    chunk_size = 1024
                                    for i in range(0, len(content), chunk_size):
                                        chunk = content[i:i+chunk_size]
                                        cl.send(chunk)
                                        # 等待客户端确认
                                        ack = cl.recv(10)
                                        if ack.decode() != "OK":
                                            break
                                    cl.send("COMPLETE".encode())
                                else:
                                    cl.send("文件下载失败".encode())
                            else:
                                cl.send("文件不存在".encode())
                        else:
                            cl.send('请指定文件名'.encode())
                    elif data.decode().startswith("resume "):
                        filename = data.decode()[7:].strip()
                        if filename:
                            # 检查是否已有传输状态
                            transfer_status = get_transfer_status()
                            if transfer_status and transfer_status["filename"] == filename:
                                cl.send(f"FOUND:{transfer_status['position']}:{transfer_status['total_size']}".encode())
                            else:
                                cl.send("NOTFOUND".encode())
                        else:
                            cl.send('请指定文件名'.encode())
                    else:
                        blink_led(times=1)
                        cl.send('错误，发送的指令不对！'.encode())
                except OSError as e:
                    print("客户端断开连接:", e)
                    led_pin.value(0)
                    try:
                        cl.close()
                    except:
                        pass
                    break
        except OSError as e:
            print("接受连接时出错:", e)
            time.sleep(1)  # 等待一秒后继续尝试接受连接
        except Exception as e:
            print("未知错误:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
