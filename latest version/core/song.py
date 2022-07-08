from .error import NoData


class Chart:
    # defnum: chart const * 10

    def __init__(self, c=None, song_id: str = None, difficulty: int = None) -> None:
        self.c = c
        self.set_chart(song_id, difficulty)
        self.defnum: int = None

    def to_dict(self) -> dict:
        return {
            'difficulty': self.difficulty,
            'chart_const': self.chart_const
        }

    @property
    def chart_const(self) -> float:
        return self.defnum / 10 if self.defnum else -1

    @property
    def song_id_difficulty(self) -> str:
        return '%s%d' % (self.song_id, self.difficulty)

    def set_chart(self, song_id: str = None, difficulty: int = None) -> None:
        self.song_id = song_id
        self.difficulty = int(difficulty) if difficulty is not None else None

    def select(self) -> None:
        self.c.execute(
            '''select rating_pst, rating_prs, rating_ftr, rating_byn from chart where song_id=:a''', {'a': self.song_id})
        x = self.c.fetchone()
        if x is None:
            self.defnum = -10
            # raise NoData('The song `%s` does not exist.' % self.song_id)
        else:
            self.defnum = x[self.difficulty]


class Song:
    def __init__(self, c=None, song_id=None) -> None:
        self.c = c
        self.song_id: str = song_id
        self.name: str = None
        self.charts: dict = None

    def to_dict(self) -> dict:
        return {
            'song_id': self.song_id,
            'name': self.name,
            'charts': [chart.to_dict() for chart in self.charts]
        }

    def from_list(self, x: list) -> 'Song':
        if self.song_id is None:
            self.song_id = x[0]
        self.name = x[1]
        self.charts = [Chart(self.c, self.song_id, 0), Chart(self.c, self.song_id, 1), Chart(
            self.c, self.song_id, 2), Chart(self.c, self.song_id, 3)]
        self.charts[0].defnum = x[2]
        self.charts[1].defnum = x[3]
        self.charts[2].defnum = x[4]
        self.charts[3].defnum = x[5]
        return self

    def insert(self) -> None:
        self.c.execute(
            '''insert into chart values (?,?,?,?,?,?)''', (self.song_id, self.name, self.charts[0].defnum, self.charts[1].defnum, self.charts[2].defnum, self.charts[3].defnum))

    def select(self, song_id: str = None) -> 'Song':
        if song_id is not None:
            self.song_id = song_id

        self.c.execute('''select * from chart where song_id=:a''', {
                       'a': self.song_id})
        x = self.c.fetchone()
        if x is None:
            raise NoData('The song `%s` does not exist.' % self.song_id)

        return self.from_list(x)
