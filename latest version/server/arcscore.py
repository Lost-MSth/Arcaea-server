from core.sql import Connect


def calculate_rating(defnum, score):
    # 计算rating
    if score >= 10000000:
        ptt = defnum + 2
    elif score < 9800000:
        ptt = defnum + (score-9500000) / 300000
        if ptt < 0 and defnum != -10:
            ptt = 0
    else:
        ptt = defnum + 1 + (score-9800000) / 200000

    return ptt


def refresh_all_score_rating():
    # 刷新所有best成绩的rating
    error = 'Unknown error.'

    with Connect() as c:
        c.execute(
            '''select song_id, rating_pst, rating_prs, rating_ftr, rating_byn from chart''')
        x = c.fetchall()

    if x:
        song_list = [i[0] for i in x]
        with Connect() as c:
            c.execute('''update best_score set rating=0 where song_id not in ({0})'''.format(
                ','.join(['?']*len(song_list))), tuple(song_list))
            for i in x:
                for j in range(0, 4):
                    defnum = -10  # 没在库里的全部当做定数-10
                    if i is not None:
                        defnum = float(i[j+1]) / 10
                        if defnum <= 0:
                            defnum = -10  # 缺少难度的当做定数-10

                    c.execute('''select user_id, score from best_score where song_id=:a and difficulty=:b''', {
                              'a': i[0], 'b': j})
                    y = c.fetchall()
                    if y:
                        for k in y:
                            ptt = calculate_rating(defnum, k[1])
                            if ptt < 0:
                                ptt = 0

                            c.execute('''update best_score set rating=:a where user_id=:b and song_id=:c and difficulty=:d''', {
                                      'a': ptt, 'b': k[0], 'c': i[0], 'd': j})
            error = None

    else:
        error = 'No song data.'

    return error
