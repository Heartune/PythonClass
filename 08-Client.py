import socket
import threading
import json
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox


class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("聊天客户端")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.username = None
        self.client_socket = None
        self.connected = False
        self.chat_groups = {}  # {group_id: {"name": display_name, "users": [user1, user2]}}
        self.current_group = None

        self.setup_ui()

    def setup_ui(self):
        """初始化UI界面"""
        # 创建主框架
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧面板 - 聊天组列表
        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=1)

        # 连接框架
        connection_frame = ttk.LabelFrame(left_frame, text="连接")
        connection_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(connection_frame, text="服务器:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.server_entry = ttk.Entry(connection_frame)
        self.server_entry.insert(0, "localhost")
        self.server_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        ttk.Label(connection_frame, text="端口:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.port_entry = ttk.Entry(connection_frame)
        self.port_entry.insert(0, "9999")
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        ttk.Label(connection_frame, text="用户名:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(connection_frame)
        self.username_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        self.connect_button = ttk.Button(connection_frame, text="连接", command=self.connect_to_server)
        self.connect_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # 聊天组列表框架
        groups_frame = ttk.LabelFrame(left_frame, text="聊天列表")
        groups_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.groups_tree = ttk.Treeview(groups_frame, columns=("users",), show="tree")
        self.groups_tree.heading("#0", text="聊天")
        self.groups_tree.heading("users", text="参与者")
        self.groups_tree.column("#0", width=120)
        self.groups_tree.column("users", width=180)
        self.groups_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.groups_tree.bind("<<TreeviewSelect>>", self.on_group_selected)

        # 新建聊天按钮
        self.new_chat_button = ttk.Button(groups_frame, text="新建聊天", command=self.create_new_chat)
        self.new_chat_button.pack(fill=tk.X, padx=5, pady=5)
        self.new_chat_button.config(state=tk.DISABLED)

        # 右侧面板 - 聊天窗口
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=3)

        # 聊天显示区域
        self.chat_display = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 消息输入区域
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind("<Return>", self.send_message)
        self.message_entry.config(state=tk.DISABLED)

        self.send_button = ttk.Button(input_frame, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5)
        self.send_button.config(state=tk.DISABLED)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("未连接")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def connect_to_server(self):
        """连接到服务器"""
        server = self.server_entry.get()
        port = int(self.port_entry.get())
        self.username = self.username_entry.get()

        if not server or not port or not self.username:
            messagebox.showerror("错误", "请填写服务器、端口和用户名")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server, port))

            # 发送注册信息
            register_info = {
                'type': 'register',
                'username': self.username
            }
            self.client_socket.send(json.dumps(register_info).encode('utf-8'))

            # 接收服务器响应
            response_data = self.client_socket.recv(1024).decode('utf-8')
            response = json.loads(response_data)

            if response.get('status') == 'success':
                self.connected = True
                self.status_var.set(f"已连接: {self.username}")

                # 禁用连接相关控件
                self.server_entry.config(state=tk.DISABLED)
                self.port_entry.config(state=tk.DISABLED)
                self.username_entry.config(state=tk.DISABLED)
                self.connect_button.config(state=tk.DISABLED)

                # 启用聊天相关控件
                self.new_chat_button.config(state=tk.NORMAL)

                # 启动接收消息的线程
                receive_thread = threading.Thread(target=self.receive_messages)
                receive_thread.daemon = True
                receive_thread.start()

                # 启动心跳线程
                heartbeat_thread = threading.Thread(target=self.send_heartbeat)
                heartbeat_thread.daemon = True
                heartbeat_thread.start()

                messagebox.showinfo("连接成功", f"欢迎, {self.username}!")
            else:
                messagebox.showerror("连接失败", response.get('message', '未知错误'))
                self.client_socket.close()
                self.client_socket = None

        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到服务器: {e}")
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None

    def receive_messages(self):
        """接收服务器消息的线程"""
        while self.connected:
            try:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data:
                    # 连接已关闭
                    break

                message = json.loads(data)
                msg_type = message.get('type')

                if msg_type == 'chat_message':
                    # 聊天消息
                    group_id = message.get('group_id')
                    from_user = message.get('from_user')
                    content = message.get('content')

                    # 在聊天窗口显示消息
                    if group_id in self.chat_groups:
                        self.display_message(group_id, from_user, content)

                elif msg_type == 'chat_invitation':
                    # 收到聊天邀请
                    group_id = message.get('group_id')
                    from_user = message.get('from_user')

                    # 添加到聊天组列表
                    self.chat_groups[group_id] = {
                        "name": f"与 {from_user} 的聊天",
                        "users": [self.username, from_user]
                    }

                    # 更新UI
                    self.update_chat_groups()

                    # 提示用户
                    self.root.bell()
                    self.display_system_message(f"{from_user} 邀请您进行聊天")

                elif msg_type == 'create_chat_response':
                    # 创建聊天响应
                    if message.get('status') == 'success':
                        group_id = message.get('group_id')
                        target_user = message.get('target_user')

                        # 添加到聊天组列表
                        self.chat_groups[group_id] = {
                            "name": f"与 {target_user} 的聊天",
                            "users": [self.username, target_user]
                        }

                        # 更新UI
                        self.update_chat_groups()

                        # 自动选择新创建的聊天
                        for item_id in self.groups_tree.get_children():
                            if self.groups_tree.item(item_id, "values")[0] == group_id:
                                self.groups_tree.selection_set(item_id)
                                self.on_group_selected(None)
                                break
                    else:
                        messagebox.showerror("创建聊天失败", message.get('message', '未知错误'))

                elif msg_type == 'user_left' or msg_type == 'user_offline':
                    # 用户离开聊天或离线
                    group_id = message.get('group_id')
                    username = message.get('username')
                    system_message = message.get('message')

                    if group_id in self.chat_groups:
                        if username in self.chat_groups[group_id]["users"]:
                            self.chat_groups[group_id]["users"].remove(username)

                        # 显示系统消息
                        self.display_system_message(system_message, group_id)

                        # 更新UI
                        self.update_chat_groups()

                elif msg_type == 'heartbeat_ack':
                    # 心跳包确认，不做处理
                    pass

                elif msg_type == 'error':
                    # 错误消息
                    error_msg = message.get('message', '未知错误')
                    self.display_system_message(f"错误: {error_msg}")

            except json.JSONDecodeError:
                print("接收到无效的JSON数据")
                continue
            except Exception as e:
                print(f"接收消息时出错: {e}")
                break

        # 连接已断开
        self.display_system_message("与服务器的连接已断开")
        self.connected = False
        self.status_var.set("未连接")

        # 启用连接控件
        self.server_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        self.username_entry.config(state=tk.NORMAL)
        self.connect_button.config(state=tk.NORMAL)

        # 禁用聊天控件
        self.new_chat_button.config(state=tk.DISABLED)
        self.message_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)

    def send_heartbeat(self):
        """定期发送心跳包以保持连接"""
        while self.connected:
            try:
                if self.client_socket:
                    heartbeat = {'type': 'heartbeat'}
                    self.client_socket.send(json.dumps(heartbeat).encode('utf-8'))
                time.sleep(30)  # 每30秒发送一次心跳
            except:
                break

    def update_chat_groups(self):
        """更新聊天组列表"""
        # 清空现有列表
        for item in self.groups_tree.get_children():
            self.groups_tree.delete(item)

        # 添加聊天组
        for group_id, group_info in self.chat_groups.items():
            users_str = ", ".join(user for user in group_info["users"] if user != self.username)
            if not users_str:
                users_str = "只有您"

            self.groups_tree.insert("", tk.END, text=group_info["name"], values=(users_str, group_id))

    def create_new_chat(self):
        """创建新的聊天"""
        if not self.connected:
            return

        target_user = simpledialog.askstring("新建聊天", "请输入要聊天的用户名:")
        if not target_user:
            return

        if target_user == self.username:
            messagebox.showerror("错误", "不能与自己聊天")
            return

        # 发送创建聊天请求
        request = {
            'type': 'create_chat',
            'target_user': target_user
        }
        try:
            self.client_socket.send(json.dumps(request).encode('utf-8'))
        except Exception as e:
            messagebox.showerror("发送错误", f"无法发送请求: {e}")

    def on_group_selected(self, event):
        """选择聊天组时的处理"""
        selected_items = self.groups_tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        group_id = self.groups_tree.item(item_id, "values")[1]
        if group_id in self.chat_groups:
            # 切换当前聊天组
            self.current_group = group_id

            # 清空聊天显示区域
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)

            # 启用消息输入控件
            self.message_entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)

            # 显示系统提示
            chat_name = self.chat_groups[group_id]["name"]
            self.display_system_message(f"已进入 {chat_name}")

    def send_message(self, event=None):
        """发送消息"""
        if not self.connected or not self.current_group:
            return

        message = self.message_entry.get().strip()
        if not message:
            return

        # 构建消息
        chat_message = {
            'type': 'chat_message',
            'group_id': self.current_group,
            'content': message
        }

        try:
            # 发送消息
            self.client_socket.send(json.dumps(chat_message).encode('utf-8'))

            # 在本地显示消息
            self.display_message(self.current_group, self.username, message)

            # 清空输入框
            self.message_entry.delete(0, tk.END)
        except Exception as e:
            self.display_system_message(f"发送消息失败: {e}")

    def display_message(self, group_id, username, content):
        """在聊天窗口显示消息"""
        if self.current_group != group_id:
            # 如果不是当前聊天组，只在树状视图中标记有未读消息
            for item_id in self.groups_tree.get_children():
                item_group_id = self.groups_tree.item(item_id, "values")[1]
                if item_group_id == group_id:
                    current_text = self.groups_tree.item(item_id, "text")
                    if not current_text.endswith(" (有新消息)"):
                        self.groups_tree.item(item_id, text=current_text + " (有新消息)")
                    break
            return

        self.chat_display.config(state=tk.NORMAL)

        # 添加时间戳
        timestamp = time.strftime("%H:%M:%S", time.localtime())

        # 格式化显示
        if username == self.username:
            self.chat_display.insert(tk.END, f"{timestamp} 我: ", "self")
        else:
            self.chat_display.insert(tk.END, f"{timestamp} {username}: ", "other")

        self.chat_display.insert(tk.END, f"{content}\n")
        self.chat_display.see(tk.END)

        self.chat_display.config(state=tk.DISABLED)

    def display_system_message(self, message, group_id=None):
        """显示系统消息"""
        if group_id and self.current_group != group_id:
            return

        self.chat_display.config(state=tk.NORMAL)

        # 添加时间戳
        timestamp = time.strftime("%H:%M:%S", time.localtime())

        # 格式化显示
        self.chat_display.insert(tk.END, f"{timestamp} 系统: {message}\n", "system")
        self.chat_display.see(tk.END)

        self.chat_display.config(state=tk.DISABLED)

    def on_closing(self):
        """窗口关闭时的处理"""
        if self.connected:
            # 断开与服务器的连接
            try:
                # 给每个聊天组发送离开消息
                for group_id in self.chat_groups:
                    leave_message = {
                        'type': 'leave_chat',
                        'group_id': group_id
                    }
                    self.client_socket.send(json.dumps(leave_message).encode('utf-8'))

                # 关闭套接字
                self.client_socket.close()
            except:
                pass

            self.connected = False

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()