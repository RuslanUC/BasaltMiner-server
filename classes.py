from base64 import urlsafe_b64decode as ub64d, urlsafe_b64encode as ub64e
from hmac import new as hnew
from hashlib import sha256
from json import loads as jloads, dumps as jdumps
from util import formatNumber

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
        if fields:
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
        return [d.to_json(self) for d in self.completedDuels]

    def getMyDuelRequests(self):
        if not self.myDuelRequests:
            self.myDuelRequests = self._core.getMyDuelRequests(self)
        return [d.to_json(self) for d in self.myDuelRequests]

    def getDuelRequests(self):
        if not self.duelRequests:
            self.duelRequests = self._core.getDuelRequests(self)
        return [d.to_json(self) for d in self.duelRequests]

    def duelsAvailable(self):
        return self._core.duelsAvailable(self)

    def addCompletedDuel(self, duel):
        self.completedDuels.insert(0, duel)
        if duel.winner == self:
            self.set(duelsWins=self.duelsWins+1, duelsTotal=self.duelsTotal+1)
        else:
            self.set(duelsTotal=self.duelsTotal+1)

    def addDuelRequest(self, duel):
        self.duelRequests.insert(0, duel)

    def addMyDuelRequest(self, duel):
        self.myDuelRequests.insert(0, duel)

    def declineDuel(self, ouser):
        duels = [duel for duel in self.myDuelRequests+self.duelRequests if duel.othuser == ouser]
        for duel in duels:
            duel.cancel(self)
            try:
                self.myDuelRequests.remove(duel)
            except:
                pass
            try:
                self.duelRequests.remove(duel)
            except:
                pass

    def removeDuelRequest(self, ouser):
        duels = [duel for duel in self.myDuelRequests+self.duelRequests if duel.othuser == ouser]
        for duel in duels:
            try:
                self.myDuelRequests.remove(duel)
            except:
                pass
            try:
                self.duelRequests.remove(duel)
            except:
                pass

    def getStreamers(self):
        return Streamers(self)

    def __eq__(self, other):
        if isinstance(other, User):
            return self.id == other.id
        return False

class CompletedDuel:
    def __init__(self, user1, user2, winner, time):
        self.user1 = user1
        self.user2 = user2
        self.winner = winner
        self.time = time

    def to_json(self, user):
        return [self.user1.login, self.user2.login, self.time, self.winner == user]

class RequestedDuel:
    def __init__(self, othuser, time, rtime, core):
        self.othuser = othuser
        self.time = time
        self.rtime = rtime
        self._core = core

    def to_json(self, user):
        return [self.othuser.id, self.othuser.login, self.time]

    def cancel(self, user):
        if user != self.othuser:
            self._core.declineDuel(user, self.othuser)

class JWT:
    @classmethod
    def decode(cls, token, secret):
        token = bytes(token, "utf8").split(b".")
        header = token[0]
        payload = token[1]
        signature = token[2]
        sig = header+b"."+payload
        sig = hnew(secret, sig, sha256).digest()
        sig = ub64e(sig).replace(b"=", b"")
        if sig == signature:
            payload += b"=" * ((4 - len(payload) % 4) % 4)
            payload = ub64d(payload).decode("utf8")
            return jloads(payload)
        return None

class Streamer:
    def __init__(self, id, count, name, def_cost, def_income, redstone, user):
        self.id = id
        self.count = count
        self.name = name
        self.def_cost = def_cost
        self.def_income = def_income
        self.redstone = redstone
        self._user = user

    def getCost(self):
        return self.def_cost*(self.count+1)

    def getIncomeForCount(self, c):
        if c == 0:
            return 0
        return self.def_income*(1.5**c)

    def toJSON(self):
        return [
            self.id, 
            self.count, 
            self.name, 
            formatNumber(self.getCost()), 
            self.redstone, 
            formatNumber(self.getIncomeForCount(self.count)),
            formatNumber(self.getIncomeForCount(self.count+1))]

    def canBeUpgraded(self, gold, redstone):
        if gold < self.getCost(): return 1
        if redstone < self.redstone: return 2
        return 0

    def upgrade(self):
        self.count += 1

    def getIncome(self):
        return self.getIncomeForCount(self.count)

class Streamers:
    def __init__(self, user):
        self._user = user
        arr = jloads(user.streamers)
        self.st = []
        self.st.append(Streamer(0, arr[0], "5opka", 1000000, 1000, 0, user))
        self.st.append(Streamer(1, arr[1], "JackLooney", 100000000, 10000, 100, user))
        self.st.append(Streamer(2, arr[2], "exx1dae", 10000000000, 100000, 250, user))
        self.st.append(Streamer(3, arr[3], "Zakviel", 10000000000000, 10000000, 500, user))

    def canBeUpgraded(self, id):
        return self.st[id].canBeUpgraded(self._user.gold, self._user.redstone)

    def upgrade(self, id):
        st = self.st[id]
        cost = st.getCost()
        st.upgrade()
        self._user.set(gold=self._user.gold-cost, redstone=self._user.redstone-st.redstone, streamers=jdumps(self.exportLevels()))

    def toJSON(self, id=-1):
        if id != -1:
            return self.st[id].toJSON()
        return [s.toJSON() for s in self.st]

    def getTotalIncome(self):
        return sum([s.getIncome() for s in self.st])

    def getIncome(self, minutes):
        return self.getTotalIncome()*minutes

    def getCost(self, id):
        return self.st[id].getCost()

    def exportLevels(self):
        return [s.count for s in self.st]