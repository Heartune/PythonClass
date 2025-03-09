import subprocess
import time
import os
import sys
import signal
import atexit

SERVER_FILE = "08-Server.py"  # 服务器脚本文件名
CLIENT_FILE = "08-Client.py"  # 客户端脚本文件名

# 存储所有进程
processes = []


def cleanup():
    """清理所有子进程"""
    print("正在关闭所有进程...")
    for process in processes:
        if process.poll() is None:  # 检查进程是否还在运行
            try:
                if sys.platform == "win32":
                    process.terminate()  # Windows 平台使用 terminate
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Unix 平台
            except:
                pass
    print("所有进程已关闭")


# 注册退出处理函数
atexit.register(cleanup)


def start_server():
    """启动服务器进程"""
    print("正在启动服务器...")

    if sys.platform == "win32":
        # Windows平台
        server_process = subprocess.Popen(
            ["python", SERVER_FILE],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # Unix平台
        server_process = subprocess.Popen(
            ["python3", SERVER_FILE],
            preexec_fn=os.setsid
        )

    processes.append(server_process)
    print(f"服务器已启动，PID: {server_process.pid}")

    # 等待服务器启动
    time.sleep(2)
    return server_process


def start_client(client_number):
    """启动客户端进程"""
    print(f"正在启动客户端 {client_number}...")

    if sys.platform == "win32":
        # Windows平台 - 创建新的控制台窗口
        client_process = subprocess.Popen(
            ["python", CLIENT_FILE],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # Unix平台
        client_process = subprocess.Popen(
            ["python3", CLIENT_FILE],
            preexec_fn=os.setsid
        )

    processes.append(client_process)
    print(f"客户端 {client_number} 已启动，PID: {client_process.pid}")

    return client_process


def main():
    """主函数"""
    try:
        # 首先启动服务器
        server_process = start_server()

        # 然后启动4个客户端
        client_processes = []
        for i in range(1, 5):
            client_process = start_client(i)
            client_processes.append(client_process)
            # 稍微延迟，避免同时启动造成问题
            time.sleep(1)

        print("聊天系统已全部启动！")
        print("按 Ctrl+C 停止所有进程")

        # 保持脚本运行，直到用户中断
        while True:
            time.sleep(1)

            # 检查服务器是否还在运行
            if server_process.poll() is not None:
                print("服务器已停止运行，正在关闭所有客户端...")
                break

            # 检查客户端是否还在运行
            clients_running = 0
            for i, process in enumerate(client_processes):
                if process.poll() is None:
                    clients_running += 1

            if clients_running == 0:
                print("所有客户端已关闭，正在停止服务器...")
                break

    except KeyboardInterrupt:
        print("\n检测到键盘中断，正在关闭所有进程...")
    finally:
        cleanup()


if __name__ == "__main__":
    main()