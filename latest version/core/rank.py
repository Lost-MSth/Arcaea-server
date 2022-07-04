from .user import UserInfo
from .song import Chart
from .score import UserScore
from .constant import Constant


class RankList:
    '''
        排行榜类\ 
        默认limit=20，limit<0认为是all\ 
        property: `user` - `User`类或者子类的实例
    '''

    def __init__(self, c=None) -> None:
        self.c = c
        self.list: list = []
        self.song = Chart()
        self.limit: int = 20
        self.user = None

    @property
    def to_dict_list(self) -> list:
        return [x.to_dict for x in self.list]

    def select_top(self) -> None:
        '''
            得到top分数表
        '''
        if self.limit >= 0:
            self.c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit''', {
                'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'limit': self.limit})
        else:
            self.c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC''', {
                'song_id': self.song.song_id, 'difficulty': self.song.difficulty})

        x = self.c.fetchall()
        if not x:
            return None

        rank = 0
        self.list = []
        for i in x:
            rank += 1
            y = UserScore(self.c, UserInfo(self.c, i[0]))
            y.song = self.song
            y.select_score()
            y.rank = rank
            self.list.append(y)

    def select_friend(self, user=None, limit=Constant.MAX_FRIEND_COUNT) -> None:
        '''
            得到用户好友分数表
        '''
        self.limit = limit
        if user:
            self.user = user

        self.c.execute('''select user_id from best_score where user_id in (select :user_id union select user_id_other from friend where user_id_me = :user_id) and song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit''', {
            'user_id': self.user.user_id, 'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'limit': self.limit})
        x = self.c.fetchall()
        if not x:
            return None

        rank = 0
        self.list = []
        for i in x:
            rank += 1
            y = UserScore(self.c, UserInfo(self.c, i[0]))
            y.song = self.song
            y.select_score()
            y.rank = rank
            self.list.append(y)

    def select_me(self, user=None) -> None:
        '''
            得到我的排名分数表\ 
            尚不清楚这个函数有没有问题
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
        x = self.c.fetchone()
        myrank = int(x[0]) + 1
        self.c.execute('''select count(*) from best_score where song_id=:a and difficulty=:b''',
                       {'a': self.song.song_id, 'b': self.song.difficulty})
        amount = int(self.c.fetchone()[0])

        if myrank <= 4:  # 排名在前4
            self.select_top()
        elif myrank >= 5 and myrank <= 9999 - self.limit + 4 and amount >= 10000:  # 万名内，前面有4个人
            self.c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
                'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'limit': self.limit, 'offset': myrank - 5})
            x = self.c.fetchall()
            if x:
                rank = myrank - 5
                self.list = []
                for i in x:
                    rank += 1
                    y = UserScore(self.c, UserInfo(self.c, i[0]))
                    y.song = self.song
                    y.select_score()
                    y.rank = rank
                    self.list.append(y)

        elif myrank >= 10000:  # 万名外
            self.c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
                'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'limit': self.limit - 1, 'offset': 9999-self.limit})
            x = self.c.fetchall()
            if x:
                rank = 9999 - self.limit
                for i in x:
                    rank += 1
                    y = UserScore(self.c, UserInfo(self.c, i[0]))
                    y.song = self.song
                    y.select_score()
                    y.rank = rank
                    self.list.append(y)
                y = UserScore(self.c, UserInfo(self.c, self.user.user_id))
                y.song = self.song
                y.rank = -1
                self.list.append(y)

        elif amount - myrank < self.limit - 5:  # 后方人数不足
            self.c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
                'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'limit': self.limit, 'offset': amount - self.limit})
            x = self.c.fetchall()
            if x:
                rank = amount - self.limit
                if rank < 0:
                    rank = 0
                for i in x:
                    rank += 1
                    y = UserScore(self.c, UserInfo(self.c, i[0]))
                    y.song = self.song
                    y.select_score()
                    y.rank = rank
                    self.list.append(y)

        else:
            self.c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
                'song_id': self.song.song_id, 'difficulty': self.song.difficulty, 'limit': self.limit, 'offset': 9998-self.limit})
            x = self.c.fetchall()
            if x:
                rank = 9998 - self.limit
                for i in x:
                    rank += 1
                    y = UserScore(self.c, UserInfo(self.c, i[0]))
                    y.song = self.song
                    y.select_score()
                    y.rank = rank
                    self.list.append(y)
