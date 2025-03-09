import random
import time


class Animal:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, max_step, boundary):
        # 随机选择移动方向：x轴或y轴
        axis = random.choice(['x', 'y'])

        # 随机选择移动步数，对于狼是1或2，对于羊是1
        steps = random.randint(1, max_step)

        # 随机选择移动方向：正方向或负方向
        direction = random.choice([1, -1])

        # 进行移动
        if axis == 'x':
            new_x = self.x + steps * direction
            # 检查边界，如果超出边界则反向移动
            if new_x < 0 or new_x >= boundary[0]:
                new_x = self.x - steps * direction
            self.x = new_x
        else:  # axis == 'y'
            new_y = self.y + steps * direction
            # 检查边界，如果超出边界则反向移动
            if new_y < 0 or new_y >= boundary[1]:
                new_y = self.y - steps * direction
            self.y = new_y

        return steps  # 返回实际移动的步数


class Wolf(Animal):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.energy = 100  # 初始体力为100


class Sheep(Animal):
    def __init__(self, x, y):
        super().__init__(x, y)


class Game:
    def __init__(self):
        self.boundary = (10, 10)  # 游戏场景范围：0≤x≤9,0≤y≤9
        self.wolf = None
        self.sheep_list = []
        self.round = 0

    def initialize(self):
        """初始化游戏，生成1只狼和10只羊"""
        # 生成狼
        wolf_x = random.randint(0, self.boundary[0] - 1)
        wolf_y = random.randint(0, self.boundary[1] - 1)
        self.wolf = Wolf(wolf_x, wolf_y)

        # 生成10只羊
        for _ in range(10):
            sheep_x = random.randint(0, self.boundary[0] - 1)
            sheep_y = random.randint(0, self.boundary[1] - 1)
            self.sheep_list.append(Sheep(sheep_x, sheep_y))

        print("游戏初始化完成！")
        print(f"狼的初始位置: ({self.wolf.x}, {self.wolf.y}), 体力: {self.wolf.energy}")
        for i, sheep in enumerate(self.sheep_list):
            print(f"羊{i + 1}的初始位置: ({sheep.x}, {sheep.y})")
        print("-" * 50)

    def play_round(self):
        """进行一轮游戏"""
        self.round += 1
        print(f"\n第{self.round}轮游戏开始")

        # 狼移动
        steps = self.wolf.move(2, self.boundary)
        self.wolf.energy -= steps  # 体力消耗与移动步数相等
        print(f"狼移动到位置: ({self.wolf.x}, {self.wolf.y}), 消耗体力: {steps}, 剩余体力: {self.wolf.energy}")

        # 如果狼体力为0，游戏结束
        if self.wolf.energy <= 0:
            print("狼的体力耗尽，游戏结束！")
            return False

        # 羊移动
        for i, sheep in enumerate(self.sheep_list):
            sheep.move(1, self.boundary)
            print(f"羊{i + 1}移动到位置: ({sheep.x}, {sheep.y})")

        # 检查狼是否能吃到羊
        sheep_eaten = []
        for i, sheep in enumerate(self.sheep_list):
            if self.wolf.x == sheep.x and self.wolf.y == sheep.y:
                sheep_eaten.append(i)
                self.wolf.energy += 20
                print(f"狼吃掉了羊{i + 1}，体力增加20，当前体力: {self.wolf.energy}")

        # 从后往前删除被吃掉的羊，避免索引错误
        for i in sorted(sheep_eaten, reverse=True):
            del self.sheep_list[i]

        # 如果所有羊都被吃掉，游戏结束
        if not self.sheep_list:
            print("所有的羊都被吃掉了，狼获胜！游戏结束！")
            return False

        # 输出剩余羊的数量
        print(f"剩余羊的数量: {len(self.sheep_list)}")

        return True

    def play(self):
        """进行游戏主循环"""
        self.initialize()

        while True:
            continue_game = self.play_round()
            if not continue_game:
                break
            time.sleep(0.5)  # 添加一些延迟，使输出更易于阅读

        # 游戏结束，显示结果
        print("\n游戏结束！")
        print(f"总回合数: {self.round}")
        print(f"狼剩余体力: {self.wolf.energy}")
        print(f"剩余羊的数量: {len(self.sheep_list)}")


# 运行游戏
if __name__ == "__main__":
    game = Game()
    game.play()