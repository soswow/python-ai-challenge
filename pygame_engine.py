import pygame
import sys
import os
import os.path
import subprocess


from utils import Debuggable, count_time_take, set_default_debug

from planet_wars import PlanetWars, Fleet

MAPS_DIR = "maps"

class PlanetWarViz(Debuggable):
    def __init__(self, data=None):
        self.data = data
        self.surface = None
        self.width, self.height = 640, 480
        self.k = None
        self.growth_size_k = 5
        self.border_padding = 30
        self.debug_name = "viz"

    def update_k_and_height(self):
        self.debug("update_k_and_height")
        max_x = max([p.x for p in self.state.planets])
        max_y = max([p.y for p in self.state.planets])
        self.debug("max_x = %d, max_y = %d" % (max_x, max_y))
        self.k = (self.width - self.border_padding) / max_x
        self.debug("k = %.2f" % self.k)
        self.height = max_y * self.k

    def make_surface(self):
        pygame.init()
        width = self.width + self.border_padding
        height = self.height + (self.border_padding * 2)
        self.surface = pygame.display.set_mode((width, height))
        self.surface.fill((255,255,255))
        pygame.display.update()

    def draw_state(self, state=None):
        if state:
            self.state = state
        if not self.k:
            self.update_k_and_height()
        if not self.surface:
            self.make_surface()

        map(self.draw_planet, self.state.planets)

    def input(self, events):
       for event in events:
          if event.type == pygame.QUIT:
             sys.exit(0)

    def draw_planet(self, p):
        pos = (p.x * self.k + self.border_padding, p.y * self.k + self.border_padding)
        rect = pygame.draw.circle(self.surface, (100, 100, 100, 0.5), pos, p.growth_rate * self.growth_size_k)
        pygame.display.update(rect)

