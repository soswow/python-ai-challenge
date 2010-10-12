#!/usr/bin/env python
#

from utils import Debuggable

from math import ceil, sqrt
from sys import stdout

def pov(owner, who):
    if who == 1 or owner == 0:
        return owner
    else:
        return 2 if owner == 1 else 1

class Fleet(object):
    def __init__(self, owner, num_ships, source_planet=-1, destination_planet=-1,
                 total_trip_length=-1, turns_remaining=-1):
        self.owner = owner
        self.num_ships = num_ships
        self.src = source_planet
        self.dest = destination_planet
        self.total_trip_length = total_trip_length
        self.turns_remaining = turns_remaining

    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return self.repr_for()

    def repr_for_enemy(self):
        return self.repr_for(2)

    def repr_for(self, who=1):
        return "F %d %d %d %d %d %d\n" % (pov(self.owner, who), self.num_ships,
                                          self.src, self.dest,
                                          self.total_trip_length, self.turns_remaining)

class Planet(object):
    def __init__(self, planet_id, owner, num_ships, growth_rate, x, y):
        self.id = planet_id
        self.owner = owner
        self.num_ships = num_ships
        self.growth_rate = growth_rate
        self.x = x
        self.y = y

    def add_ships(self, amount):
        self.num_ships += amount

    def remove_ships(self, amount):
        self.num_ships -= amount

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.repr_for()

    def repr_for_enemy(self):
        return self.repr_for(2)

    def repr_for(self, who=1):
        return "P %f %f %d %d %d\n" % (self.x, self.y, pov(self.owner, who), self.num_ships, self.growth_rate) 

    def __eq__(self, other):
        return self.id == other.id

class PlanetWars(Debuggable):
    def __init__(self, game_state=None):
        super(PlanetWars, self).__init__()
        self.planets = []
        self.fleets = []
        self.turn = 0
        self.real_orders = []
        self.game_state = game_state
        self.debug_name = "planetwars"
        self.via_standart_io = True
        if game_state:
            self.parse_game_state()

    def load_data(self, game_state):
        self.game_state = game_state
        self.real_orders = []
        self.parse_game_state()

    @property
    def num_planets(self):
        return len(self.planets)

    def get_planet(self, planet_id):
        return self.planets[planet_id]

    @property
    def num_fleets(self):
        return len(self.fleets)

    def get_fleet(self, fleet_id):
        return self.fleets[fleet_id]

    def _objects_by_owners(self, objects, owners):
        return filter(lambda p: p.owner in owners, objects)

    def _planets_by_owners(self, *owners):
        return self._objects_by_owners(self.planets, owners)

    @property
    def my_planets(self):
        return self._planets_by_owners(1)

    @property
    def neutral_planets(self):
        return self._planets_by_owners(0)

    @property
    def enemy_planets(self):
        return self._planets_by_owners(2)

    @property
    def not_my_planets(self):
        return self._planets_by_owners(0, 2)

    def _fleets_by_owners(self, *owners):
        return self._objects_by_owners(self.fleets, owners)

    @property
    def my_fleets(self):
        return self._fleets_by_owners(self, 1)

    @property
    def enemy_fleets(self):
        return self._fleets_by_owners(self, 2)

    def __repr__(self):
        return "".join([str(pl) for pl in (self.planets + self.fleets)])

    def repr_for_enemy(self):
        return "".join([obj.repr_for_enemy() for obj in (self.planets + self.fleets)])

    def distance(self, src_id, dest_id):
        src = self.planets[src_id]
        dest = self.planets[dest_id]
        dx = src.x - dest.x
        dy = src.y - dest.y
        return int(ceil(sqrt(dx * dx + dy * dy)))

    def issue_order(self, src_id, dest_id, num_ships):
        order = (src_id, dest_id, num_ships)
        self.real_orders.append(order)
        if self.via_standart_io:
            self.debug("Order: %d %d %d" % order)
            stdout.write("%d %d %d\n" % order)
            stdout.flush()

    def total_ships(self, player_id):
        objs = self._planets_by_owners(player_id) + self._fleets_by_owners(player_id)
        return sum([obj.num_ships for obj in objs])

    def is_alive(self, player_id):
        return self.total_ships(player_id) > 0

    def is_game_over(self):
        '''check for end of the game'''
        return not all([self.is_alive(player) for player in range(1,3)]) or self.turn > self.max_turns

    @property
    def winner(self):
        pl1_ships = self.total_ships(1)
        pl2_ships = self.total_ships(2)
        self.debug("Player1: %d ships, Player2: %d ships" % (pl1_ships, pl2_ships))
        if pl1_ships > pl2_ships:
            return 1
        elif pl2_ships > pl1_ships:
            return 2
        else:
            return 0

    def load_turn_finish(self, map_data):
        turn_msg = "# %d" % self.turn
        self.debug(turn_msg)
        self.debug(turn_msg, 'server-io')
        self.turn += 1
        self.load_data(map_data)
        self.do_turn()
        self.finish_turn()

    def parse_game_state(self):
        self.planets = []
        self.fleets = []
        planet_id = 0

        for line in self.game_state.split("\n"):
            line = line.split("#")[0] # remove comments
            tokens = line.split(" ")
            if len(tokens) == 1:
                continue
            if tokens[0] == "P":
                if len(tokens) != 6:
                    return 0
                p = Planet(planet_id, # The ID of this planet
                           int(tokens[3]), # Owner
                           int(tokens[4]), # Num ships
                           int(tokens[5]), # Growth rate
                           float(tokens[1]), # X
                           float(tokens[2])) # Y
                planet_id += 1
                self.planets.append(p)
            elif tokens[0] == "F":
                if len(tokens) != 7:
                    return 0
                f = Fleet(int(tokens[1]), # Owner
                          int(tokens[2]), # Num ships
                          int(tokens[3]), # Source
                          int(tokens[4]), # Destination
                          int(tokens[5]), # Total trip length
                          int(tokens[6])) # Turns remaining
                self.fleets.append(f)
            else:
                return 0
        return 1

    def finish_turn(self):
        stdout.write("go\n")
        stdout.flush()

    def issue_and_update(self, src, dest, ships):
        p = self.get_planet(src)
        total = p.num_ships
        if total < ships:
            self.debug("Bad order %d -> %d with %d, but have %d. Aborting" % (src, dest, ships, total))
            return
        self.debug("Sending %d ships from %d to %d" % (ships, src, dest))
        self.issue_order(src, dest, ships)
        #Updating planet
        p.num_ships = total - ships
        #Making fleet
        d = self.distance(src, dest)
        new_fleet = Fleet(1, ships, src, dest, d, d)
        self.fleets.append(new_fleet)



