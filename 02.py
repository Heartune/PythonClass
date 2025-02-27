import numpy as np
N = int(input("请输入元素的个数:"))
M = int(input("请输入取出数字的个数:"))

random_list = np.random.randint(1, 2**31, size=N)

selected_numbers = np.random.choice(random_list, size=M, replace=False)

sorted_numbers = np.sort(selected_numbers)

print(sorted_numbers)
