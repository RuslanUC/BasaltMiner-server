from mysql.connector import connect
from re import sub
from util import getTS
from random import choice
from time import time
from threading import currentThread
from datetime import datetime
from json import loads as jloads
from classes import User, CompletelDuel

class bmCore:
    def __init__(self, helix, host, user, password, database, port=3306):
        self.dbs = {}
        self._dbargs = {"user": user, "password": password, "host": host, "port": port, "database": database, "autocommit": True}
        self._users = {}
        self.helix = helix

    def getDB(self):
        ct = currentThread().ident
        if ct in self.dbs:
            db = self.dbs[ct]
            if not db.is_connected():
                try:
                    db.close()
                except:
                    pass
            db = connect(**self._dbargs)
            self.dbs[ct] = db
        else:
            db = connect(**self._dbargs)
            self.dbs[ct] = db
        return db

    def _pr(self, text):
        try:
            jloads(text)
            return text
        except:
            pass
        return sub('[^a-zA-Z0-9_-]', "", text)

    def getTop(self, tp):
        if tp not in ["gold", "level", "redstone", "duelsWins", "biba"]:
            return []
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `login`, `{tp}` FROM users WHERE `ban`=0 ORDER BY {tp} DESC LIMIT 10')
        c = list(cur)
        cur.close()
        for idx, p in enumerate(c):
            c[idx] = list(c[idx])
            c[idx][1] = round(c[idx][1], 1)
        return c

    def authUser(self, uid):
        c = round(time()*1000)
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `login` FROM `users` WHERE `user_id`={uid}')
        cr = list(cur)
        if cr:
            login = cr[0][0]
        else:
            login = self.helix.users([uid])[0].display_name
            login = self._pr(login)
        cur.execute(f'INSERT INTO `users` (`user_id`, `login`, `count`) values ({uid}, "{login}", {c}) ON DUPLICATE KEY UPDATE `count`={c};')
        cur.close()
        user = User(uid, login, c, self)
        self._users[uid] = user
        return user

    def getUser(self, uid):
        if uid in self._users:
            return self._users[uid]
        else:
            cur = self.getDB().cursor()
            cur.execute(f'SELECT `login`, `count` FROM `users` WHERE `user_id`={uid};')
            c = list(cur)
            cur.close()
            if c:
                return User(uid, c[0][0], c[0][1], self)

    def getUserByLogin(self, login, fields=[]):
        user = [usr for usr in self._users if usr.login == login]
        if user:
            return user[0]
        else:
            fields = [f"`{f}`" for f in fields]
            fields = ", ".join(fields)
            cur = self.getDB().cursor()
            cur.execute(f'SELECT `user_id`, `count`, {fields} FROM `users` WHERE `login`={self._pr(login)};')
            c = list(cur)
            cur.close()
            if c:
                user = User(c[0][0], login, c[0][1], self)
                user.setData(dict([(k,v) for k,v in zip(fields, list(c[0])[2:])]))
                self._users[c[0][0]] = user
                return user

    def getData(self, user, fields):
        ofields = fields.copy()
        fields = [f"`{f}`" for f in fields]
        fields = ", ".join(fields)
        cur = self.getDB().cursor()
        cur.execute(f'SELECT {fields} FROM `users` WHERE `user_id`={user.id}')
        c = list(cur)
        cur.close()
        if c:
            data = [(k,v) for k,v in zip(ofields, list(c[0]))]
            return data
        return {}

    def updateUserData(self, user, data):
        data = [f"`{k}`={v}" if isinstance(v, int) or isinstance(v, bool) or isinstance(v, float) else f"`{k}`=\"{self._pr(v)}\"" for k,v in data.items()]
        data = ", ".join(data)
        cur = self.getDB().cursor()
        cur.execute(f'UPDATE `users` SET {data} WHERE `user_id`={user.id}')
        cur.close()

    def getCompletedDuels(self, user):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user1`, `user2`, `winner`, `time` FROM `duels` WHERE (`user1`={user.id} OR `user2`={user.id}) AND `completed`=1 LIMIT 10')
        data = list(cur)
        cur.close()
        duels = []

        user1 = None
        user2 = None
        winner = False
        tm = None

        for row in data:
            if row[0] == user.id:
                user1 = user
                u = row[1]
            else:
                user2 = user
                u = row[0]
            oth = self.getUser(u)
            if row[0] == user.id:
                user2 = oth
            else:
                user1 = oth
            winner = user if row[2] == user.id else oth
            tm = datetime.fromtimestamp(row[3]).strftime("%d.%m.%Y-%H:%M:%S")
            duels.append(CompletelDuel(user1, user2, True, winner, tm, self))
        return duels

    def getMyDuelRequests(self, user):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user1`, `user2`, `time` FROM `duels` WHERE `user1`={user.id} AND `completed`=0 LIMIT 10')
        data = list(cur)
        cur.close()
        mreq = []
        for row in data:
            mreq.append([])
            if row[0] == user.id:
                mreq[-1].append(row[1])
                u = row[1]
            else:
                mreq[-1].append(row[0])
                u = row[0]
            oth = self.getUserData(select=['login'], where={'user_id': u})
            mreq[-1].append(oth.login)
            mreq[-1].append(datetime.fromtimestamp(row[2]).strftime("%d.%m.%Y-%H:%M:%S"))
        return mreq

    def getDuelRequests(self, user):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user1`, `user2`, `time` FROM `duels` WHERE `user2`={user.id} AND `completed`=0 LIMIT 10')
        data = list(cur)
        cur.close()
        req = []
        for row in data:
            req.append([])
            if row[0] == user.id:
                req[-1].append(row[1])
                u = row[1]
            else:
                req[-1].append(row[0])
                u = row[0]
            oth = self.getUserData(select=['login'], where={'user_id': u})
            req[-1].append(oth.login)
            req[-1].append(datetime.fromtimestamp(row[2]).strftime("%d.%m.%Y-%H:%M:%S"))
        return req

    def duelsAvailable(self, user):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `completed` FROM `duels` WHERE (`user1`={user.id} OR `user2`={user.id}) AND `time` > {getTS()}')
        av = len(list(cur)) <= 25
        cur.close()
        return av

    def duelsAvailableForUsers(self, user, ouser):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `completed` FROM `duels` WHERE ((`user1`={user.id} AND `user2`={ouser.id}) OR (`user1`={ouser.id} AND `user2`={user.id})) AND `time` > {getTS()}')
        av = len(list(cur)) <= 5
        cur.close()
        return av

    def getUserForRandomDuel(self, user):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user_id`, `login`, `stats`, `duelsWins`, `duelsTotal` FROM `users` WHERE `duelsRandom`=true AND `duelsAuto`=true AND `level`>{user.level-5} AND `level`>9 AND `level`<{user.level+10} AND `user_id`!={user.id} ORDER BY RAND() LIMIT 10')
        data = list(cur)
        cur.close()
        if len(data) < 1:
            return None
        data = choice(data)
        ouser = User(None, None, None, self)
        ouser.setData(dict([(k,v) for k,v in zip(['id', 'login', 'stats', 'duelsWins', 'duelsTotal'], list(data))]))
        return ouser

    def insertDuel(self, user1, user2, winner, time):
        cur = self.getDB().cursor()
        cur.execute(f'INSERT INTO `duels` VALUES ({user1}, {user2}, {winner}, true, {time})')
        cur.close()

    def insertIncDuel(self, user1, user2, time):
        cur = self.getDB().cursor()
        cur.execute(f'INSERT INTO `duels` VALUES ({user1}, {user2}, 0, false, {time})')
        cur.close()

    def notCompletedDuelExist(self, user1, user2):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `time` FROM `duels` WHERE ((`user1`={user1.id} AND `user2`={user2.id}) OR (`user1`={user2.id} AND `user2`={user1.id})) AND `completed`=0')
        ex = len(list(cur)) > 0
        cur.close()
        return ex

    def updateDuelData(self, user1, user2, winner, time):
        cur = self.getDB().cursor()
        cur.execute(f'UPDATE `duels` SET `winner`={winner}, `completed`=true, `time`={time} WHERE (`user1`={user2} AND `user2`={user1})')
        cur.close()

    def declineDuel(self, user1, user2):
        cur = self.getDB().cursor()
        cur.execute(f'DELETE FROM `duels` WHERE ((`user1`={user1} AND `user2`={user2}) OR (`user1`={user2} AND `user2`={user1})) AND `completed`=0')
        cur.close()