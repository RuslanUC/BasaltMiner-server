from flask import Flask, request, abort
from time import time
from json import dumps as jdumps, loads as jloads
from functools import wraps
from util import getBlock, getBlockBreakTime, getWorlds, getBibaPercentage, getLevelPrice, worldAvailable, formatNumber, isWin, Logs, LogEntry, RTL
from base64 import urlsafe_b64decode as ub64d
from core import bmCore
from twitch import Helix
from random import random as rrandom
from datetime import datetime
from re import sub
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from mysql.connector import connect
from classes import CompletedDuel, RequestedDuel, JWT, Streamers
import os
import docs

class bmServer(Flask):
    def process_response(self, response):
        response.headers['Server'] = "BasaltMiner"
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Headers'] = "*"
        response.headers['Access-Control-Allow-Methods'] = "*"
        response.headers['Content-Security-Policy'] = "connect-src *;"
        super(bmServer, self).process_response(response)
        return(response)

top = []
STREAM = 1
helix = Helix(os.environ["APP_ID"], os.environ["APP_SECRET"])
core = bmCore(helix=helix, user=os.environ["DB_USER"], password=os.environ["DB_PASS"], host=os.environ["DB_HOST"], port=3306, database=os.environ["DB_NAME"])
app = bmServer("BasaltMiner")
CORS(app)
st = time()
logs = Logs()
requests = {}

# Functions

def topUpdateTask():
    global top
    try:
        top = []
        for tp in ["gold", "level", "redstone", "duelsWins", "biba"]:
            top.append([])
            top[-1] += core.getTop(tp)
    except:
        pass

def liveUpdateTask():
    global STREAM
    try:
        if helix.users(["zakvielchannel"])[0].stream.type == 'live':
            STREAM = 3
        else:
            STREAM = 1
    except:
        pass

def logsTask():
    try:
        s = logs.exportSQLdata()
        if len(s) == 0:
            return
        db = connect(user=os.environ.get("DBL_USER"), password=os.environ.get("DBL_PASS"), host=os.environ.get("DBL_HOST"), port=3306, database=os.environ.get("DBL_NAME"), autocommit=True)
        cur = db.cursor()
        cur.executemany("INSERT INTO logs VALUES (%s, %s, %s, %s);", s)
        cur.close()
        db.close()
    except Exception as e:
        print(f"Error: {e}")

