# bluetooth.py
import bluetooth
from ep32.utils import debug_log

# 设置蓝牙
def setup_bluetooth():
    debug_log("设置蓝牙")
    bt = bluetooth.BLE()  # 初始化 BLE
    bt.active(True)  # 激活蓝牙
    # 广播设备信息（设置设备名称等）
    bt.gap_advertise(100, adv_data=b'\x02\x01\x06\x03\x03\xAA\xFE\x0F\x09ESP32')
    debug_log("蓝牙设置完成")
    return bt
