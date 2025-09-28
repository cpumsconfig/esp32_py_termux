# wifi.py
import network
import time
import machine
from ep32.utils import debug_log, get_ntp_time, format_time
from ep32.config import SSID, PASSWORD

# 初始化Wi-Fi连接
def connect_wifi():
    debug_log("开始连接Wi-Fi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        debug_log("Wi-Fi未连接，尝试连接...")
        wlan.connect(SSID, PASSWORD)
        connection_start = time.time()
        while not wlan.isconnected():
            if time.time() - connection_start > 10:  # 10秒超时
                debug_log("Wi-Fi连接超时")
                return False
            time.sleep(1)
    
    debug_log(f"Wi-Fi连接成功，IP地址: {wlan.ifconfig()[0]}")
    
    # 同步时间
    try:
        debug_log("尝试同步时间...")
        ntp_time = get_ntp_time()
        machine.RTC().datetime(time.localtime(ntp_time)[0:7] + (0,))
        debug_log(f"时间已同步: {format_time(ntp_time)}")
    except Exception as e:
        debug_log(f"时间同步失败: {str(e)}")
    
    return True
