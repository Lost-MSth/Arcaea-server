from .song import Chart


class Score:
    def __init__(self) -> None:
        self.song = Chart()
        self.score = None
        self.shiny_perfect_count = None
        self.perfect_count = None
        self.near_count = None
        self.miss_count = None
        self.health = None
        self.modifier = None
        self.time_played = None
        self.best_clear_type = None
        self.clear_type = None
        self.rating = None

    def set_score(self, score: int, shiny_perfect_count: int, perfect_count: int, near_count: int, miss_count: int, health: int, modifier: int, time_played: int, clear_type: int):
        self.score = score
        self.shiny_perfect_count = shiny_perfect_count
        self.perfect_count = perfect_count
        self.near_count = near_count
        self.miss_count = miss_count
        self.health = health
        self.modifier = modifier
        self.time_played = time_played
        self.clear_type = clear_type

    @property
    def is_valid(self) -> bool:
        # 分数有效性检查
        return True

    @staticmethod
    def calculate_rating(defnum: int, score: int) -> float:
        # 计算rating，-1视作Unrank
        if not defnum or defnum <= 0:
            # 谱面没定数或者定数小于等于0被视作Unrank
            return -1

        if score >= 10000000:
            ptt = defnum + 2
        elif score < 9800000:
            ptt = defnum + (score-9500000) / 300000
            if ptt < 0:
                ptt = 0
        else:
            ptt = defnum + 1 + (score-9800000) / 200000

        return ptt

    def get_rating_by_calc(self) -> float:
        # 通过计算得到本成绩的rating
        self.rating = self.calculate_rating(self.song.defnum, self.score)
        return self.rating

    @property
    def to_dict(self) -> dict:
        return {
            "rating": self.rating,
            "modifier": self.modifier,
            "time_played": self.time_played,
            "health": self.health,
            "clear_type": self.clear_type,
            "miss_count": self.miss_count,
            "near_count": self.near_count,
            "perfect_count": self.perfect_count,
            "shiny_perfect_count": self.shiny_perfect_count,
            "score": self.score,
            "difficulty": self.song.difficulty,
            "song_id": self.song.song_id
        }
