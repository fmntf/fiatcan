import unittest
import sys
sys.path.insert(0, "../")
from TextMessage import TextMessage


class TextMessageTest(unittest.TestCase):

    tm = TextMessage()

    def test_normalizes_strings(self):
        test = {
            "Menu ": "MENU",
            "Menù": "MENU",
            "A, B": "A B",
            "A,B": "A B",
        }
        for str_in, str_out in test.items():
            self.assertEqual(self.tm.normalize_string(str_in), str_out)

    def test_encodes_menu(self):
        [can1, can2] = self.tm.encode_instpanel("ABCDEFGHIJ", True)

        self.assertEqual(can1.arbitration_id, 0xA394021)
        self.assertEqual(self.byte_to_string(can1.data), "101A30D38F411493")

        self.assertEqual(can2.arbitration_id, 0xA394021)
        self.assertEqual(self.byte_to_string(can2.data), "111A515000000000")

    def test_encodes_string(self):
        [can1, can2] = self.tm.encode_instpanel("ABCDEFGHIJ", False)

        self.assertEqual(can1.arbitration_id, 0xA394021)
        self.assertEqual(self.byte_to_string(can1.data), "101630D38F411493")

        self.assertEqual(can2.arbitration_id, 0xA394021)
        self.assertEqual(self.byte_to_string(can2.data), "1116515000000000")

    def byte_to_string(self, bytearray):
        return ''.join('{:02x}'.format(x) for x in bytearray).upper()


if __name__ == '__main__':
    unittest.main()


