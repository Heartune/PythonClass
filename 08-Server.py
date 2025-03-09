import socket
import threading
import json
import time
from collections import defaultdict


class ChatServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)  # 支持多个客户端同时连接

        # 客户端连接信息
        self.clients = {}  # {username: (client_socket, client_address)}

        # 聊天组信息
        self.chat_groups = defaultdict(set)  # {group_id: {username1, username2}}
        self.user_groups = defaultdict(set)  # {username: {group_id1, group_id2}}

        # 生成组ID的计数器
        self.group_counter = 0

        print(f"聊天服务器已启动，监听地址：{self.host}:{self.port}")

    def generate_group_id(self):
        """生成唯一的聊天组ID"""
        self.group_counter += 1
        return f"group_{self.group_counter}"

    def broadcast_to_group(self, group_id, message, sender=None):
        """向组内所有用户广播消息"""
        for username in self.chat_groups[group_id]:
            if username != sender:  # 不需要给发送者自己发送消息
                try:
                    client_socket = self.clients[username][0]
                    client_socket.send(message.encode('utf-8'))
                except Exception as e:
                    print(f"向{username}发送消息失败: {e}")

    def handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        try:
            # 1. 接收客户端注册信息
            register_data = client_socket.recv(1024).decode('utf-8')
            register_info = json.loads(register_data)
            username = register_info.get('username')

            if not username or username in self.clients:
                # 用户名为空或已存在
                response = {
                    'type': 'register_response',
                    'status': 'error',
                    'message': '用户名为空或已被使用'
                }
                client_socket.send(json.dumps(response).encode('utf-8'))
                client_socket.close()
                return

            # 注册成功
            self.clients[username] = (client_socket, client_address)
            response = {
                'type': 'register_response',
                'status': 'success',
                'message': f'欢迎 {username}!'
            }
            client_socket.send(json.dumps(response).encode('utf-8'))

            print(f"用户 {username} ({client_address}) 已连接")

            # 2. 处理客户端消息
            while True:
                try:
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        break

                    message = json.loads(data)
                    msg_type = message.get('type')

                    if msg_type == 'create_chat':
                        # 创建新的聊天请求
                        target_user = message.get('target_user')
                        if target_user not in self.clients:
                            response = {
                                'type': 'create_chat_response',
                                'status': 'error',
                                'message': f'用户 {target_user} 不存在或不在线'
                            }
                            client_socket.send(json.dumps(response).encode('utf-8'))
                        else:
                            # 创建新的聊天组
                            group_id = self.generate_group_id()
                            self.chat_groups[group_id] = {username, target_user}
                            self.user_groups[username].add(group_id)
                            self.user_groups[target_user].add(group_id)

                            # 通知发起者
                            initiator_response = {
                                'type': 'create_chat_response',
                                'status': 'success',
                                'group_id': group_id,
                                'target_user': target_user,
                                'message': f'与 {target_user} 的聊天已创建'
                            }
                            client_socket.send(json.dumps(initiator_response).encode('utf-8'))

                            # 通知目标用户
                            target_response = {
                                'type': 'chat_invitation',
                                'group_id': group_id,
                                'from_user': username,
                                'message': f'{username} 想与您聊天'
                            }
                            target_socket = self.clients[target_user][0]
                            target_socket.send(json.dumps(target_response).encode('utf-8'))

                    elif msg_type == 'chat_message':
                        # 发送聊天消息
                        group_id = message.get('group_id')
                        content = message.get('content')

                        if group_id not in self.chat_groups:
                            response = {
                                'type': 'error',
                                'message': '聊天组不存在'
                            }
                            client_socket.send(json.dumps(response).encode('utf-8'))
                        else:
                            # 构建消息并广播
                            broadcast_message = {
                                'type': 'chat_message',
                                'group_id': group_id,
                                'from_user': username,
                                'content': content,
                                'timestamp': time.time()
                            }
                            self.broadcast_to_group(group_id, json.dumps(broadcast_message), username)

                    elif msg_type == 'leave_chat':
                        # 离开聊天组
                        group_id = message.get('group_id')
                        if group_id in self.chat_groups and username in self.chat_groups[group_id]:
                            self.chat_groups[group_id].remove(username)
                            self.user_groups[username].remove(group_id)

                            # 如果组内没有用户了，删除该组
                            if not self.chat_groups[group_id]:
                                del self.chat_groups[group_id]
                            else:
                                # 通知组内其他用户
                                notify_message = {
                                    'type': 'user_left',
                                    'group_id': group_id,
                                    'username': username,
                                    'message': f'{username} 已离开聊天'
                                }
                                self.broadcast_to_group(group_id, json.dumps(notify_message))

                    elif msg_type == 'heartbeat':
                        # 心跳包，保持连接
                        response = {'type': 'heartbeat_ack'}
                        client_socket.send(json.dumps(response).encode('utf-8'))

                except json.JSONDecodeError:
                    print(f"从客户端 {username} 接收到无效JSON数据")
                    continue
                except Exception as e:
                    print(f"处理客户端 {username} 消息时出错: {e}")
                    break

        except Exception as e:
            print(f"处理客户端连接时出错: {e}")
        finally:
            # 清理用户资源
            if username in self.clients:
                # 通知所有聊天组该用户已离线
                for group_id in list(self.user_groups[username]):
                    if group_id in self.chat_groups:
                        self.chat_groups[group_id].remove(username)

                        # 如果组内没有用户了，删除该组
                        if not self.chat_groups[group_id]:
                            del self.chat_groups[group_id]
                        else:
                            # 通知组内其他用户
                            notify_message = {
                                'type': 'user_offline',
                                'group_id': group_id,
                                'username': username,
                                'message': f'{username} 已离线'
                            }
                            self.broadcast_to_group(group_id, json.dumps(notify_message))

                # 移除用户信息
                del self.clients[username]
                del self.user_groups[username]

                print(f"用户 {username} 已断开连接")

            try:
                client_socket.close()
            except:
                pass

    def run(self):
        """运行服务器"""
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("服务器正在关闭...")
        finally:
            self.server_socket.close()
            print("服务器已关闭")


if __name__ == "__main__":
    server = ChatServer()
    server.run()