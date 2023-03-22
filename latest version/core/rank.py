from .constant import Constant
from .score import UserScore
from .song import Chart
from .sql import Query, Sql
from .user import UserInfo


class RankList:
    '''
        排行榜类
        默认limit=20，limit<0认为是all

        property: `user` - `User`类或者子类的实例
    '''

    def __init__(self, c=None) -> None:
        self.c = c
        self.list: list = []
        self.song = Chart()
        self.limit: int = 20
        self.user = None

    def to_dict_list(self) -> list:
        return [x.to_dict() for x in self.list]

    def select_top(self) -> None:
        '''
            得到top分数表
        '''
        if self.limit >= 0:
            self.c.execute('''select * from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit''', {
                'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'limit': self.limit})
        else:
            self.c.execute('''select * from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC''', {
                'song_id': self.song.song_id, 'difficulty': self.song.difficulty})

        x = self.c.fetchall()
        if not x:
            return None

        user_info_list = Sql(self.c).select('user', ['user_id', 'name', 'character_id', 'is_skill_sealed', 'is_char_uncapped',
                                                     'is_char_uncapped_override', 'favorite_character'], Query().from_args({'user_id': [i[0] for i in x]}))
        user_info_dict = {i[0]: i[1:] for i in user_info_list}

        rank = 0
        self.list = []
        for i in x:
            rank += 1
            y = UserScore(self.c, UserInfo(self.c, i[0])).from_list(i)
            y.song = self.song
            y.rank = rank
            y.user.from_list_about_character(user_info_dict[i[0]])

            self.list.append(y)

    def select_friend(self, user=None, limit=Constant.MAX_FRIEND_COUNT) -> None:
        '''
            得到用户好友分数表
        '''
        self.limit = limit
        if user:
            self.user = user

        user_ids = [self.user.user_id] + [x[0] for x in self.user.friend_ids]

        self.c.execute(f'''select * from best_score where user_id in ({','.join(['?'] * len(user_ids))}) and song_id = ? and difficulty = ? order by score DESC, time_played DESC limit ?''', user_ids + [
                       self.song.song_id, self.song.difficulty, self.limit])
        x = self.c.fetchall()
        if not x:
            return None

        user_info_list = Sql(self.c).select('user', ['user_id', 'name', 'character_id', 'is_skill_sealed', 'is_char_uncapped',
                                                     'is_char_uncapped_override', 'favorite_character'], Query().from_args({'user_id': [i[0] for i in x]}))
        user_info_dict = {i[0]: i[1:] for i in user_info_list}
        rank = 0
        self.list = []
        for i in x:
            rank += 1
            y = UserScore(self.c, UserInfo(self.c, i[0])).from_list(i)
            y.song = self.song
            y.rank = rank
            y.user.from_list_about_character(user_info_dict[i[0]])

            self.list.append(y)

    @staticmethod
    def get_my_rank_parameter(my_rank: int, amount: int, all_limit: int = 20, max_local_position: int = Constant.MY_RANK_MAX_LOCAL_POSITION, max_global_position: int = Constant.MY_RANK_MAX_GLOBAL_POSITION):
        '''
            计算我的排名中的查询参数

            returns:
            `sql_limit`: int - 查询limit参数
            `sql_offset`: int - 查询offset参数
            `need_myself`: bool - 是否需要在排名结尾添加自己
        '''
        sql_limit = all_limit
        sql_offset = 0
        need_myself = False

        if my_rank <= max_local_position:  # 排名在前面，前方人数不足
            pass
        elif my_rank > max_global_position:  # 排名太后了，不显示排名
            sql_limit -= 1
            sql_offset = max_global_position - all_limit + 1
            need_myself = True
        elif amount - my_rank < all_limit - max_local_position:  # 后方人数不足，显示排名
            sql_offset = amount - all_limit
        elif max_local_position <= my_rank <= max_global_position - all_limit + max_local_position - 1:  # 前方人数足够，显示排名
            sql_offset = my_rank - max_local_position
        else:  # 我已经忘了这是什么了
            sql_offset = max_global_position - all_limit

        return sql_limit, sql_offset, need_myself

    def select_me(self, user=None) -> None:
        '''
            得到我的排名分数表
        '''
        if user:
            self.user = user
        self.c.execute('''select score, time_played from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty''', {
            'user_id': self.user.user_id, 'song_id': self.song.song_id, 'difficulty': self.song.difficulty})
        x = self.c.fetchone()
        if not x:
            return None

        self.c.execute('''select count(*) from best_score where song_id = :song_id and difficulty = :difficulty and ( score > :score or (score = :score and time_played > :time_played) )''', {
            'user_id': self.user.user_id, 'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'score': x[0], 'time_played': x[1]})
        my_rank = int(self.c.fetchone()[0]) + 1
        self.c.execute('''select count(*) from best_score where song_id=:a and difficulty=:b''',
                       {'a': self.song.song_id, 'b': self.song.difficulty})

        sql_limit, sql_offset, need_myself = self.get_my_rank_parameter(
            my_rank, int(self.c.fetchone()[0]), self.limit)
        self.c.execute('''select * from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
            'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'limit': sql_limit, 'offset': sql_offset})
        x = self.c.fetchall()

        if x:
            user_info_list = Sql(self.c).select('user', ['user_id', 'name', 'character_id', 'is_skill_sealed', 'is_char_uncapped',
                                                         'is_char_uncapped_override', 'favorite_character'], Query().from_args({'user_id': [i[0] for i in x]}))
            user_info_dict = {i[0]: i[1:] for i in user_info_list}
            rank = sql_offset if sql_offset > 0 else 0
            self.list = []
            for i in x:
                rank += 1
                y = UserScore(self.c, UserInfo(self.c, i[0])).from_list(i)
                y.song = self.song
                y.rank = rank
                y.user.from_list_about_character(user_info_dict[i[0]])

                self.list.append(y)

            if need_myself:
                y = UserScore(self.c, UserInfo(self.c, self.user.user_id))
                y.song = self.song
                y.select_score()
                y.rank = -1
                self.list.append(y)
