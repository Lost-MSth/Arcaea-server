from .download import DownloadList
from .error import NoData
from .save import SaveData
from .score import Score
from .sql import Connect, Sql
from .user import User


class BaseOperation:
    _name: str = None

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs) -> None:
        return self.run(*args, **kwargs)

    def set_params(self, *args, **kwargs) -> None:
        pass

    def run(self, *args, **kwargs) -> None:
        raise NotImplementedError


class RefreshAllScoreRating(BaseOperation):
    '''
        刷新所有成绩的评分
    '''
    _name = 'refresh_all_score_rating'

    def run(self):
        # 追求效率，不用Song类，尽量不用对象
        # 但其实还是很慢
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
                        ptt = max(ptt, 0)
                        values.append((ptt,))
                        where_values.append((k[0], i[0], j))
                    if values:
                        Sql(c).update_many('best_score', ['rating'], values, [
                            'user_id', 'song_id', 'difficulty'], where_values)


class RefreshSongFileCache(BaseOperation):
    '''
        刷新歌曲文件缓存，包括文件hash缓存重建、文件目录重遍历、songlist重解析
        注意在设置里预先计算关闭的情况下，文件hash不会计算
    '''
    _name = 'refresh_song_file_cache'

    def run(self):
        DownloadList.clear_all_cache()
        DownloadList.initialize_cache()


class SaveUpdateScore(BaseOperation):
    '''
        云存档更新成绩，是覆盖式更新
        提供user参数时，只更新该用户的成绩，否则更新所有用户的成绩
    '''
    _name = 'save_update_score'

    def __init__(self, user=None):
        self.user = user

    def set_params(self, user_id: int = None, *args, **kwargs):
        if user_id is not None:
            self.user = User()
            self.user.user_id = int(user_id)

    def run(self, user=None):
        '''
        parameter:
            `user` - `User`类或子类的实例
        '''
        if user is not None:
            self.user = user
        if self.user is not None and self.user.user_id is not None:
            self._one_user_update()
        else:
            self._all_update()

    def _one_user_update(self):
        with Connect() as c:
            save = SaveData(c)
            save.select_scores(self.user)

            clear_state = {f'{i["song_id"]}{i["difficulty"]}': i['clear_type']
                           for i in save.clearlamps_data}

            song_id_1 = [i['song_id'] for i in save.scores_data]
            song_id_2 = [i['song_id'] for i in save.clearlamps_data]
            song_id = list(set(song_id_1 + song_id_2))

            c.execute(
                f'''select song_id, rating_pst, rating_prs, rating_ftr, rating_byn from chart where song_id in ({','.join(['?']*len(song_id))})''', song_id)
            x = c.fetchall()
            song_chart_const = {i[0]: [i[1], i[2], i[3], i[4]]
                                for i in x}  # chart const * 10

            new_scores = []
            for i in save.scores_data:
                rating = 0
                if i['song_id'] in song_chart_const:
                    rating = Score.calculate_rating(
                        song_chart_const[i['song_id']][i['difficulty']] / 10, i['score'])
                    rating = max(rating, 0)

                y = f'{i["song_id"]}{i["difficulty"]}'
                if y in clear_state:
                    clear_type = clear_state[y]
                else:
                    clear_type = 0

                new_scores.append((self.user.user_id, i['song_id'], i['difficulty'], i['score'], i['shiny_perfect_count'], i['perfect_count'],
                                   i['near_count'], i['miss_count'], i['health'], i['modifier'], i['time_played'], clear_type, clear_type, rating))

            c.executemany(
                '''insert or replace into best_score values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', new_scores)

    def _all_update(self):
        with Connect() as c:
            c.execute(
                '''select song_id, rating_pst, rating_prs, rating_ftr, rating_byn from chart''')
            song_chart_const = {i[0]: [i[1], i[2], i[3], i[4]]
                                for i in c.fetchall()}  # chart const * 10
            c.execute('''select user_id from user_save''')
            for y in c.fetchall():
                user = User()
                user.user_id = y[0]
                save = SaveData(c)
                save.select_scores(user)

                clear_state = {f'{i["song_id"]}{i["difficulty"]}': i['clear_type']
                               for i in save.clearlamps_data}

                new_scores = []
                for i in save.scores_data:
                    rating = 0
                    if i['song_id'] in song_chart_const:
                        rating = Score.calculate_rating(
                            song_chart_const[i['song_id']][i['difficulty']] / 10, i['score'])
                        rating = max(rating, 0)

                    y = f'{i["song_id"]}{i["difficulty"]}'
                    if y in clear_state:
                        clear_type = clear_state[y]
                    else:
                        clear_type = 0

                    new_scores.append((user.user_id, i['song_id'], i['difficulty'], i['score'], i['shiny_perfect_count'], i['perfect_count'],
                                       i['near_count'], i['miss_count'], i['health'], i['modifier'], i['time_played'], clear_type, clear_type, rating))

                c.executemany(
                    '''insert or replace into best_score values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', new_scores)


class UnlockUserItem(BaseOperation):
    '''
        全解锁/锁定用户物品
        提供user参数时，只更新该用户的，否则更新所有用户的
    '''
    _name = 'unlock_user_item'

    ALLOW_TYPES = ['single', 'pack', 'world_song',
                   'course_banner', 'world_unlock']

    def __init__(self, user=None, method: str = 'unlock', item_types: list = ['single', 'pack']):
        self.user = user
        self.set_params(method=method, item_types=item_types)

    def set_params(self, user_id: int = None, method: str = 'unlock', item_types: list = ['single', 'pack'], *args, **kwargs):
        if user_id is not None:
            self.user = User()
            self.user.user_id = int(user_id)
        if method in ['unlock', 'lock']:
            self.method = method
        if isinstance(item_types, list) and all(i in self.ALLOW_TYPES for i in item_types):
            self.item_types = item_types

    def run(self):
        if self.user is not None and self.user.user_id is not None:
            if self.method == 'unlock':
                self._one_user_insert()
            else:
                self._one_user_delete()
        else:
            if self.method == 'unlock':
                self._all_insert()
            else:
                self._all_delete()

    def _one_user_insert(self):
        with Connect() as c:
            c.execute(
                '''select exists(select * from user where user_id = ?)''', (self.user.user_id,))
            if not c.fetchone()[0]:
                raise NoData(
                    f'No such user: `{self.user.user_id}`', api_error_code=-110)
            c.execute(
                f'''select item_id, type from item where type in ({','.join(['?'] * len(self.item_types))})''', self.item_types)
            sql_list = [(self.user.user_id, i[0], i[1])
                        for i in c.fetchall()]
            c.executemany(
                '''insert or ignore into user_item values (?, ?, ?, 1)''', sql_list)

    def _all_insert(self):
        with Connect() as c:
            c.execute('''select user_id from user''')
            x = c.fetchall()
            c.execute(
                f'''select item_id, type from item where type in ({','.join(['?'] * len(self.item_types))})''', self.item_types)
            y = c.fetchall()
            sql_list = [(i[0], j[0], j[1])
                        for i in x for j in y]
            c.executemany(
                '''insert or ignore into user_item values (?, ?, ?, 1)''', sql_list)

    def _one_user_delete(self):
        with Connect() as c:
            c.execute(
                f'''delete from user_item where user_id = ? and type in ({','.join(['?'] * len(self.item_types))})''', (self.user.user_id, *self.item_types))

    def _all_delete(self):
        with Connect() as c:
            c.execute(
                f'''delete from user_item where type in ({','.join(['?'] * len(self.item_types))})''', self.item_types)
