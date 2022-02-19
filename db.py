from mysql.connector import connect
from re import sub
from util import getTS
from random import choice
from time import time
from threading import currentThread
from datetime import datetime
from json import loads as jloads

class obj:
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

class bmDatabase:
    def __init__(self, host, user, password, database, port=3306):
        self.dbs = {}
        self._dbargs = {"user": user, "password": password, "host": host, "port": port, "database": database, "autocommit": True}

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

    def authUser(self, uid, login):
        login = self._pr(login)
        c = round(time()*1000)
        cur = self.getDB().cursor()
        cur.execute(f'INSERT INTO `users` (`user_id`, `login`, `count`) values ({uid}, "{login}", {c}) ON DUPLICATE KEY UPDATE `count`={c};')
        cur.close()
        return c

    def getUserData(self, select, where):
        rselect = select.copy()
        select = [f"`{s}`" for s in select]
        select = ", ".join(select)
        where = [f"`{k}`={v}" if isinstance(v, int) or isinstance(v, bool) or isinstance(v, float) else f"`{k}`=\"{self._pr(v)}\"" for k,v in where.items()]
        where = " AND ".join(where)
        cur = self.getDB().cursor()
        cur.execute(f'SELECT {select} FROM `users` WHERE {where}')
        c = list(cur)
        cur.close()
        if c:
            res = dict([(k,v) for k,v in zip(rselect, list(c[0]))])
            return obj(**res)
        return None

    def updateUserData(self, set, where):
        set = [f"`{k}`={v}" if isinstance(v, int) or isinstance(v, bool) or isinstance(v, float) else f"`{k}`=\"{self._pr(v)}\"" for k,v in set.items()]
        set = ", ".join(set)
        where = [f"`{k}`={v}" if isinstance(v, int) or isinstance(v, bool) or isinstance(v, float) else f"`{k}`=\"{self._pr(v)}\"" for k,v in where.items()]
        where = " AND ".join(where)
        cur = self.getDB().cursor()
        cur.execute(f'UPDATE `users` SET {set} WHERE {where}')
        cur.close()

    def getCompletedDuels(self, uid, r):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user1`, `user2`, `winner`, `time` FROM `duels` WHERE (`user1`={uid} OR `user2`={uid}) AND `completed`=1 LIMIT 10')
        data = list(cur)
        cur.close()
        res = []
        for row in data:
            res.append([])
            if row[0] == uid:
                res[-1].append(r.login)
                u = row[1]
            else:
                u = row[0]
            oth = self.getUserData(select=['login'], where={'user_id': u})
            if row[0] == uid:
                res[-1].append(oth.login)
            else:
                res[-1].append(oth.login)
                res[-1].append(r.login)
            res[-1].append(datetime.fromtimestamp(row[3]).strftime("%d.%m.%Y-%H:%M:%S"))
            res[-1].append(True if row[2] == uid else False)
        return res

    def getMyDuelRequests(self, uid):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user1`, `user2`, `time` FROM `duels` WHERE `user1`={uid} AND `completed`=0 LIMIT 10')
        data = list(cur)
        cur.close()
        mreq = []
        for row in data:
            mreq.append([])
            if row[0] == uid:
                mreq[-1].append(row[1])
                u = row[1]
            else:
                mreq[-1].append(row[0])
                u = row[0]
            oth = self.getUserData(select=['login'], where={'user_id': u})
            mreq[-1].append(oth.login)
            mreq[-1].append(datetime.fromtimestamp(row[2]).strftime("%d.%m.%Y-%H:%M:%S"))
        return mreq

    def getDuelRequests(self, uid):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user1`, `user2`, `time` FROM `duels` WHERE `user2`={uid} AND `completed`=0 LIMIT 10')
        data = list(cur)
        cur.close()
        req = []
        for row in data:
            req.append([])
            if row[0] == uid:
                req[-1].append(row[1])
                u = row[1]
            else:
                req[-1].append(row[0])
                u = row[0]
            oth = self.getUserData(select=['login'], where={'user_id': u})
            req[-1].append(oth.login)
            req[-1].append(datetime.fromtimestamp(row[2]).strftime("%d.%m.%Y-%H:%M:%S"))
        return req

    def duelsAvailable(self, uid):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `completed` FROM `duels` WHERE (`user1`={uid} OR `user2`={uid}) AND `time` > {getTS()}')
        av = len(list(cur)) <= 25
        cur.close()
        return av

    def duelsAvailableForUsers(self, uid, ouid):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `completed` FROM `duels` WHERE ((`user1`={uid} AND `user2`={ouid}) OR (`user1`={ouid} AND `user2`={uid})) AND `time` > {getTS()}')
        av = len(list(cur)) <= 5
        cur.close()
        return av

    def getUserForRandomDuel(self, uid, r):
        cur = self.getDB().cursor()
        cur.execute(f'SELECT `user_id`, `login`, `stats`, `duelsWins`, `duelsTotal` FROM `users` WHERE `duelsRandom`=true AND `duelsAuto`=true AND `level`>{r.level-5} AND `level`>9 AND `level`<{r.level+10} AND `user_id`!={uid} ORDER BY RAND() LIMIT 10')
        data = list(cur)
        cur.close()
        if len(data) < 1:
            return None
        data = choice(data)
        data = dict([(k,v) for k,v in zip(['user_id', 'login', 'stats', 'duelsWins', 'duelsTotal'], list(data))])
        return obj(**data)

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
        cur.execute(f'SELECT `time` FROM `duels` WHERE ((`user1`={user1} AND `user2`={user2}) OR (`user1`={user2} AND `user2`={user1})) AND `completed`=0')
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