def main():
    start = int(input("请输入下界:"))
    end = int(input("请输入上界:"))
    num_lists = list(range(start, end+1))
    even_lists = list(filter(lambda x: x > 0 and x % 2 == 0, num_lists))
    result = sum(even_lists)
    print(result)


main()
