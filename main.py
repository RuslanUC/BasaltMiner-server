from flask import Flask, request, abort
from time import time, sleep
from json import dumps as jdumps, loads as jloads
from functools import wraps
from util import JWT, getBlock, getBlockBreakTime, getWorlds, getBibaPercentage, getLevelPrice, worldAvailable, formatNumber, Streamers, getStreamersIncome, isWin, Logs, LogEntry, RTL
from base64 import urlsafe_b64decode as ub64d
from db import bmDatabase
from twitch import Helix
from random import random as rrandom
from threading import Thread
from datetime import datetime
from re import sub
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from mysql.connector import connect
import os
import docs

class bmServer(Flask):
    def process_response(self, response):
        response.headers['Server'] = "BasaltMiner"
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Headers'] = "*"
        response.headers['Access-Control-Allow-Methods'] = "*"
        response.headers['Content-Security-Policy'] = "default-src 'self' https://5fro3bxcl1xjauv4n9t5gzee9qore0.ext-twitch.tv; block-all-mixed-content; img-src 'self' https://5fro3bxcl1xjauv4n9t5gzee9qore0.ext-twitch.tv https://www.google-analytics.com data: blob:; media-src 'self' https://5fro3bxcl1xjauv4n9t5gzee9qore0.ext-twitch.tv data: blob:; frame-ancestors https://supervisor.ext-twitch.tv https://extension-files.twitch.tv https://*.twitch.tv https://*.twitch.tech https://localhost.twitch.tv:* https://localhost.twitch.tech:* http://localhost.rig.twitch.tv:*; font-src 'self' https://5fro3bxcl1xjauv4n9t5gzee9qore0.ext-twitch.tv https://fonts.googleapis.com https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://5fro3bxcl1xjauv4n9t5gzee9qore0.ext-twitch.tv https://fonts.googleapis.com; connect-src 'self' https://5fro3bxcl1xjauv4n9t5gzee9qore0.ext-twitch.tv https://api.twitch.tv wss://pubsub-edge.twitch.tv https://www.google-analytics.com https://stats.g.doubleclick.net; script-src 'self' https://5fro3bxcl1xjauv4n9t5gzee9qore0.ext-twitch.tv https://extension-files.twitch.tv https://www.google-analytics.com;"
        super(bmServer, self).process_response(response)
        return(response)

top = []
STREAM = 1
db = bmDatabase(user=os.environ["DB_USER"], password=os.environ["DB_PASS"], host=os.environ["DB_HOST"], port=3306, database=os.environ["DB_NAME"])
helix = Helix(os.environ["APP_ID"], os.environ["APP_SECRET"])
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
            top[-1] += db.getTop(tp)
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

def jwt_required(f):
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
    return "" #docs.index

@app.route("/dev")
def dev():
    return "" #docs.dev

@app.route("/ext/auth")
@jwt_required
@rate_limit(15)
def ext_auth(uid):
    r = db.getUserData(select=['login'], where={'user_id': uid})
    if r:
        login = r.login
    else:
        login = helix.users([uid])[0].display_name
    count = db.authUser(uid, login)
    r = db.getUserData(select=['level', 'world', 'breakTime', 'block', 'gold', 'redstone', 'ban', 'banReason'], where={'user_id': uid})
    if r.ban:
        return jdumps({"message": "You are banned.", "reason": r.banReason}), 403
    return jdumps({"level": r.level, "world": r.world, "time": r.breakTime, "count": count, "block": r.block, "point": 2, "update": {"time": round(time()*1000), "money": formatNumber(r.gold), "points": formatNumber(r.redstone)}})

