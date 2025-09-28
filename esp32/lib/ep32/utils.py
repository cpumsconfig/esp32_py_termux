# utils.py
import time
import json
import ustruct
import gc
import machine
import network
import socket
import urequests
from ep32.config import DEBUG_MODE, DEBUG_LOG_FILE

# 调试信息输出函数
def debug_log(message):
    if DEBUG_MODE:
        timestamp = time.time()
        formatted_time = format_time(timestamp)
        log_entry = f"[{formatted_time}] {message}\n"
        print(log_entry)
        
        try:
            with open(DEBUG_LOG_FILE, "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"无法写入调试日志: {str(e)}")

# 格式化时间
def format_time(timestamp):
    tm = time.localtime(timestamp)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(tm[0], tm[1], tm[2], tm[3], tm[4], tm[5])

# 获取网络时间
def get_ntp_time():
    debug_log("获取网络时间")
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

# 获取IP位置信息
def get_ip_location():
    debug_log("获取IP位置信息")
    try:
        # 使用ipinfo.io获取IP位置信息（免费版本，不需要SSL）
        url = "http://ipinfo.io/json"
        response = urequests.get(url)
        data = response.json()
        response.close()
        
        if "country" in data:
            # 解析位置信息
            loc = data.get("loc", "0,0").split(",")
            location = {
                "country": data.get("country", "未知"),
                "region": data.get("region", "未知"),
                "city": data.get("city", "未知"),
                "lat": float(loc[0]) if len(loc) > 0 else 0,
                "lon": float(loc[1]) if len(loc) > 1 else 0,
                "timezone": data.get("timezone", "未知"),
                "ip": data.get("ip", "未知")
            }
            debug_log(f"获取位置信息成功: {location['city']}, {location['country']}")
            return location
        else:
            debug_log("无法获取位置信息: 无country字段")
            return {"error": "无法获取位置信息"}
    except Exception as e:
        debug_log(f"获取位置信息时出错: {str(e)}")
        return {"error": f"获取位置信息时出错: {str(e)}"}

# 获取天气信息
def get_weather():
    debug_log("获取天气信息")
    try:
        # 首先获取位置信息
        location = get_ip_location()
        if "error" in location:
            debug_log(f"获取天气信息失败: {location['error']}")
            return {"error": location["error"]}
        
        city = location["city"]
        # 使用wttr.in免费天气API
        url = f"http://wttr.in/{city}?format=j1"
        response = urequests.get(url)
        data = response.json()
        response.close()
        
        if "weather" in data:
            current = data["current_condition"][0]
            weather = {
                "city": city,
                "country": location["country"],
                "region": location["region"],
                "temperature": current["temp_C"],
                "description": current["weatherDesc"][0]["value"],
                "humidity": current["humidity"],
                "pressure": current["pressure"],
                "lat": location["lat"],
                "lon": location["lon"],
                "timezone": location["timezone"],
                "feels_like": current["FeelsLikeC"],
                "visibility": current["visibility"],
                "uv_index": current["uvIndex"]
            }
            debug_log(f"获取天气信息成功: {weather['city']}, {weather['temperature']}°C")
            return weather
        else:
            debug_log("无法获取天气信息: 无weather字段")
            return {"error": "无法获取天气信息"}
    except Exception as e:
        debug_log(f"获取天气信息时出错: {str(e)}")
        return {"error": f"获取天气信息时出错: {str(e)}"}

# 系统状态监控
def monitor_system_status():
    debug_log("开始系统状态监控")
    try:
        # 获取内存信息
        mem_free = gc.mem_free()
        mem_alloc = gc.mem_alloc()
        debug_log(f"内存状态 - 空闲: {mem_free} 字节, 已分配: {mem_alloc} 字节")
        
        # 获取Wi-Fi状态
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            debug_log(f"Wi-Fi状态 - 已连接, IP: {wlan.ifconfig()[0]}")
        else:
            debug_log("Wi-Fi状态 - 未连接")
        
        # 获取CPU温度
        try:
            import esp32
            temp = esp32.raw_temperature()
            debug_log(f"CPU温度: {temp} °C")
        except:
            debug_log("无法获取CPU温度")
        
        # 检查文件系统
        try:
            import os
            files = os.listdir()
            debug_log(f"文件系统 - 文件数量: {len(files)}")
        except:
            debug_log("无法访问文件系统")
            
    except Exception as e:
        debug_log(f"系统状态监控出错: {str(e)}")
