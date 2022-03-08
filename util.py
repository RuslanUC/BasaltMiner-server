from json import loads as jloads
from random import choice
from datetime import datetime
from time import mktime, time

class World:
    def __init__(self, name, color, level):
        self.name = name
        self.color = color
        self.level = level

blocks = { # Блоки для каждой шахты
	1: [1, 2],
	2: [4, 5, 6],
	3: [24, 9],
	4: [11, 12, 13, 14],
	5: [15, 16, 17],
	6: [24, 20, 21, 23],
	7: [25, 26, 27],
	8: [46, 47, 48, 59],
	9: [28, 29, 30, 31],
	10: [50, 51],
	11: [35, 32, 33],
	12: [35, 36, 37],
	13: [38, 40, 53, 54],
	14: [41, 39, 62],
	15: [42, 43],
	16: [44, 55, 56],
	17: [58]
}

worlds = [ # Шахты
	World("Земля", "5D8052", 1),
	World("Пустыня", "E5B017", 3),
	World("Джунгли", "17FF00", 5),
	World("Терракота", "C26B0E", 8),
	World("Лес", "539D08", 13),
	World("Деревня", "B0B802", 18),
	World("Шахта", "C1C1C1", 26),
	World("Океан", "0041CD", 34),
	World("Глубинная шахта", "666666", 18),
	World("Долина песка душ", "463425", 45),
	World("Адский лес", "832603", 50),
	World("Ад", "F24200", 57),
	World("Бастион", "34302F", 64),
	World("Базальтовые дельты", "533C36", 72),
	World("Обсидиан", "2E0D34", 81),
	World("Энд", "AC08CA", 90),
	World("Бедрок", "000000", 100),
]

n = 10
levels = {}
for i in range(100): # Расчёт уровней
	levels[i+1] = n
	if i % 5 != 0:
		n *= 2
	else:
		n *= 1.5

biba = {
	1: 100,
	2: 98,
	3: 96,
	4: 94,
	5: 92,
	6: 90,
	7: 88,
	8: 86,
	9: 84,
	10: 82,
	11: 80,
	12: 75,
	13: 70,
	14: 65,
	15: 60,
	16:	55,
	17: 50,
	18: 45,
	19: 40,
	20: 35,
	21: 30,
	22: 30,
	23: 30,
	24: 30,
	25: 25,
	26: 25,
	27: 25,
	28: 25,
	29: 25,
	30: 25
}

def getBlock(world): # Получение случайного блока для шахты
	return choice(blocks[world])

def getWorld(block): # Получения шахты по блоку
	return list(blocks.keys())[list(blocks.values()).index([x for x in list(blocks.values()) if block in x][0])]

def getBlockBreakTime(block, level): # Получение времени разрушения блока
	if block != 58:
		t = 1500+getWorld(block)*400-level*100
		if t < 750:
			return 750
		return t
	return 86400*31*12*1000 # 1 year YEP

def getBibaPercentage(lenght):
	return biba[lenght+1]

def getLevelPrice(level):
	return levels[level]

def getWorlds(level): # Получение всех миров
	w = []
	for world in worlds:
		if world.level <= level:
			w.append([worlds.index(world)+1, world.name, world.color])
		else:
			w.append(world.level)
	return w

def worldAvailable(level, world):
	return level >= worlds[world-1].level

def formatNumber(num): # Преобразования чисел в сокращённый вид
	if num < 10**3:
		return round(num, 1)
	elif 10**6 > num >= 10**3:
		return str(round(num/10**3, 1))+"K" # thousand: kilo-
	elif 10**9 > num >= 10**6:
		return str(round(num/10**6, 1))+"M" # million: mega-
	elif 10**12 > num >= 10**9:
		return str(round(num/10**9, 1))+"B" # billion: giga-
	elif 10**15 > num >= 10**12:
		return str(round(num/10**12, 1))+"T" # trillion: tera-
	elif 10**18 > num >= 10**15:
		return str(round(num/10**15, 1))+"Q" # quadrillion: peta-
	elif 10**21 > num >= 10**18:
		return str(round(num/10**18, 1))+"E" # quintillion: exa-
	elif 10**24 > num >= 10**21:
		return str(round(num/10**21, 1))+"Z" # sextillion: zetta-
	elif 10**27 > num >= 10**24:
		return str(round(num/10**24, 1))+"Y" # septillion: yotta-
	elif 10**30 > num >= 10**27:
		return str(round(num/10**27, 1))+"O" # octillion: ?
	elif num >= 10**30:
		return "Много" 
	else:
		return "???"

def isWin(s1, s2):
	return [True if u-o > 0 else False for u,o in zip(jloads(s1), jloads(s2))].count(True) >= 2

def getTS(): # Получение метки времени текущего дня
	n = datetime.now()
	return mktime(datetime(year=n.year, month=n.month, day=n.day).timetuple())

class LogEntry:
    def __init__(self, path, time, resp_code):
        self.path = path
        self.time = time-1640995200
        self.resp_code = resp_code

class Log:
    def __init__(self, uid):
        self.log_entries = []

    def addLog(self, log_entry):
        self.log_entries.append(log_entry)

class Logs:
    logs = {}

    def addLog(self, uid, log_entry):
        if uid in self.logs:
            self.logs[uid].addLog(log_entry)
        else:
            l = Log(uid)
            l.addLog(log_entry)
            self.logs[uid] = l

    def exportSQLdata(self):
        sql = []
        _logs = self.logs.copy()
        self.logs.clear()
        for uid, logs in _logs.items():
            for log in logs.log_entries:
                sql.append((uid, log.path, log.time, log.resp_code))
        return sql

    def __len__(self):
        return len(self.logs)

class RTL:
	def __init__(self):
		self.req = {}

	def isLimited(self, n, l):
		if n in self.req:
			t = time()-self.req[n]
			self.req[n] = time()
			if t > l:
				return False
		else:
			self.req[n] = time()
		return True