def getUid(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if "X-Extension-Jwt" not in list(request.headers.keys()):
            abort(400, [1, "Invalid jwt token."])
        else:
            token = request.headers["X-Extension-Jwt"]
            try:
                uid = JWT.decode(token, ub64d(bytes(os.environ["APP_KEY"], "utf8")))["user_id"]
            except KeyError:
                abort(400, [2, "Invalid jwt token."])
            except:
                abort(400, [3, "Invalid jwt token."])
            kwargs["uid"] = int(uid)
        return f(*args, **kwargs)
    return dec

def getUser(f):
    @wraps(f)
    def gUser(*args, **kwargs):
        user = core.getUser(kwargs["uid"])
        if "c" not in request.args:
            return abort(403)
        sess = int(request.args.get("c"))
        if not user.valid(sess):
            return abort(403)
        del kwargs["uid"]
        kwargs["user"] = user
        return f(*args, **kwargs)
    return gUser

def getUserData(fields):
    def gd(f):
        @wraps(f)
        def getData(*args, **kwargs):
            user = kwargs["user"]
            user.getData(fields)
            return f(*args, **kwargs)
        return getData
    return gd

def rate_limit(limit):
    def rl(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            uid = kwargs["uid"]
            """if uid in requests:
                r = requests[uid]
                if r.isLimited(f.__name__, limit):
                    abort(429)
            else:
                requests[uid] = RTL()"""
            return f(*args, **kwargs)
        return wrapper
    return rl

@app.before_first_request
def run_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=topUpdateTask, trigger="interval", seconds=30)
    scheduler.add_job(func=liveUpdateTask, trigger="interval", seconds=30)
    scheduler.add_job(func=logsTask, trigger="interval", seconds=30)
    scheduler.start()

@app.errorhandler(400)
def e400(error):
    return jdumps({'error': error.description[1], "code": error.description[0]}), 400

@app.after_request
def after_request(response):
    try:
        uid = JWT.decode(request.headers["X-Extension-Jwt"], ub64d(bytes(os.environ["APP_KEY"], "utf8")))["user_id"]
        logs.addLog(uid, LogEntry(request.full_path, round(time(), 1), response.status_code))
    except:
        pass
    return response

# Routes

@app.route('/', methods=['GET'])
def index():
    return docs.index

@app.route("/dev")
def dev():
    return docs.dev

@app.route("/ext/auth")
@getUid
def ext_auth(uid):
    user = core.authUser(uid)
    user.getData(['level', 'world', 'breakTime', 'block', 'gold', 'redstone', 'ban', 'banReason'])
    if user.ban:
        return jdumps({"message": "You are banned.", "reason": user.banReason}), 403
    return jdumps({"level": user.level, "world": user.world, "time": user.breakTime, "count": user.session, "block": user.block, "point": 2, "update": {"time": round(time()*1000), "money": formatNumber(user.gold), "points": formatNumber(user.redstone)}})

@app.route("/mine/reward")
@getUid
@getUser
@getUserData(['gold', 'boost', 'block', 'world', 'redstone', 'level', 'lastupdate', 'streamers'])
def mine_reward(user):
    block = getBlock(user.world)
    breakTime = getBlockBreakTime(block, user.level)
    bonus = 10 if rrandom() <= 0.13 else 1
    m = user.block*user.boost*STREAM*bonus*0.1
    user.set(gold=user.gold+m+user.getStreamers().getIncome((time()-user.lastupdate)/60), block=block, breakTime=breakTime, lastupdate=round(time()))
    return jdumps({"block": block, "point": 2, "time": breakTime, "cost": formatNumber(m), "boost": round(user.boost*STREAM*bonus, 1), "update": {"time": round(time()*1000), "money": formatNumber(user.gold), "points": formatNumber(user.redstone)}})
    
@app.route("/upgrade/update")
@getUid
@getUser
@getUserData(['gold', 'redstone'])
def upgrade_update(user):
    return jdumps({"time": round(time()*1000), "money": formatNumber(user.gold), "points": formatNumber(user.redstone)})

@app.route("/upgrade/income")
@getUid
@getUser
@getUserData(['boost', 'streamers'])
def upgrade_income(user):
    boosts = []
    total = round(user.boost, 1)
    if STREAM != 1:
        boosts.append(["?????????? ??????????????", STREAM])
        total *= STREAM
    boosts.append(["???????????????????? ??????????????????", round(user.boost, 1)])
    return jdumps({"boost": boosts, "total": total, "income": formatNumber(user.getStreamers().getIncome(1))})

@app.route("/upgrade/level")
@getUid
@getUser
@getUserData(['level', 'stats', 'biba', 'statPoints'])
def upgrade_level(user):
    return jdumps({"level": [user.level, formatNumber(getLevelPrice(user.level))], "biba": [user.biba, 2500, 0, getBibaPercentage(user.biba)], "stats": [["????????", 0, jloads(user.stats)[0]], ["????????????????", 0, jloads(user.stats)[1]], ["??????????????????", 0, jloads(user.stats)[2]]], "discost": 1000, "statpoints": user.statPoints})

@app.route("/upgrade/levelup")
@getUid
@getUser
@getUserData(['level', 'statPoints', 'block', 'gold', 'redstone'])
def upgrade_levelup(user):
    if user.gold >= getLevelPrice(user.level):
        user.set(level=user.level+1, statPoints=user.statPoints+1, breakTime=getBlockBreakTime(user.block, user.level), gold=user.gold-getLevelPrice(user.level))
    else:
        return jdumps({"code": 2})
    return jdumps({"code": 1, "cost": [user.level, getLevelPrice(user.level)], "time": user.breakTime, "update": {"time": round(time()*1000), "money": formatNumber(user.gold), "points": formatNumber(user.redstone)}})

@app.route("/upgrade/bibaup")
@getUid
@getUser
@getUserData(['biba', 'boost', 'redstone', 'gold'])
def upgrade_bibaup(user):
    if user.redstone >= 2500:
        if rrandom() < getBibaPercentage(user.biba)/100:
            user.set(biba=user.biba+1, boost=user.boost+0.1, redstone=user.redstone-2500)
        else:
            user.set(biba=user.biba-1, boost=user.boost-0.1, redstone=user.redstone-2500)
    else:
        return jdumps({"code": 2})
    return jdumps({"code": 1, "cost": [user.biba, 2500, 0, getBibaPercentage(user.biba)], "update": {"time": round(time()*1000), "money": formatNumber(user.gold), "points": formatNumber(user.redstone)}})

@app.route("/upgrade/statdis")
@getUid
@getUser
@getUserData(['statPoints', 'stats', 'redstone', 'gold'])
def upgrade_statdis(user):
    if user.redstone >= 1000:
        s = sum(jloads(user.stats))
        if s == 0:
            return jdumps({"code": 2})
        user.set(stats=jdumps([0, 0, 0]), statPoints=user.statPoints+s, redstone=user.redstone-1000)
    else:
        return jdumps({"code": 3})
    return jdumps({"code": 1, "statpoints": user.statPoints, "update": {"time": round(time()*1000), "money": formatNumber(user.gold), "points": formatNumber(user.redstone)}, "cost": 1000})

@app.route("/upgrade/statadd")
@getUid
@getUser
@getUserData(['statPoints', 'stats'])
def upgrade_statadd(user):
    sid = int(request.args.get("id"))
    if user.statPoints >= 1:
        s = jloads(user.stats)
        s[sid-1] += 1
        user.set(stats=jdumps(s), statPoints=user.statPoints-1)
    else:
        return jdumps({"code": 2})
    return jdumps({"code": 1, "stats": [["????????", 0, jloads(user.stats)[0]], ["????????????????", 0, jloads(user.stats)[1]], ["??????????????????", 0, jloads(user.stats)[2]]], "statpoints": user.statPoints})

@app.route("/upgrade/faq")
@getUid
@getUser
def upgrade_faq(user):
    return jdumps([["?????? ?????????????????????? ?????????????", "??????."]])

@app.route("/top/list")
@getUid
@getUser
def top_list(user):
    return jdumps({"top": top, "time": round(time()*1000), "next": 60})

@app.route("/world/list")
@getUid
@getUser
@getUserData(['level'])
def world_list(user):
    return jdumps(getWorlds(user.level))

@app.route("/world/select")
@getUid
@getUser
@getUserData(['level'])
def world_select(user):
    wid = int(request.args.get("id"))
    if worldAvailable(user.level, wid) and wid <= 17:
        bl = getBlock(wid)
        bt = getBlockBreakTime(bl, user.level)
        user.set(world=wid, block=bl, breakTime=bt)
    else:
        return jdumps({"error": "?????????????? ?????????????? ???????????? ?????? ???????? ?????????? ?????? ?????????? ?????????? ???? ????????????????????."}), 400
    return jdumps({"point": 2, "time": bt, "block": bl})

@app.route("/duel/menu")
@getUid
@getUser
@getUserData(['duelsTotal', 'duelsWins', 'duelsRandom', 'duelsAuto', 'login'])
def duel_menu(user):
    res = user.getCompletedDuels()
    mreq = user.getMyDuelRequests()
    req = user.getDuelRequests()
    return jdumps({"wins": user.duelsWins, "count": user.duelsTotal, "auto": user.duelsAuto, "rnd": user.duelsRandom, "requests": req, "myrequests": mreq, "results": res})

@app.route("/duel/set")
@getUid
@getUser
@getUserData(['duelsRandom', 'duelsAuto'])
def duel_set(user):
    cid = int(request.args.get("id"))
    if cid == 1:
        user.set(duelsRandom=not r.duelsRandom)
    else:
        user.set(duelsAuto=not r.duelsAuto)
    return jdumps({"ok": True})

@app.route("/duel/rnd")
@getUid
@getUser
@getUserData(['login', 'stats', 'level', 'duelsWins', 'duelsTotal'])
def duel_rnd(user):
    if not user.duelsAvailable():
        return jdumps({"code": 1})
    ouser = core.getUserForRandomDuel(user)
    if not ouser:
        return jdumps({"code": 2})
    iw = isWin(user.stats, ouser.stats)
    winner = user if iw else ouser
    curtime = round(time())
    tm = datetime.fromtimestamp(curtime).strftime("%d.%m.%Y-%H:%M:%S")
    duel = CompletedDuel(user, ouser, winner, tm)
    user.addCompletedDuel(duel)
    ouser.addCompletedDuel(duel)
    core.insertDuel(user, ouser, winner, curtime)
    return jdumps({"code": 3, "result": [user.login, ouser.login, tm, iw]})

@app.route("/duel/send")
@getUid
@getUser
def duel_send(user):
    login = request.args.get("login")
    login = sub('[^a-zA-Z0-9_-]', "", login)
    if 4 > len(login) > 25:
        return jdumps({"code": 1})
    if not user.duelsAvailable():
        return jdumps({"code": 5})
    if user.login.lower() == login.lower():
        return jdumps({"code": 2})
    ouser = core.getUserByLogin(login, ['level'])
    if not ouser:
        return jdumps({"code": 1})
    if ouser.level < 10:
        return jdumps({"code": 3})
    if core.notCompletedDuelExist(user, ouser):
        return jdumps({"code": 4})
    curtime = round(time())
    tm = datetime.fromtimestamp(curtime).strftime("%d.%m.%Y-%H:%M:%S")
    user.addMyDuelRequest(RequestedDuel(ouser, tm, curtime, core))
    ouser.addDuelRequest(RequestedDuel(user, tm, curtime, core))
    core.insertDuel(user, ouser, curtime)
    return jdumps({"code": 6, "request": [ouser.id, login, tm]})

@app.route("/duel/decline")
@getUid
@getUser
def duel_decline(user):
    ouid = int(request.args.get("id"))
    user.declineDuel(core.getUser(ouid))
    return jdumps({"code": 0})

@app.route("/duel/accept")
@getUid
@getUser
@getUserData(['stats', 'level', 'duelsWins', 'duelsTotal'])
def duel_accept(user):
    ouid = int(request.args.get("id"))
    ouser = core.getUser(ouid)
    if not user.duelsAvailable():
        return jdumps({"code": 2})
    if not ouser.duelsAvailable():
        return jdumps({"code": 5})
    if not core.duelsAvailableForUsers(user, ouser):
        return jdumps({"code": 4})
    ouser.getData(['login', 'stats', 'duelsWins', 'duelsTotal'])
    iw = isWin(user.stats, ouser.stats)
    curtime = round(time())
    tm = datetime.fromtimestamp(curtime).strftime("%d.%m.%Y-%H:%M:%S")
    winner = user if iw else ouser
    user.removeDuelRequest(ouser)
    ouser.removeDuelRequest(user)
    duel = CompletedDuel(user, ouser, winner, tm)
    user.addCompletedDuel(duel)
    ouser.addCompletedDuel(duel)
    core.updateDuelData(user, ouser, winner, curtime)
    return jdumps({"code": 5, "result": [user.login, ouser.login, tm, iw], "wins": user.duelsWins, "count": user.duelsTotal})

@app.route("/upgrade/list")
@getUid
@getUser
@getUserData(['streamers'])
def upgrade_list(user):
    return jdumps(user.getStreamers().toJSON())

@app.route("/upgrade/streamerup")
@getUid
@getUser
@getUserData(['streamers', 'gold', 'redstone'])
def upgrade_streamerup(user):
    streamer_id = int(request.args.get("id"))
    st = user.getStreamers()
    cbu = st.canBeUpgraded(streamer_id)
    if cbu in [1, 2]:
        return jdumps({"code": cbu})
    st.upgrade(streamer_id)
    return jdumps({"code": 3, "info": st.toJSON(streamer_id), "update": {"time": round(time()*1000), "money": formatNumber(user.gold), "points": formatNumber(user.redstone)}})

@app.route("/uptime")
def uptime():
    return jdumps({"uptime": round(time()-st)})

# Start
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)