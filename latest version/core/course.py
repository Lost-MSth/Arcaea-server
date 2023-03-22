from .error import NoData
from .item import ItemFactory
from .song import Chart


class CourseChart(Chart):
    def __init__(self, c=None, song_id: str = None, difficulty: int = None) -> None:
        super().__init__(c, song_id, difficulty)
        self.flag_as_hidden: bool = None

    def from_dict(self, d: dict) -> 'CourseChart':
        self.song_id = d['id']
        self.difficulty = d['difficulty']
        self.flag_as_hidden = d.get('flag_as_hidden', False)
        return self

    def to_dict(self) -> dict:
        return {
            'id': self.song_id,
            'difficulty': self.difficulty,
            'flag_as_hidden': self.flag_as_hidden
        }

    def insert_course_chart(self, course_id: str, song_index: int) -> None:
        self.c.execute('insert into course_chart values (?,?,?,?,?)',
                       (course_id, self.song_id, self.difficulty, self.flag_as_hidden, song_index))


class Course:
    def __init__(self, c=None) -> None:
        self.c = c
        self.course_id: str = None
        self.course_name: str = None
        self.dan_name: str = None
        self.style: int = None
        self.gauge_requirement: str = None
        self.flag_as_hidden_when_requirements_not_met: bool = None
        self.can_start: bool = None  # 这有什么鬼用？

        self.requirements: list = []
        self.charts: list = [None, None, None, None]
        self.items: list = None

    def to_dict(self) -> dict:
        if self.course_name is None:
            self.select_course()
        if not self.items:
            self.select_course_item()
        if not self.charts:
            self.select_course_chart()
        return {
            'course_id': self.course_id,
            'course_name': self.course_name,
            'dan_name': self.dan_name,
            'style': self.style,
            'gauge_requirement': self.gauge_requirement,
            'flag_as_hidden_when_requirements_not_met': self.flag_as_hidden_when_requirements_not_met,
            'can_start': self.can_start,
            'requirements': [{'value': x, 'type': 'course'} for x in self.requirements],
            'songs': [x.to_dict() for x in self.charts],
            'rewards': [str(x) for x in self.items]
        }

    def from_dict(self, d: dict) -> 'Course':
        self.course_id = d['course_id']
        self.course_name = d.get('course_name', '')
        self.dan_name = d.get('dan_name', '')
        self.style = d.get('style', 1)
        self.gauge_requirement = d.get('gauge_requirement', 'default')
        self.flag_as_hidden_when_requirements_not_met = d.get(
            'flag_as_hidden_when_requirements_not_met', False)
        self.can_start = d.get('can_start', True)
        self.requirements = [x['value'] for x in d.get('requirements', [])]
        self.charts = [CourseChart(self.c).from_dict(x)
                       for x in d.get('songs', [])]
        self.items = [ItemFactory.from_str(x, self.c)
                      for x in d.get('rewards', [])]

        return self

    def from_list(self, l: list) -> 'Course':
        self.course_id = l[0]
        self.course_name = l[1]
        self.dan_name = l[2]
        self.style = l[3] if l[3] else 1
        self.gauge_requirement = l[4] if l[4] else 'default'
        self.flag_as_hidden_when_requirements_not_met = l[5] == 1
        self.can_start = l[6] == 1

        return self

    def select_course(self, course_id: str = None) -> 'Course':
        if course_id is not None:
            self.course_id = course_id
        self.c.execute(
            '''select * from course where course_id = ?''', (self.course_id,))
        x = self.c.fetchone()
        if x is None:
            raise NoData(f'The course `{self.course_id}` is not found.')
        return self.from_list(x)

    def select_course_chart(self) -> None:
        self.c.execute(
            '''select * from course_chart where course_id = ?''', (self.course_id,))

        for i in self.c.fetchall():
            self.charts[i[4]] = CourseChart(self.c).from_dict({
                'id': i[1],
                'difficulty': i[2],
                'flag_as_hidden': i[3] == 1
            })

    def select_course_requirement(self) -> None:
        self.c.execute(
            '''select required_id from course_requirement where course_id = ?''', (self.course_id,))
        self.requirements = [x[0] for x in self.c.fetchall()]

    def select_course_item(self) -> None:
        self.c.execute(
            '''select * from course_item where course_id = ?''', (self.course_id,))
        self.items = [ItemFactory.from_dict({
            'item_id': x[1],
            'type': x[2],
            'amount': x[3] if x[3] else 1,
        }, self.c) for x in self.c.fetchall()]

    def insert_course(self) -> None:
        self.c.execute(
            '''insert into course values (?,?,?,?,?,?,?)''', (self.course_id, self.course_name, self.dan_name, self.style, self.gauge_requirement, self.flag_as_hidden_when_requirements_not_met, self.can_start))

    def insert_course_item(self) -> None:
        for i in self.items:
            self.c.execute('''insert into course_item values (?,?,?,?)''',
                           (self.course_id, i.item_id, i.item_type, i.amount))

    def insert_course_chart(self) -> None:
        for i, x in enumerate(self.charts):
            x.insert_course_chart(self.course_id, i)

    def insert_course_requirement(self) -> None:
        for i in self.requirements:
            self.c.execute('''insert into course_requirement values (?,?)''',
                           (self.course_id, i))

    def insert_all(self) -> None:
        self.insert_course()
        self.insert_course_item()
        self.insert_course_chart()
        self.insert_course_requirement()