class Engine(Debuggable):
    def __init__(self, mapp, enemy_cmd, my_bot_class, timeout=1000, max_turns=200):
        super(Engine, self).__init__()
        self.mapp = mapp
        self.timeout = timeout
        self.max_turns = max_turns
        self.enemy_cmd = enemy_cmd
        self.pw = PlanetWars()
        self.my_bot_class = my_bot_class
        self.turn = 0
        self.debug_name = "engine"
        self.playback = ""

    def load_map_data(self):
        f = open(self.mapp)
        data = "\n".join([line for line in f])
        f.close()
        return data

    def load_init_state(self):
        '''load map data and make initial game state'''
        self.pw = PlanetWars()
        self.pw.load_data(self.load_map_data())
        self.playback = ":".join(["%.10f,%.10f,%d,%d,%d" % (p.x, p.y, p.owner, p.num_ships, p.growth_rate)
                                  for p in self.pw.planets]) + "|"

    def _departure(self, enemy_fleets, my_fleets):
        for i, fleets in enumerate((my_fleets, enemy_fleets,)):
            for src, dest, num_ships in fleets:
                dist = self.pw.distance(src,dest)
                self.pw.fleets.append(Fleet(i+1,num_ships,src,dest,dist,dist))
                #TODO make check for ships availability
                self.pw.planets[src].num_ships -= num_ships
                
    def _advancement(self):
        for fl in self.pw.fleets:
            fl.turns_remaining -= 1
        for pl in self.pw.planets:
            if pl.owner > 0:
                pl.num_ships += pl.growth_rate

    def _get_participants(self, pl):
        participants = {pl.owner:pl.num_ships}
        updated_fleets = []
        for fl in self.pw.fleets:
            if fl.dest == pl.id and fl.turns_remaining <= 0:
                if not fl.owner in participants:
                    participants[fl.owner] = fl.num_ships
                else:
                    participants[fl.owner] += fl.num_ships
            else:
                updated_fleets.append(fl)
        self.pw.fleets = updated_fleets
        return participants

    def _get_winner_second(self, participants):
        winner = Fleet(0, 0)
        second = Fleet(0, 0)
        for k, v in participants.items():
            if v > second.num_ships:
                if v > winner.num_ships:
                    second = winner
                    winner = Fleet(k, v)
                else:
                    second = Fleet(k, v)
        return winner, second

    def _process_arrival(self, pl, winner, second):
        if winner.num_ships > second.num_ships:
            pl.num_ships = winner.num_ships - second.num_ships
            pl.owner = winner.owner
        else:
            pl.num_ships = 0

    def _arrival(self):
        for pl in self.pw.planets:
            participants = self._get_participants(pl)
            winner, second = self._get_winner_second(participants)
            self._process_arrival(pl, winner, second)

    def game_state_update(self, enemy_fleets, my_fleets):
        self._departure(enemy_fleets, my_fleets)
        self._advancement()
        self._arrival()

    @property
    def winner(self):
        return "Old" if self.pw.winner == 2 else "New" if self.pw.winner == 1 else "Draw"

    def run(self):
        self.load_init_state()
        process = subprocess.Popen(self.enemy_cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        stdin, stdout = process.stdin, process.stdout
        my_bot = self.my_bot_class()
        my_bot.via_standart_io = False
        while 1:
            self.turn += 1
            self.print_it("Turn #%d" % self.turn)
            if self.pw.is_game_over():
                return

            stdin.write(self.pw.repr_for_enemy() + "go\n")
            stdin.flush()
            enemy_orders = []
            while True:
                line = stdout.readline().replace("\n","")
                self.debug("> %s" % line)
                self.print_it("> %s" % line)
                if line.startswith("go"):
                    break
                enemy_orders.append(map(int, line.split(" ")))
            #self.debug("enemy orders:\n %s" % output)
            my_bot.load_data(repr(self.pw))
            my_bot.do_turn()
            print_it("\n".join(["< %d %d %d" % order for order in my_bot.real_orders]))
            self.game_state_update(enemy_orders, my_bot.real_orders)
            self.print_play_back()


    def print_play_back(self):
        planets = ["%d.%d" % (p.owner, p.num_ships) for p in self.pw.planets]
        fleets = ["%d.%d.%d.%d.%d.%d" % (f.owner, f.num_ships, f.src, f.dest, f.total_trip_length, f.turns_remaining)
                  for f in self.pw.fleets]
        self.playback += ",".join(planets + fleets) + ":"

class Runner(object):
    def __init__(self, mapp, playback_file, timeout, max_turns, bot_cmd, bot_class):
        self.mapp = mapp
        self.playback_file = playback_file
        self.timeout, self.max_turns = int(timeout), int(max_turns)
        self.bot_cmd = bot_cmd
        self.bot_class = bot_class

    @count_time_take
    def play_map(self, mapp, debug_enabled=True):
        engine = Engine(os.path.join(MAPS_DIR, mapp), self.bot_cmd, self.bot_class, self.timeout, self.max_turns)
        engine.debug_enabled = debug_enabled
        engine.run()
        engine.debug("Winner is %s" % engine.winner)
        if debug_enabled:
            f = open(self.playback_file, 'w')
            f.write(engine.playback)
            f.close()
        return engine.winner, engine.turn

    def run(self):
        debug_enabled = True
        maps = [self.mapp]
        if self.mapp == "ALL":
            maps = sorted(os.listdir(MAPS_DIR), key=lambda p: int(p[3:-4]))
            debug_enabled = False

        set_default_debug(debug_enabled)

        for mapp in maps:
            winner, in_turns, time_take = self.play_map(mapp, debug_enabled)
            print "%s - %s (%d turns in %s seconds)" % (mapp, winner, in_turns, time_take)

@count_time_take
def main(bot_class):
    args = sys.argv
    assert len(args) > 5
    #Must be 5 arguments: [mapp name|ALL] [file for java playback] [timeout] [max turns] [enemy script]
    args.append(bot_class)
    runner = Runner(*args[1:])
    runner.run()

if __name__ == "__main__":
    print "Lets game begin!"
    from my_bots import MyBot6 as bot_class
    time_take = main(bot_class)
    print "Game take %d minutes %d seconds" % (time_take / 60, time_take % 60)
  