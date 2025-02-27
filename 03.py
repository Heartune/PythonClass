result = []
while True:
    sentence = input()

    if not sentence:
        break

    words = sentence.split()
    words = words[::-1]
    new_sentence = ' '.join(words)

    result.append(new_sentence)

for sentence in result:
    print(sentence)