class Bot(PlanetWars):
    def __init__(self):
        super(Bot, self).__init__()
        self.debug_name = "bot"
        self.ships_key_getter = lambda a: a.num_ships

    def do_turn(self):
        pass

    def simple_estimate(self, src, dst):
        need = float(dst.num_ships)
        owner = dst.owner
        if owner > 1:
            need += self.distance(src.id, dst.id) * dst.growth_rate

        enemy_fleet_count = [fleet.num_ships for fleet in self.enemy_fleets if fleet.destination_planet == dst.id]
        need += sum(enemy_fleet_count)

        my_fleet = [fleet for fleet in self.my_fleets if fleet.destination_planet == dst.id]
        my_fleet.sort(key=lambda fleet: fleet.turns_remaining)
        for fleet in my_fleet:
            if owner > 1:
                need += dst.growth_rate * fleet.turns_remaining
            need -= fleet.num_ships

            if need <= 0:
                break

        return int(math.ceil(need * 1.10))

    def all_other_planets(self, src):
        self.debug("all_other_tables")
        planets = self.not_my_planets + []
        planets.sort(key=self.ships_key_getter)
        self.debug("all other planets %s" % [s.id for s in planets])
        return planets

    @property
    def my_sorted_planets(self):
        planets = self.my_planets + []
        planets.sort(key=self.ships_key_getter, reverse=True)
        self.debug("my planets %s" % [s.id for s in planets])
        return planets

    def attack(self, choose_targets, estimate, give_portion=0.66):
        self.debug("Attacking.")
        for src in self.my_sorted_planets:
            init_was = src.num_ships
            can_give = float(init_was * give_portion)
            self.debug("My planet %d can give %d ships" % (src.id, can_give))
            for dest in choose_targets(src):
                ships_to_send = estimate(src, dest)
                if ships_to_send > 0 and can_give >= ships_to_send:
                    self.debug("Sending %d ships to %d planet" % (ships_to_send, dest.id))
                    self.issue_and_update(src.id, dest.id, ships_to_send)
                    can_give -= ships_to_send
            self.debug("From %d in total sent %d ships" % (init_was - src.num_ships, src.id))