@app.route("/mine/reward")
@jwt_required
@rate_limit(1)
def mine_reward(uid):
    try:
        r = db.getUserData(select=['gold', 'boost', 'block', 'world', 'redstone', 'level', 'lastupdate', 'streamers'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    block = getBlock(r.world)
    breakTime = getBlockBreakTime(block, r.level)
    bonus = 10 if rrandom() <= 0.13 else 1
    m = r.block*r.boost*STREAM*bonus*0.1
    db.updateUserData(set={'gold': r.gold+m+getStreamersIncome((round(time())-r.lastupdate)/60, r.streamers), 'block': block, 'breakTime': breakTime, 'lastupdate': round(time())}, where={'user_id': uid})
    return jdumps({"block": block, "point": 2, "time": breakTime, "cost": formatNumber(m), "boost": round(r.boost*STREAM*bonus, 1), "update": {"time": round(time()*1000), "money": formatNumber(r.gold+m), "points": formatNumber(r.redstone)}})
    
@app.route("/upgrade/update")
@jwt_required
@rate_limit(5)
def upgrade_update(uid):
    try:
        r = db.getUserData(select=['gold', 'redstone'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    return jdumps({"time": round(time()*1000), "money": formatNumber(r.gold), "points": formatNumber(r.redstone)})

@app.route("/upgrade/income")
@jwt_required
@rate_limit(5)
def upgrade_income(uid):
    try:
        r = db.getUserData(select=['boost', 'streamers'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    boosts = []
    total = round(r.boost, 1)
    if STREAM != 1:
        boosts.append(["Стрим запущен", STREAM])
        total *= STREAM
    boosts.append(["Постоянный множитель", round(r.boost, 1)])
    return jdumps({"boost": boosts, "total": total, "income": formatNumber(getStreamersIncome(1, r.streamers))})

@app.route("/upgrade/level")
@jwt_required
@rate_limit(5)
def upgrade_level(uid):
    try:
        r = db.getUserData(select=['level', 'stats', 'biba', 'statPoints'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    return jdumps({"level": [r.level, formatNumber(getLevelPrice(r.level))], "biba": [r.biba, 2500, 0, getBibaPercentage(r.biba)], "stats": [["Сила", 0, jloads(r.stats)[0]], ["Ловкость", 0, jloads(r.stats)[1]], ["Интеллект", 0, jloads(r.stats)[2]]], "discost": 1000, "statpoints": r.statPoints})

@app.route("/upgrade/levelup")
@jwt_required
@rate_limit(15)
def upgrade_levelup(uid):
    try:
        r = db.getUserData(select=['level', 'statPoints', 'block', 'gold'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    if r.gold >= getLevelPrice(r.level):
        db.updateUserData(set={'level': r.level+1, 'statPoints': r.statPoints+1, 'breakTime': getBlockBreakTime(r.block, r.level), 'gold': r.gold-getLevelPrice(r.level)}, where={'user_id': uid})
    else:
        return jdumps({"code": 2})
    r = db.getUserData(select=['level', 'gold', 'statPoints', 'breakTime', 'redstone'], where={'user_id': uid, 'count': request.args.get("c")})
    return jdumps({"code": 1, "cost": [r.level, getLevelPrice(r.level)], "time": r.breakTime, "update": {"time": round(time()*1000), "money": formatNumber(r.gold), "points": formatNumber(r.redstone)}})

@app.route("/upgrade/bibaup")
@jwt_required
@rate_limit(1)
def upgrade_bibaup(uid):
    try:
        r = db.getUserData(select=['biba', 'boost', 'redstone'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    if r.redstone >= 2500:
        if rrandom() < getBibaPercentage(r.biba)/100:
            db.updateUserData(set={'biba': r.biba+1, 'boost': r.boost+0.1, 'redstone': r.redstone-2500}, where={'user_id': uid})
        else:
            db.updateUserData(set={'biba': r.biba-1, 'boost': r.boost-0.1, 'redstone': r.redstone-2500}, where={'user_id': uid})
    else:
        return jdumps({"code": 2})
    r = db.getUserData(select=['gold', 'biba', 'redstone'], where={'user_id': uid, 'count': request.args.get("c")})
    return jdumps({"code": 1, "cost": [r.biba, 2500, 0, getBibaPercentage(r.biba)], "update": {"time": round(time()*1000), "money": formatNumber(r.gold), "points": formatNumber(r.redstone)}})

@app.route("/upgrade/statdis")
@jwt_required
@rate_limit(15)
def upgrade_statdis(uid):
    try:
        r = db.getUserData(select=['statPoints', 'stats', 'redstone'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    if r.redstone >= 1000:
        s = sum(jloads(r.stats))
        if s == 0:
            return jdumps({"code": 2})
        db.updateUserData(set={'stats': jdumps([0, 0, 0]), 'statPoints': r.statPoints+s, 'redstone': r.redstone-1000}, where={'user_id': uid})
    else:
        return jdumps({"code": 3})
    r = db.getUserData(select=['stats', 'statPoints', 'gold', 'redstone'], where={'user_id': uid, 'count': request.args.get("c")})
    return jdumps({"code": 1, "statpoints": r.statPoints, "update": {"time": round(time()*1000), "money": formatNumber(r.gold), "points": formatNumber(r.redstone)}, "cost": 1000})

@app.route("/upgrade/statadd")
@jwt_required
@rate_limit(0.5)
def upgrade_statadd(uid):
    try:
        r = db.getUserData(select=['statPoints', 'stats'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    sid = int(request.args.get("id"))
    if r.statPoints >= 1:
        s = jloads(r.stats)
        s[sid-1] += 1
        db.updateUserData(set={'stats': jdumps(s), 'statPoints': r.statPoints-1}, where={'user_id': uid})
    else:
        return jdumps({"code": 2})
    return jdumps({"code": 1, "stats": [["Сила", 0, s[0]], ["Ловкость", 0, s[1]], ["Интеллект", 0, s[2]]], "statpoints": r.statPoints-1})

@app.route("/upgrade/faq")
@jwt_required
@rate_limit(15)
def upgrade_faq(uid):
    try:
        db.getUserData(select=['level'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    faq = [["Я пополнил редстоун, но он не отображается в игре", "при пополнении нужно написать любую букву или цифру."], ["Я не могу войти в игру, хотя другие могут", "Ваш аккаунт был заблокирован."]]
    return jdumps(faq)

@app.route("/top/list")
@jwt_required
@rate_limit(15)
def top_list(uid):
    try:
        db.getUserData(select=['level'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    return jdumps({"top": top, "time": round(time()*1000), "next": 60})

@app.route("/world/list")
@jwt_required
@rate_limit(5)
def world_list(uid):
    try:
        r = db.getUserData(select=['level'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    return jdumps(getWorlds(r.level))

@app.route("/world/select")
@jwt_required
@rate_limit(15)
def world_select(uid):
    try:
        r = db.getUserData(select=['level'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    wid = int(request.args.get("id"))
    if worldAvailable(r.level, wid) and wid <= 17:
        bl = getBlock(wid)
        bt = getBlockBreakTime(bl, r.level)
        db.updateUserData(set={'world': wid, 'block': bl, 'breakTime': bt}, where={'user_id': uid})
    else:
        return jdumps({"error": "Уровень слишком низкий для этого мира или такого мира не существует."}), 400
    return jdumps({"point": 2, "time": bt, "block": bl})

@app.route("/duel/menu")
@jwt_required
@rate_limit(5)
def duel_menu(uid):
    try:
        r = db.getUserData(select=['duelsTotal', 'duelsWins', 'duelsRandom', 'duelsAuto', 'login'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    res = db.getCompletedDuels(uid, r)
    mreq = db.getMyDuelRequests(uid)
    req = db.getDuelRequests(uid)
    return jdumps({"wins": r.duelsWins, "count": r.duelsTotal, "auto": r.duelsAuto, "rnd": r.duelsRandom, "requests": req, "myrequests": mreq, "results": res})

@app.route("/duel/set")
@jwt_required
@rate_limit(5)
def duel_set(uid):
    try:
        r = db.getUserData(select=['duelsRandom', 'duelsAuto'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    cid = int(request.args.get("id"))
    if cid == 1:
        db.updateUserData(set={'duelsRandom': not r.duelsRandom}, where={'user_id': uid})
    else:
        db.updateUserData(set={'duelsAuto': not r.duelsAuto}, where={'user_id': uid})
    return jdumps({"ok": True})

@app.route("/duel/rnd")
@jwt_required
@rate_limit(10)
def duel_rnd(uid):
    try:
        r = db.getUserData(select=['login', 'stats', 'level', 'duelsWins', 'duelsTotal'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    if not db.duelsAvailable(uid):
        return jdumps({"code": 1})
    d = db.getUserForRandomDuel(uid, r)
    if d == None:
        return jdumps({"code": 2})
    iw = isWin(r.stats, d.stats)
    curtime = round(time())
    if iw:
        db.updateUserData(set={'duelsWins': r.duelsWins+1, 'duelsTotal': r.duelsTotal+1}, where={'user_id': uid, 'count': request.args.get("c")})
        db.updateUserData(set={'duelsTotal': d.duelsTotal+1}, where={'user_id': d.user_id})
    else:
        db.updateUserData(set={'duelsTotal': r.duelsTotal+1}, where={'user_id': uid, 'count': request.args.get("c")})
        db.updateUserData(set={'duelsWins': r.duelsWins+1, 'duelsTotal': d.duelsTotal+1}, where={'user_id': d.user_id})
    db.insertDuel(uid, d.user_id, uid if iw else d.user_id, curtime)
    return jdumps({"code": 3, "result": [r.login, d.login, datetime.fromtimestamp(curtime).strftime("%d.%m.%Y-%H:%M:%S"), iw]})

@app.route("/duel/send")
@jwt_required
@rate_limit(10)
def duel_send(uid):
    login = request.args.get("login")
    login = sub('[^a-zA-Z0-9_-]', "", login)
    if 4 > len(login) > 25:
        return jdumps({"code": 1})
    try:
        r = db.getUserData(select=['login'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    if not db.duelsAvailable(uid):
        return jdumps({"code": 5})
    if r.login.lower() == login.lower():
        return jdumps({"code": 2})
    d = db.getUserData(select=['user_id', 'level'], where={'login': login})
    if d == None:
        return jdumps({"code": 1})
    if d.level < 10:
        return jdumps({"code": 3})
    if db.notCompletedDuelExist(uid, d.user_id):
        return jdumps({"code": 4})
    curtime = round(time())
    db.insertIncDuel(uid, d.user_id, curtime)
    return jdumps({"code": 6, "request": [d.user_id, login, datetime.fromtimestamp(curtime).strftime("%d.%m.%Y-%H:%M:%S")]})

@app.route("/duel/decline")
@jwt_required
@rate_limit(5)
def duel_decline(uid):
    ouid = int(request.args.get("id"))
    try:
        db.getUserData(select=['login'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    db.declineDuel(uid, ouid)
    return jdumps({"code": 0})

@app.route("/duel/accept")
@jwt_required
@rate_limit(5)
def duel_accept(uid):
    ouid = int(request.args.get("id"))
    try:
        r = db.getUserData(select=['login', 'stats', 'duelsWins', 'duelsTotal'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    if not db.duelsAvailable(uid):
        return jdumps({"code": 2})
    if not db.duelsAvailable(ouid):
        return jdumps({"code": 5})
    if not db.duelsAvailableForUsers(uid, ouid):
        return jdumps({"code": 4})
    d = db.getUserData(select=['login', 'stats', 'duelsWins', 'duelsTotal'], where={'user_id': ouid})
    iw = isWin(r.stats, d.stats)
    curtime = round(time())
    if iw:
        db.updateUserData(set={'duelsWins': r.duelsWins+1, 'duelsTotal': r.duelsTotal+1}, where={'user_id': uid, 'count': request.args.get("c")})
        db.updateUserData(set={'duelsTotal': d.duelsTotal+1}, where={'user_id': ouid})
    else:
        db.updateUserData(set={'duelsTotal': r.duelsTotal+1}, where={'user_id': uid, 'count': request.args.get("c")})
        db.updateUserData(set={'duelsWins': r.duelsWins+1, 'duelsTotal': d.duelsTotal+1}, where={'user_id': ouid})
    db.updateDuelData(uid, ouid, uid if iw else ouid, curtime)
    return jdumps({"code": 5, "result": [r.login, d.login, datetime.fromtimestamp(curtime).strftime("%d.%m.%Y-%H:%M:%S"), iw], "wins": r.duelsWins+(1 if iw else 0), "count": r.duelsTotal+1})

@app.route("/upgrade/list")
@jwt_required
@rate_limit(5)
def upgrade_list(uid):
    try:
        r = db.getUserData(select=['streamers'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    return jdumps(Streamers(r.streamers).toJSON())

@app.route("/upgrade/streamerup")
@jwt_required
@rate_limit(15)
def upgrade_streamerup(uid):
    streamer_id = int(request.args.get("id"))
    try:
        r = db.getUserData(select=['streamers', 'gold', 'redstone'], where={'user_id': uid, 'count': request.args.get("c")})
    except IndexError:
        return abort(403)
    st = Streamers(r.streamers)
    cbu = st.canBeUpgraded(streamer_id, r.gold, r.redstone)
    if cbu in [1, 2]:
        return jdumps({"code": cbu})
    gold = r.gold - st.getCost(streamer_id)
    redstone = r.redstone - st.st[streamer_id].redstone
    st.upgrade(streamer_id)
    db.updateUserData(set={'gold': gold, 'redstone': redstone, 'streamers': jdumps(st.exportLevels()), 'lastupdate': round(time())}, where={'user_id': uid})
    return jdumps({"code": 3, "info": st.st[streamer_id].toJSON(), "update": {"time": round(time()*1000), "money": formatNumber(gold), "points": formatNumber(redstone)}})

@app.route("/uptime")
def uptime():
    return jdumps({"uptime": round(time()-st)})

# Start
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)