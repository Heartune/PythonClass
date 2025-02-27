def is_palindrome(num):
    num_str = str(num)

    length = len(num_str)

    for i in range(length//2):
        if num_str[i] != num_str[length-i-1]:
            return False
    return True


def find_palindromes(start, end):
    palindromes = []

    for num in range(start, end+1):
        if is_palindrome(num):
            palindromes.append(num)

        if len(palindromes) >= 10:
            break

    return palindromes


start = int(input("请输入起始数字:"))
end = int(input("请输入终止数字:"))

result = find_palindromes(start, end)

print(result)
