# led.py
import machine
import time
from ep32.utils import debug_log
from ep32.config import LED_PIN

# 初始化LED
led_pin = machine.Pin(LED_PIN, machine.Pin.OUT)

# 控制LED闪烁
def blink_led(times=1, interval=0.5):
    debug_log(f"LED闪烁 {times} 次，间隔 {interval} 秒")
    for _ in range(times):
        led_pin.value(1)  # 开灯
        time.sleep(interval)
        led_pin.value(0)  # 关灯
        time.sleep(interval)

# 打开LED
def led_on():
    debug_log("LED已打开")
    led_pin.value(1)

# 关闭LED
def led_off():
    debug_log("LED已关闭")
    led_pin.value(0)
