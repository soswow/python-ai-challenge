
import unittest
from time import sleep

from planet_wars import PlanetWars, Planet, Fleet, pov, EndOfTheGame
from engine import Engine

class PlanetTest(unittest.TestCase):
    def setUp(self):
        self.pw = PlanetWars()

    def _game_over_true(self, max_turn):
        try:
            self.pw.is_game_over(max_turn)
            self.fail("Exception expected")
        except EndOfTheGame:
            pass

    def _game_over_false(self, max_turn):
        try:
            self.pw.is_game_over(max_turn)
        except EndOfTheGame:
            self.fail("Exception unexpected")

    def test_is_game_over(self):
        self.pw.turn = 10
        self._game_over_true(9)

        self.pw.turn = 1

        self._game_over_true(1)
        self.pw.planets.append(Planet(1,1,10,5,10,10))
        self._game_over_true(1)
        self.pw.planets.append(Planet(2,2,10,5,10,10))
        self._game_over_false(1)

        self.pw.planets = []
        self._game_over_true(1)
        self.pw.fleets.append(Fleet(1, 10, 1, 2, 10, 10))
        self._game_over_true(1)
        self.pw.fleets.append(Fleet(2, 10, 1, 2, 10, 10))
        self._game_over_false(1)


    def test_pov(self):
        self.assertEqual(1, pov(1,1))
        self.assertEqual(2, pov(2,1))
        self.assertEqual(1, pov(2,2))
        self.assertEqual(2, pov(1,2))
        self.assertEqual(0, pov(0,1))
        self.assertEqual(0, pov(0,2))



class EngineTest(unittest.TestCase):
    def setUp(self):
        self.eng = Engine(None, None, None)

    def add_planets(self):
        pl1 = Planet(0, 2, 35, 2, 0, 0)
        pl2 = Planet(1, 1, 7, 2, 10, 0)
        pl3 = Planet(2, 1, 15, 2, 0, 20)
        pl4 = Planet(3, 2, 0, 2, 10, 20)
        self.eng.pw.planets = [pl1, pl2, pl3, pl4]

    def add_some_stuff(self):
        enenmy_fleets = ((0, 1, 10), (0, 2, 20))
        my_fleets = ((1, 0, 5), (2, 0, 14), (2, 3, 16))
        self.add_planets()
        return enenmy_fleets, my_fleets

    def add_fleets_and_planets(self):
        enenmy_fleets, my_fleets = self.add_some_stuff()
        self.eng._departure(enenmy_fleets, my_fleets)

    def test_departure(self):
        self.add_fleets_and_planets()
        self.assertEqual(5, len(self.eng.pw.fleets))
        self.assertEqual(2, len(self.eng.pw.enemy_fleets))
        self.assertEqual(3, len(self.eng.pw.my_fleets))
        self.assertEqual(10, self.eng.pw.enemy_fleets[0].total_trip_length)

    def test_advancement(self):
        self.add_fleets_and_planets()
        pl5 = Planet(4,0,10,100,0,0)
        self.eng.pw.planets.append(pl5)
        check = self.eng.pw.my_fleets[0].turns_remaining
        self.eng._advancement()
        self.assertEqual(10, self.eng.pw.planets[4].num_ships)
        self.assertEqual(2, self.eng.pw.planets[3].num_ships)
        self.assertEqual(check - 1,self.eng.pw.my_fleets[0].turns_remaining)

    def test_get_participants(self):
        self.add_planets()
        fl1 = Fleet(1,38,1,0,10,0)
        fl2 = Fleet(2,2,3,0,10,0)
        self.eng.pw.fleets = [fl1, fl2]
        pl = self.eng.pw.planets[0]
        res = self.eng._get_participants(pl)
        self.assert_(1 in res and 2 in res)
        self.assertEqual(38, res[1])
        self.assertEqual(37, res[2])
        self.eng.pw.fleets = [fl1, fl2]
        self.eng.pw.fleets.append(Fleet(2,4,3,0,10,0))
        res = self.eng._get_participants(pl)
        self.assertEqual(41, res[2])

    def test_get_winner_second(self):
        partis = {1:10, 2:15, 0:5}
        winner, second = self.eng._get_winner_second(partis)
        self.assertEqual(2, winner.owner)
        self.assertEqual(1, second.owner)

        partis = {1:20, 2:15, 0:5}
        winner, second = self.eng._get_winner_second(partis)
        self.assertEqual(1, winner.owner)
        self.assertEqual(2, second.owner)

    def test_process_arrival(self):
        pl = Planet(0,1,40,1,0,0)
        winner = Fleet(2, 21)
        second = Fleet(2, 10)
        self.eng._process_arrival(pl, winner, second)
        self.assertEqual(11, pl.num_ships)

    def test_main(self):
        self.runner_ok = 0
        test_self = self
        class FakeRunner(object):
            def __init__(self, mapp, playback_file, timeout, max_turns, bot_cmd, bot_class):
                test_self.assertEqual(1, mapp)
                test_self.assertEqual(2, playback_file)
                test_self.assertEqual(3, timeout)
                test_self.assertEqual(4, max_turns)
                test_self.assertEqual(5, bot_cmd)
                test_self.assertEqual(6, bot_class)
                test_self.runner_ok += 1
                sleep(2)

            def run(self):
                test_self.runner_ok += 1

        self.runner_ok = False
        import engine
        engine.sys.argv = [0,1,2,3,4,5]
        engine.Runner = FakeRunner
        secs = engine.main(6)
        self.assertEqual(2, self.runner_ok)
        self.assertEqual(2, secs)

    def test_arrival(self):
        pass

#TODO Write tests for game_state_update parts methods.