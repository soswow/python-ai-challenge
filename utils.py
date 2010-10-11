import logging
import logging.handlers
from datetime import datetime
from os.path import join as path_join
from functools import wraps

DEBUG = True
DEFAULT_SCOPE = "default"
DEFAULT_DEBUG_ENABLE_FILE = "is_debug_enabled"
LOGS_DIR = "logs"

loggers = {}
def getlogger(ext):
    global loggers
    if ext not in loggers:
        logger = logging.getLogger(ext)
        hdlr = logging.handlers.RotatingFileHandler(path_join(LOGS_DIR, 'log-%s.txt' % ext),'a',20097152,20)
        formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s"%(message)s"','%Y-%m-%d %a %H:%M:%S')

        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.DEBUG)
        loggers[ext] = logger

    return loggers[ext]

def debug_force(msg):
    debug(msg, 'force')

def debug(msg, ext=None):
    if not ext:
        ext = DEFAULT_SCOPE
    if DEBUG:
        logger = getlogger(ext)
        logger.debug(msg)

def set_default_debug(is_enabled):
    f = open(path_join(LOGS_DIR, DEFAULT_DEBUG_ENABLE_FILE), 'w')
    f.write(str(int(is_enabled)))
    f.close()

def _read_is_debug_enabled():
    f = open(path_join(LOGS_DIR, DEFAULT_DEBUG_ENABLE_FILE))
    is_enabled = bool(int(f.read()))
    f.close()
    return is_enabled

class Debuggable(object):
    def __init__(self):
        self.debug_enabled = _read_is_debug_enabled()
        self.debug_name = "default"
        
    def debug(self, msg, ext=None):
        if self.debug_enabled:
            ext = self.debug_name + ("-" + ext if ext else "")
            debug(msg, ext)

def fleet_needed(pw, dest):
    debug_force("Fleet_needed for %d (%d)" % (dest.PlanetID(), dest.Owner()))
    all_fleets = pw.MyFleets() + pw.EnemyFleets()
    all_fleets = [fleet for fleet in all_fleets if fleet.DestinationPlanet() == dest.PlanetID()]
    all_fleets.sort(key=lambda fleet: fleet.TurnsRemaining())

    force = -float(dest.NumShips())
    debug_force("Init force = %d" % force)

    in_n_turns = None
    my_fleet_on_way = False
    #prev_fleet = None
    for fleet in all_fleets:
        fleet_num = fleet.NumShips()
        debug_force("Fleet %d -> %d (%d) with %d ships" % (fleet.SourcePlanet(),
                                             fleet.DestinationPlanet(),
                                             fleet.Owner(),
                                             fleet_num))
        if fleet.Owner() == 1:
            force += fleet_num
            my_fleet_on_way = True
        else:
            force -= fleet_num
        debug_force("Force now %d" % force)

        growth = dest.GrowthRate()
        debug_force("Growth %d" % growth)
        if force >= 0:
            force += growth
        else:
            force -= growth
        debug_force("Force now %d" % force)
        in_n_turns = fleet.TotalTripLength()
        #prev_fleet = fleet

    if not my_fleet_on_way:
        force *= 1.20

    debug_force("Force of dest %d = %d (+20%%)" % (dest.PlanetID(), force))
    return -force if force < 0 else 0, in_n_turns

def print_server_io(map_data):
    i = 0
    k = True
    for line in map_data.split("\n"):
        if line.startswith("F"):
            if k:
                i=0
                k=False
            parts = line.split(" ")
            line = "%s o%d n%d s%d -> d%d t%d r%d" % tuple([parts[0]] + map(int, parts[1:]))
        line = "%.2d %s" % (i, line)
        i += 1
        debug(line, 'server-io')

def main_util(bot_class):
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        debug("Let's game begin!!")
        run(bot_class)
    except KeyboardInterrupt:
        print 'ctrl-c, leaving ...'

def count_time_take(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        time_start = datetime.now()
        res = f(*args, **kwds)
        time_take = (datetime.now() - time_start).seconds
        if res is None:
            return time_take
        elif isinstance(res, tuple):
            return res + (time_take,)
        else:
            return res, time_take
    return wrapper

def run(bot_class):
    map_data = ''
    bot = bot_class()
    i = 0
    while(True):
        current_line = raw_input()
        if len(current_line) >= 2 and current_line.startswith("go"):
            try:
                i+=1
                bot.load_turn_finish(map_data)
            except Exception, e:
                debug("Exception: %s" % e, 'error')
            map_data = ''
        else:
            map_data += current_line + '\n'