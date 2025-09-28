# file_ops.py
import os
import json
from ep32.utils import debug_log
from ep32.config import USERPASS_FILE, TRANSFER_STATUS_FILE

# 初始化用户名和密码
def init_userpass():
    debug_log("初始化用户名和密码")
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
        debug_log("已创建默认用户名和密码文件")
        return default_credentials
    else:
        # 读取现有用户名和密码
        with open(USERPASS_FILE, "r") as f:
            credentials = json.load(f)
        debug_log("已读取现有用户名和密码")
        return credentials

# 更新用户名和密码
def update_userpass(username, password):
    debug_log(f"更新用户名和密码: {username}")
    credentials = {
        "username": username,
        "password": password
    }
    with open(USERPASS_FILE, "w") as f:
        json.dump(credentials, f)
    debug_log("用户名和密码已更新")
    return credentials

# 列出文件
def list_files():
    debug_log("列出文件")
    files = os.listdir()
    result = "文件列表:\n"
    for f in files:
        try:
            size = os.stat(f)[6]
            result += f"{f} - {size} 字节\n"
        except:
            result += f"{f} - [目录]\n"
    debug_log(f"找到 {len(files)} 个文件/目录")
    return result

# 读取文件
def read_file(filename):
    debug_log(f"读取文件: {filename}")
    try:
        with open(filename, "r") as f:
            content = f.read()
        debug_log(f"成功读取文件: {filename}, 大小: {len(content)} 字节")
        return content
    except Exception as e:
        debug_log(f"读取文件错误: {str(e)}")
        return f"读取文件错误: {str(e)}"

# 写入文件
def write_file(filename, content):
    debug_log(f"写入文件: {filename}")
    try:
        with open(filename, "w") as f:
            f.write(content)
        debug_log(f"文件 {filename} 已保存")
        return f"文件 {filename} 已保存"
    except Exception as e:
        debug_log(f"写入文件错误: {str(e)}")
        return f"写入文件错误: {str(e)}"

# 删除文件
def delete_file(filename):
    debug_log(f"删除文件: {filename}")
    try:
        os.remove(filename)
        debug_log(f"文件 {filename} 已删除")
        return f"文件 {filename} 已删除"
    except Exception as e:
        debug_log(f"删除文件错误: {str(e)}")
        return f"删除文件错误: {str(e)}"

# 保存传输状态
def save_transfer_status(filename, position, total_size, file_hash):
    debug_log(f"保存传输状态: {filename}, 位置: {position}/{total_size}")
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
    debug_log("获取传输状态")
    try:
        if TRANSFER_STATUS_FILE in os.listdir():
            with open(TRANSFER_STATUS_FILE, "r") as f:
                status = json.load(f)
            debug_log(f"找到传输状态: {status['filename']}, 位置: {status['position']}/{status['total_size']}")
            return status
    except Exception as e:
        debug_log(f"获取传输状态错误: {str(e)}")
    return None

# 删除传输状态
def delete_transfer_status():
    debug_log("删除传输状态")
    try:
        if TRANSFER_STATUS_FILE in os.listdir():
            os.remove(TRANSFER_STATUS_FILE)
            debug_log("传输状态已删除")
    except Exception as e:
        debug_log(f"删除传输状态错误: {str(e)}")

# 计算文件哈希
def calculate_hash(data):
    debug_log("计算文件哈希")
    # 简单的哈希计算，实际应用中可以使用更复杂的算法
    hash_value = 0
    for byte in data:
        hash_value = (hash_value * 31 + byte) % (2**32)
    debug_log(f"文件哈希: {hash_value}")
    return hash_value
