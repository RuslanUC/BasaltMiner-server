from mysql.connector import connect
from re import sub
from util import getTS
from random import choice
from time import time
from threading import currentThread
from datetime import datetime
from json import loads as jloads
from classes import User, CompletedDuel, RequestedDuel

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
                user = User(uid, c[0][0], c[0][1], self)
                self._users[uid] = user
                return user

    def getUserByLogin(self, login, fields=[]):
        user = [usr for usr in self._users.values() if usr.login == login]
        if user:
            return user[0]
        else:
            rfields = fields
            if fields:
                fields = [f"`{f}`" for f in fields]
                fields = ", "+", ".join(fields)
            else:
                fields = ""
            cur = self.getDB().cursor()
            print(f'SELECT `user_id`, `count`{fields} FROM `users` WHERE `login`="{self._pr(login)}";')
            cur.execute(f'SELECT `user_id`, `count`{fields} FROM `users` WHERE `login`="{self._pr(login)}";')
            c = list(cur)
            cur.close()
            if c:
                user = User(c[0][0], login, c[0][1], self)
                if fields:
                    user.setData(dict([(k,v) for k,v in zip(rfields, list(c[0])[2:])]))
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
            duels.append(CompletedDuel(user1, user2, winner, tm))
        return duels

    def getMyDuelRequests(self, user):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user1`, `user2`, `time` FROM `duels` WHERE `user1`={user.id} AND `completed`=0 LIMIT 10')
        data = list(cur)
        cur.close()
        duels = []

        oth = None
        date = None

        for row in data:
            u = row[1] if row[0] == user.id else row[0]
            oth = self.getUser(u)
            date = datetime.fromtimestamp(row[2]).strftime("%d.%m.%Y-%H:%M:%S")
            duels.append(RequestedDuel(oth, date, row[2], self))
        return duels

    def getDuelRequests(self, user):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user1`, `user2`, `time` FROM `duels` WHERE `user2`={user.id} AND `completed`=0 LIMIT 10')
        data = list(cur)
        cur.close()
        duels = []

        oth = None
        date = None

        for row in data:
            u = row[1] if row[0] == user.id else row[0]
            oth = self.getUser(u)
            date = datetime.fromtimestamp(row[2]).strftime("%d.%m.%Y-%H:%M:%S")
            duels.append(RequestedDuel(oth, date, row[2], self))
        return duels

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
        cur.execute(f'SELECT `user_id`, `stats`, `duelsWins`, `duelsTotal` FROM `users` WHERE `duelsRandom`=true AND `duelsAuto`=true AND `level`>{user.level-5} AND `level`>9 AND `level`<{user.level+10} AND `user_id`!={user.id} ORDER BY RAND() LIMIT 10')
        data = list(cur)
        cur.close()
        if len(data) < 1:
            return None
        data = choice(data)
        ouser = self.getUser(data[0])
        ouser.setData(dict([(k,v) for k,v in zip(['id', 'stats', 'duelsWins', 'duelsTotal'], list(data))]))
        return ouser

    def insertDuel(self, user, ouser, time, winner=None):
        cur = self.getDB().cursor()
        if winner:
            cur.execute(f'INSERT INTO `duels` VALUES ({user.id}, {ouser.id}, {winner.id}, true, {time})')
        else:
            cur.execute(f'INSERT INTO `duels` VALUES ({user.id}, {ouser.id}, 0, false, {time})')
        cur.close()

    def notCompletedDuelExist(self, user1, user2):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `time` FROM `duels` WHERE ((`user1`={user1.id} AND `user2`={user2.id}) OR (`user1`={user2.id} AND `user2`={user1.id})) AND `completed`=0')
        ex = len(list(cur)) > 0
        cur.close()
        return ex

    def updateDuelData(self, user1, user2, winner, time):
        cur = self.getDB().cursor()
        cur.execute(f'UPDATE `duels` SET `winner`={winner.id}, `completed`=true, `time`={time} WHERE (`user1`={user2.id} AND `user2`={user1.id})')
        cur.close()

    def declineDuel(self, user1, user2):
        cur = self.getDB().cursor()
        cur.execute(f'DELETE FROM `duels` WHERE ((`user1`={user1.id} AND `user2`={user2.id}) OR (`user1`={user2.id} AND `user2`={user1.id})) AND `completed`=0')
        cur.close()