class UserCourse(Course):
    '''
        用户课题类

        parameter: `user` - `User`类或子类的实例
    '''

    def __init__(self, c=None, user=None) -> None:
        super().__init__(c)
        self.user = user

        self.is_completed: bool = False
        self.high_score: int = None
        self.best_clear_type: int = None

    def to_dict(self) -> dict:
        r = super().to_dict()
        if self.is_completed is None:
            self.select_user_course()
        r.update({
            'is_completed': self.is_completed,
            'high_score': self.high_score,
            'best_clear_type': self.best_clear_type
        })
        return r

    def select_user_course(self, course_id: str = None) -> None:
        if course_id is not None:
            self.course_id = course_id
        self.c.execute('''select * from user_course where user_id = ? and course_id = ?''',
                       (self.user.user_id, self.course_id))
        x = self.c.fetchone()
        if x is None:
            self.is_completed = False
            self.high_score = 0
            self.best_clear_type = 0
        else:
            self.is_completed = True
            self.high_score = x[2]
            self.best_clear_type = x[3]

    def insert_user_course(self) -> None:
        self.c.execute('''insert into user_course values (?,?,?,?)''',
                       (self.user.user_id, self.course_id, self.high_score, self.best_clear_type))

    def update_user_course(self) -> None:
        self.c.execute('''update user_course set high_score = ?, best_clear_type = ? where user_id = ? and course_id = ?''',
                       (self.high_score, self.best_clear_type, self.user.user_id, self.course_id))


class UserCourseList:
    '''
        用户课题列表类

        parameter: `user` - `User`类或子类的实例
    '''

    def __init__(self, c=None, user=None) -> None:
        self.c = c
        self.user = user

        self.courses: list = []

    def to_dict_list(self) -> list:
        # 临时修复满足条件也无法解锁隐藏段位的问题
        completed_course_id_list: list = []
        r: list = []
        for x in self.courses:
            if x.is_completed:
                completed_course_id_list.append(x.course_id)
            r.append(x.to_dict())
        for x in r:
            for i in x['requirements']:
                if i['value'] in completed_course_id_list:
                    i['is_fullfilled'] = True
        return r

    def select_all(self) -> None:
        self.c.execute('''select * from course''')
        self.courses = [UserCourse(self.c, self.user).from_list(x)
                        for x in self.c.fetchall()]
        for i in self.courses:
            i.select_user_course()
            i.select_course_chart()
            i.select_course_item()
            i.select_course_requirement()


class CoursePlay(UserCourse):
    '''
        课题模式打歌类，联动UserPlay

        parameter: `user` - `UserOnline`类或子类的实例
        'user_play` - `UserPlay`类的实例
    '''

    def __init__(self, c=None, user=None, user_play=None) -> None:
        super().__init__(c, user)
        self.user_play = user_play

        self.score: int = None
        self.clear_type: int = None

    def to_dict(self) -> dict:
        return {
            'rewards': [x.to_dict() for x in self.items],
            "current_stamina": self.user.stamina.stamina,
            "max_stamina_ts": self.user.stamina.max_stamina_ts,
            'user_course_banners': self.user.course_banners
        }

    def update(self) -> None:
        '''课题模式更新'''
        if self.user_play.health < 0:
            # 你挂了
            self.user_play.course_play_state = 5
            self.score = 0
            self.clear_type = 0
            self.user_play.update_play_state_for_course()
            return None
        self.user_play.course_play_state += 1
        self.score += self.user_play.score
        from .score import Score
        if Score.get_song_state(self.clear_type) > Score.get_song_state(self.user_play.clear_type):
            self.clear_type = self.user_play.clear_type
        self.user_play.update_play_state_for_course()

        if self.user_play.course_play_state == 4:
            self.user.select_user_about_stamina()
            self.select_course_item()
            for i in self.items:
                i.user_claim_item(self.user)

            self.select_user_course()
            if not self.is_completed:
                self.high_score = self.score
                self.best_clear_type = self.clear_type
                self.is_completed = True
                self.insert_user_course()
                return None

            flag = False
            if self.score > self.high_score:
                self.high_score = self.score
                flag = True
            if Score.get_song_state(self.clear_type) > Score.get_song_state(self.best_clear_type):
                self.best_clear_type = self.clear_type
                flag = True
            if flag:
                self.update_user_course()
