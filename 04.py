users = {}


def register():
    while True:
        username = input("请输入用户名:")
        if username in users:
            print("用户名已存在，请重新输入:")
            continue

        password = input("请输入密码:")
        users[username] = password
        print("注册成功!")
        break


def login():
    username = input("请输入用户名:")
    password = input("请输入密码:")

    if username not in users:
        print("用户名不存在!")
        return False

    if users[username] != password:
        print("密码错误!")
        return False

    else:
        print("登录成功!")
        return True


def main():
    while True:
        print("1. 注册")
        print("2. 登录")
        print("3. 退出")

        choice = input("请选择操作:")

        if choice == '1':
            register()
        elif choice == '2':
            login()
        elif choice == '3':
            break
        else:
            print("输入有误,请重新输入!")


main()
