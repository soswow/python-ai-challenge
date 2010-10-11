import unittest
from time import sleep

from utils import count_time_take, Debuggable
import utils

class UtilsTest(unittest.TestCase):
    @count_time_take
    def fake_method(self, case):
        if case == 1:
            return 10, 20
        elif case == 2:
            return 30
        elif case == 3:
            return
        elif case == 4:
            sleep(2.3)
            return

    def test_time_take_wrapper1(self):
        a,b,secs = self.fake_method(1)
        self.assertEqual(10, a)
        self.assertEqual(20, b)
        self.assertEqual(0, secs)

    def test_time_take_wrapper2(self):
        a,secs = self.fake_method(2)
        self.assertEqual(30, a)
        self.assertEqual(0, secs)

    def test_time_take_wrapper3(self):
        secs = self.fake_method(3)
        self.assertEqual(0, secs)

    def test_time_take_wrapper4(self):
        secs = self.fake_method(4)
        self.assertEqual(2, secs)

class DebuggerTest(unittest.TestCase):
    
    def test_debug_enable(self):
        class Debug(Debuggable):
            def __init__(self):
                super(Debug, self).__init__()

        def inner_test(sign, should_be):
            utils.set_default_debug(sign)
            d = Debug()
            self.assertEqual(should_be, d.debug_enabled)

        inner_test(1, True)
        inner_test(0, False)
        inner_test(True, True)
        inner_test(False, False)
        
if __name__ == '__main__':
    unittest.main()
