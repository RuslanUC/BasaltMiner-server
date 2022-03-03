class User:
    def __init__(self, id, login, session, core):
        self.id = id
        self.login = login
        self.session = session
        self._core = core
        self.completedDuels = []
        self.myDuelRequests = []
        self.duelRequests = []

    def set(self, **data):
        for k,v in data.items():
            setattr(self, k, v)
        self._core.updateUserData(self, data)

    def getData(self, fields):
        for f in fields.copy():
            if hasattr(self, f):
                fields.remove(f) 
        for k,v in self._core.getData(self, fields):
            setattr(self, k, v)

    def setData(self, data):
        for k,v in data.items():
            setattr(self, k, v)

    def valid(self, sess_id):
        return self.session == sess_id

    def getCompletedDuels(self):
        if not self.completedDuels:
            self.completedDuels = self._core.getCompletedDuels(self)
        return [d.to_json() for d in self.completedDuels]

    def getMyDuelRequests(self):
        if not self.myDuelRequests:
            self.myDuelRequests = self._core.getMyDuelRequests(self)
        return [d.to_json() for d in self.myDuelRequests]

    def getDuelRequests(self):
        if not self.duelRequests:
            self.duelRequests = self._core.getDuelRequests(self)
        return [d.to_json() for d in self.duelRequests]

    def duelsAvailable(self):
        return self._core.duelsAvailable(self)

    def __eq__(self, other):
        if isinstance(other, User):
            return self.id == other.id
        return False

class CompletelDuel:
    def __init__(self, user1, user2, completed, winner, time, core):
        self.user1 = user1
        self.user2 = user2
        self.completed = completed
        self.winner = winner
        self.time = time
        self._core = core

    def to_json(self, user):
        return [self.user1.login, self.user2.login, self.time, self.winner == user]

    def cancel(self):
        ...

    def update(self, winner):
        ...