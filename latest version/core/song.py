class Chart:
    # defnum: chart const * 10

    def __init__(self, song_id: str = None, difficulty: int = None, defnum: int = None) -> None:
        self.song_id = song_id
        self.difficulty = difficulty
        self.defnum = defnum
