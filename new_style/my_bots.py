#!/usr/bin/env python

import math

from utils import main_util
from planet_wars import Bot

class MyBot6(Bot):
    def __init__(self):
        super(MyBot6, self).__init__()
        self.debug_name = "bot6"

    def get_enemy_planets(self, src):
        planets =  self.enemy_planets + []
        planets.sort(key=lambda a: self.simple_estimate(a, src))
        return planets

    def all_planets(self, src):
        planets =  filter(lambda p: p.id != src.id, self.planets)
        planets.sort(key=lambda a: self.simple_estimate(a, src))
        return planets

    def simple_estimate(self, src, dst):
        need = float(dst.num_ships)
        owner = dst.owner
        if owner > 1:
            need += self.distance(src.id, dst.id) * dst.growth_rate

        enemy_fleet_count = [fleet.num_ships for fleet in self.enemy_fleets if fleet.dest == dst.id]
        need += sum(enemy_fleet_count)

        my_fleet = [fleet for fleet in self.my_fleets if fleet.dest == dst.id]
        my_fleet.sort(key=lambda fleet: fleet.turns_remaining)
        for fleet in my_fleet:
            if owner > 1:
                need += dst.growth_rate * fleet.turns_remaining
            need -= fleet.num_ships

            if need <= 0:
                break

        return int(math.ceil(need * 1.10))

    def get_weight(self, src, dst):
        weight = dst.num_ships
        return weight

    def weighted_planets(self, src):
        self.debug("Weighted_planets")
        planets = []
        for dst in self.planets:
            if src == dst:
                continue
            weight = self.get_weight(src, dst)
            planets.append((weight, dst,))
        planets.sort(key=lambda p: p[0], reverse=True)
        return [pl[1] for pl in planets]

    def do_turn(self):
        self.attack(self.weighted_planets, self.simple_estimate)

if __name__ == "__main__":
    main_util(MyBot6)
  
