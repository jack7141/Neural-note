import string


def base26_add(num1, num2):
    digits = string.ascii_uppercase
    limit = len(digits)

    # 숫자를 리스트로 변환 (역순으로 계산하기 쉽게)
    num1 = list(num1[::-1])
    num2 = list(num2[::-1])

    # 결과를 저장할 리스트
    result = []
    carry = 0
    max_len = max(len(num1), len(num2))

    for i in range(max_len):
        # num1과 num2의 해당 자리가 존재하지 않으면 0으로 취급
        digit1 = digits.index(num1[i]) if i < len(num1) else 0
        digit2 = digits.index(num2[i]) if i < len(num2) else 0

        # 두 자릿수 더하기 + carry
        total = digit1 + digit2 + carry

        # 현재 자릿수 값과 carry 값 계산
        result.append(digits[total % limit])
        carry = total // limit

    # 마지막 carry가 남아있으면 추가
    if carry:
        result.append(digits[carry])

    # 결과를 다시 역순으로 뒤집어서 반환
    return result[::-1]


def next_code(before):
    c = list(before)
    c.reverse()
    n_arr = list()
    carry = 'B'
    for i, v in enumerate(c):
        _sum = base26_add(carry, v)
        if len(_sum) > 1:
            carry = _sum.pop(0)
            pass
        else:
            carry = 'A'
            pass
        n_arr.append(_sum[-1])
        if carry == 'B' and i == len(c) - 1:
            n_arr.append('A')
            pass

    n_arr.reverse()
    return ''.join(n_arr)
