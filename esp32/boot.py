# main.py
import time
import network
import machine
import gc
import esp32
from ep32.config import DEBUG_MODE, DEBUG_LOG_FILE, MONITOR_INTERVAL
from ep32.utils import debug_log, monitor_system_status, format_time, get_weather, get_ip_location
from ep32.wifi import connect_wifi
from ep32.bluetooth import setup_bluetooth
from ep32.server import start_server, handle_client_connection, send_chunked_data, receive_chunked_data
from ep32.led import blink_led, led_on, led_off
from ep32.file_ops import (
    init_userpass, update_userpass, list_files, read_file, write_file, 
    delete_file, get_transfer_status, delete_transfer_status
)

# 处理客户端命令
def handle_client_command(cl, data, credentials):
    if data.decode() == "hello":
        blink_led(times=1)  # 接收到数据后闪烁一次
        cl.send('你好，esp32单片机'.encode())
    elif data.decode() == "exit" or data.decode() == "Exit":
        blink_led(times=1)
        cl.send('本服务端即将关闭，请关闭此程序，再次打开服务端，请按esp32上的boot按键即可！'.encode())
        cl.close()
        led_off()
        return False  # 返回False表示退出命令循环
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
weather - 查询天气信息(自动定位)
location - 查询位置信息
ls - 列出文件
cat <文件名> - 读取文件内容
write <文件名> <内容> - 写入文件
del <文件名> - 删除文件
upload <文件名> - 上传文件
get <文件名> - 下载文件
resume <文件名> - 断点续传
debug on - 开启调试模式
debug off - 关闭调试模式
debug status - 查看调试模式状态
debug log - 查看调试日志
debug clear - 清空调试日志
""".encode())
    elif data.decode() == "ledon":
        led_on()
        cl.send('LED已打开'.encode())
    elif data.decode() == "ledoff":
        led_off()
        cl.send('LED已关闭'.encode())
    elif data.decode().startswith("blink "):
        try:
            # 解析闪烁次数和间隔
            params = data.decode()[6:].split()
            times = int(params[0]) if len(params) > 0 else 1
            interval = float(params[1]) if len(params) > 1 else 0.5
            blink_led(times, interval)
            cl.send(f'LED已闪烁{times}次，间隔{interval}秒'.encode())
        except Exception as e:
            debug_log(f"LED闪烁参数错误: {str(e)}")
            cl.send('闪烁参数错误，格式: blink <次数> <间隔(秒)>'.encode())
    elif data.decode() == "wifistatus":
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            status = f"Wi-Fi已连接\nIP地址: {wlan.ifconfig()[0]}\n子网掩码: {wlan.ifconfig()[1]}\n网关: {wlan.ifconfig()[2]}\nDNS: {wlan.ifconfig()[3]}"
            debug_log(f"Wi-Fi状态: 已连接, IP: {wlan.ifconfig()[0]}")
        else:
            status = "Wi-Fi未连接"
            debug_log("Wi-Fi状态: 未连接")
        cl.send(status.encode())
    elif data.decode() == "sysinfo":
        debug_log("获取系统信息")
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
        debug_log(f"系统信息: CPU频率: {freq/1000000} MHz, 空闲内存: {mem_free} 字节")
        cl.send(info.encode())
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
        except Exception as e:
            debug_log(f"修改密码失败: {str(e)}")
            cl.send('修改密码失败'.encode())
    elif data.decode() == "user1024":
        debug_log("请求用户名")
        cl.send(credentials["username"].encode())
    elif data.decode() == "passwd1024":
        debug_log("请求密码")
        cl.send(credentials["password"].encode())
    elif data.decode() == "time":
        current_time = time.time()
        debug_log(f"请求当前时间: {format_time(current_time)}")
        cl.send(f"当前时间: {format_time(current_time)}".encode())
    elif data.decode() == "weather":
        weather = get_weather()
        if "error" in weather:
            cl.send(weather["error"].encode())
        else:
            weather_info = f"位置: {weather['city']}, {weather['region']}, {weather['country']}\n"
            weather_info += f"坐标: {weather['lat']}, {weather['lon']}\n"
            weather_info += f"时区: {weather['timezone']}\n"
            weather_info += f"温度: {weather['temperature']}°C\n"
            weather_info += f"体感温度: {weather['feels_like']}°C\n"
            weather_info += f"天气: {weather['description']}\n"
            weather_info += f"湿度: {weather['humidity']}%\n"
            weather_info += f"气压: {weather['pressure']} hPa\n"
            weather_info += f"能见度: {weather['visibility']} km\n"
            weather_info += f"紫外线指数: {weather['uv_index']}"
            cl.send(weather_info.encode())
    elif data.decode() == "location":
        location = get_ip_location()
        if "error" in location:
            cl.send(location["error"].encode())
        else:
            location_info = f"国家: {location['country']}\n"
            location_info += f"地区: {location['region']}\n"
            location_info += f"城市: {location['city']}\n"
            location_info += f"坐标: {location['lat']}, {location['lon']}\n"
            location_info += f"时区: {location['timezone']}\n"
            location_info += f"IP地址: {location['ip']}"
            cl.send(location_info.encode())
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
            debug_log(f"写入文件错误: {str(e)}")
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
    # 调试命令
    elif data.decode() == "debug on":
        global DEBUG_MODE
        DEBUG_MODE = True
        debug_log("调试模式已开启")
        cl.send('调试模式已开启'.encode())
    elif data.decode() == "debug off":
        debug_log("调试模式即将关闭")
        DEBUG_MODE = False
        cl.send('调试模式已关闭'.encode())
    elif data.decode() == "debug status":
        status = "调试模式: " + ("开启" if DEBUG_MODE else "关闭")
        cl.send(status.encode())
    elif data.decode() == "debug log":
        try:
            with open(DEBUG_LOG_FILE, "r") as f:
                log_content = f.read()
            if not send_chunked_data(cl, log_content):
                cl.send('日志发送失败'.encode())
        except Exception as e:
            cl.send(f'读取日志失败: {str(e)}'.encode())
    elif data.decode() == "debug clear":
        try:
            with open(DEBUG_LOG_FILE, "w") as f:
                f.write("")
            cl.send('调试日志已清空'.encode())
        except Exception as e:
            cl.send(f'清空日志失败: {str(e)}'.encode())
    else:
        blink_led(times=1)
        cl.send('错误，发送的指令不对！'.encode())
    
    return True  # 返回True表示继续命令循环

# 主程序
def main():
    debug_log("系统启动")
    
    # 初始化用户名和密码
    credentials = init_userpass()
    debug_log(f"用户名初始化完成: {credentials['username']}")
    
    # 连接Wi-Fi
    if not connect_wifi():
        debug_log("Wi-Fi连接失败，系统将以离线模式运行")

    # 设置蓝牙
    bt = setup_bluetooth()

    # 启动TCP服务器
    server = start_server()

    # 连接成功后闪烁LED
    debug_log("Wi-Fi已连接，开始闪烁LED")
    blink_led(times=3)  # Wi-Fi连接成功后，闪烁3次

    debug_log("进入主循环，等待客户端连接")
    
    # 初始化系统监控时间
    last_monitor_time = time.time()

    while True:
        # 定期监控系统状态
        if time.time() - last_monitor_time > MONITOR_INTERVAL:
            monitor_system_status()
            last_monitor_time = time.time()
        
        # 等待客户端连接
        try:
            debug_log("等待客户端连接...")
            cl, addr = server.accept()
            
            # 处理客户端连接
            if not handle_client_connection(cl, addr, credentials):
                continue
                
            # 接收客户端数据
            while True:
                led_on()
                try:
                    data = cl.recv(1024)
                    if not data:
                        debug_log("客户端断开连接")
                        led_off()
                        break
                    debug_log(f'接收到的数据: {data.decode()}')
                    
                    # 处理命令
                    if not handle_client_command(cl, data, credentials):
                        break
                    
                except OSError as e:
                    debug_log(f"客户端断开连接: {str(e)}")
                    led_off()
                    try:
                        cl.close()
                    except:
                        pass
                    break
        except OSError as e:
            debug_log(f"接受连接时出错: {str(e)}")
            time.sleep(1)  # 等待一秒后继续尝试接受连接
        except Exception as e:
            debug_log(f"未知错误: {str(e)}")
            time.sleep(1)

if __name__ == "__main__":
    main()
