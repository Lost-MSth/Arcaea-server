from .sql import Connect, Sql
from .score import Score


class BaseOperation:
    name: str = None

    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        raise NotImplementedError


class RefreshAllScoreRating(BaseOperation):
    '''
        刷新所有成绩的评分
    '''
    name = 'refresh_all_score_rating'

    def run(self):
        # 追求效率，不用Song类，尽量不用对象
        with Connect() as c:
            c.execute(
                '''select song_id, rating_pst, rating_prs, rating_ftr, rating_byn from chart''')
            x = c.fetchall()

            songs = [i[0] for i in x]
            c.execute(
                f'''update best_score set rating=0 where song_id not in ({','.join(['?']*len(songs))})''', songs)

            for i in x:
                for j in range(0, 4):
                    defnum = -10  # 没在库里的全部当做定数-10
                    if i[j+1] is not None and i[j+1] > 0:
                        defnum = float(i[j+1]) / 10

                    c.execute('''select user_id, score from best_score where song_id=:a and difficulty=:b''', {
                              'a': i[0], 'b': j})
                    y = c.fetchall()
                    values = []
                    where_values = []
                    for k in y:
                        ptt = Score.calculate_rating(defnum, k[1])
                        if ptt < 0:
                            ptt = 0
                        values.append((ptt,))
                        where_values.append((k[0], i[0], j))
                    if values:
                        Sql(c).update_many('best_score', ['rating'], values, [
                            'user_id', 'song_id', 'difficulty'], where_values)
