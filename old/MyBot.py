#!/usr/bin/env python
#

"""
// The DoTurn function is where your code goes. The PlanetWars object contains
// the state of the game, including information about all planets and fleets
// that currently exist. Inside this function, you issue orders using the
// pw.IssueOrder() function. For example, to send 10 ships from planet 3 to
// planet 8, you would say pw.IssueOrder(3, 8, 10).
//
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own. Check out the tutorials and articles on the contest website at
// http://www.ai-contest.com/resources.
"""
try:
    from utils import Debuggable
except:
    import sys
    from os import path
    sys.path.append(path.join(sys.path[0], ".."))
    from utils import Debuggable
import math

from PlanetWars import PlanetWars

class Debug(Debuggable):
    def __init__(self):
        super(Debug, self).__init__()
        self.debug_name = "bot1"

debugger = Debug()

def main():
    map_data = ''
    turn = 0

    try:
        while(True):
            current_line = raw_input()
            #debug("-> %s" % current_line, 'server')
            if len(current_line) >= 2 and current_line.startswith("go"):
                debugger.debug("# %d" % turn)
                pw = PlanetWars(map_data)
                DoTurn(pw)
                #debug("Answer is sent.", 'server')
                pw.FinishTurn()
                turn += 1
                map_data = ''
            else:
                map_data += current_line + '\n'
    except Exception, e:
        debugger.debug(e, "error")
    debugger.debug("The End!")

turn = 0
def DoTurn(pw):

    ships_key_getter=lambda a: a.NumShips()
    my_planets = pw.MyPlanets()
    my_planets.sort(key=ships_key_getter, reverse=True)
    other_planets = pw.NotMyPlanets()
    other_planets.sort(key=ships_key_getter)

    for p in my_planets:
        counter = 0
        can_give = float(p.NumShips() * 0.66)
        #debug("My Planet %d, init can give %f" % (p.PlanetID(), can_give))
        for op in other_planets:
            need = float(op.NumShips())
            owner = op.Owner()
            if owner > 1:
                need += pw.Distance(p.PlanetID(), op.PlanetID()) * op.GrowthRate()

            enemy_fleet_count = [fleet.NumShips() for fleet in pw.EnemyFleets() if fleet.DestinationPlanet() == op.PlanetID()]
            need += sum(enemy_fleet_count)

            my_fleet = [fleet for fleet in pw.MyFleets() if fleet.DestinationPlanet() == op.PlanetID()]
            my_fleet.sort(key=lambda fleet: fleet.TurnsRemaining())
            pluss = need
            for fleet in my_fleet:
                accum = 0
                if owner > 1:
                    accum = op.GrowthRate() * fleet.TurnsRemaining()
                    pluss += accum
                pluss -= fleet.NumShips()

                if pluss <= 0:
                    break
                    
            if pluss < 0:
#                debug("There will be enought help. Don't need us.")
                continue

            need = pluss * 1.10

            ships_to_send = int(math.ceil(need))
            if ships_to_send > 0 and can_give >= ships_to_send:
                pid, opid, num = p.PlanetID(), op.PlanetID(), ships_to_send
                has_now = pw.GetPlanet(pid).NumShips()
                #debug("src %d, dst %d, ships %d\t %d has %d ships" % (pid, opid, num, pid, has_now))
                pw.IssueOrder(pid, opid, num)
                counter += num
                can_give -= num
        debugger.debug("%d sent from %d" % (counter, p.PlanetID()))


if __name__ == '__main__':
  try:
    import psyco
    psyco.full()    
  except ImportError:
    pass
  try:
    debugger.debug("Let's game begin!!")
    main()
  except KeyboardInterrupt:
    print 'ctrl-c, leaving ...'
