

def buy_item(c, user_id, price):
    # 购买接口，返回成功与否标识符和剩余源点数
    c.execute('''select ticket from user where user_id = :a''',
              {'a': user_id})
    ticket = c.fetchone()
    if ticket:
        ticket = ticket[0]
    else:
        ticket = 0

    if ticket < price:
        return False, ticket

    c.execute('''update user set ticket = :b where user_id = :a''',
              {'a': user_id, 'b': ticket-price})

    return True, ticket - price




