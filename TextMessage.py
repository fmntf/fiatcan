import math
import time
import unidecode
from can import Message
from textwrap import wrap
from FiatProtocol import *


class TextMessage:

    string_end = "000000"
    field_separator = "111111"
    char_map = {
        "0": "000001",
        "1": "000010",
        "2": "000011",
        "3": "000100",
        "4": "000101",
        "5": "000110",
        "6": "000111",
        "7": "001000",
        "8": "001001",
        "9": "001010",
        ".": "001011",
        "A": "001100",
        "B": "001101",
        "C": "001110",
        "D": "001111",
        "E": "010000",
        "F": "010001",
        "G": "010010",
        "H": "010011",
        "I": "010100",
        "J": "010101",
        "K": "010110",
        "L": "010111",
        "M": "011000",
        "N": "011001",
        "O": "011010",
        "P": "011011",
        "Q": "011100",
        "R": "011101",
        "S": "011110",
        "T": "011111",
        "U": "100000",
        "V": "100001",
        "W": "100010",
        "X": "100011",
        "Y": "100100",
        "Z": "100101",
        "ñ": "100110",
        "ç": "100111",
        " ": "101000",
        "Ğ": "101001",
        "i": "101010",
        "j": "101011",
        "§": "101100",
        "À": "101101",
        "Ä": "101110",
        "ŭ": "101111",
        "Ü": "110000",
        "_": "110010",
        "?": "110101",
        "°": "110110",
        "!": "110111",
        "+": "111000",
        "-": "111001",
        ":": "111010",
        "/": "111011",
        "#": "111100",
        "*": "111101",
    }

    bitstrings_map = {}

    instpanel_menu_prefix1 = "0001000000011010"
    instpanel_menu_prefix2 = "0001000100011010"
    instpanel_text_prefix1 = "0001000000010110"
    instpanel_text_prefix2 = "0001000100010110"

    bus = None

    def __init__(self, bus):
        self.bus = bus
        for key, value in self.char_map.items():
            self.bitstrings_map[value] = key

    def encode_instpanel(self, message, is_menu):
        bitstring = self.encode_string(message).ljust(96, '0')

        if is_menu:
            line1 = self.instpanel_menu_prefix1 + bitstring[:48]
            line2 = self.instpanel_menu_prefix2 + bitstring[48:]
        else:
            line1 = self.instpanel_text_prefix1 + bitstring[:48]
            line2 = self.instpanel_text_prefix2 + bitstring[48:]

        can1 = Message(arbitration_id=CANID_BM_TEXT_MESSAGE, data=self.bitstring_to_bytes(line1))
        can2 = Message(arbitration_id=CANID_BM_TEXT_MESSAGE, data=self.bitstring_to_bytes(line2))

        return can1, can2

    def encode_music(self, track, artist, folder=None):
        bitstring = ""
        if folder:
            bitstring += self.encode_string(folder)
        else:
            bitstring += self.string_end
        bitstring += self.field_separator

        bitstring += self.encode_string(artist)
        bitstring += self.field_separator

        bitstring += self.encode_string(track, 18)

        messages = []
        nmessages = math.ceil(len(bitstring)/48) -1
        i = 0
        for bits in wrap(bitstring, 48):
            if len(bits) < 48:
                bits = bits.ljust(48, '0')
            bits = ba(hex='0x{}{}2A'.format(nmessages, i)).bin + bits
            messages.append(
                Message(arbitration_id=CANID_BM_TEXT_MESSAGE, data=self.bitstring_to_bytes(bits))
            )
            i += 1

        return messages

    def normalize_string(self, string, maxlen=14):
        string = string.rstrip().upper()
        if len(string) > maxlen:
            string = string[:maxlen]

        chunks = []
        for char in string:
            if char in self.char_map:
                chunks.append(char)
            else:
                decoded = unidecode.unidecode(char)
                if len(decoded) == 1 and decoded in self.char_map:
                    chunks.append(decoded)
                else:
                    chunks.append(' ')

        return ''.join(chunks).replace('  ', ' ')

    def encode_string(self, string, maxlen=14):
        string = self.normalize_string(string, maxlen)

        chunks = []
        for char in string:
            chunks.append(self.char_map[char])

        return ''.join(chunks)

    def decode(self, messages):
        bitstring = ""
        message_type = 'song' if messages[0][2] == '2' else 'instrument panel'
        for message in messages:
            bitstring += ba(hex='0x'+message[4:]).bin

        return "{}: {}".format(message_type, self.decode_bitstring(bitstring))

    def decode_radio(self, message):
        bitstring = ba(hex='0x'+message).bin
        return self.decode_bitstring(bitstring)

    def decode_bitstring(self, bitstring):
        decoded = ""
        for bits in wrap(bitstring, 6):
            if len(bits) < 6:
                continue
            if bits == self.field_separator:
                decoded += "; "
            elif bits == self.string_end:
                pass
            else:
                if bits in self.bitstrings_map:
                    decoded += self.bitstrings_map[bits]
                else:
                    decoded += "?"

        return decoded

    def bitstring_to_bytes(self, s):
        return int(s, 2).to_bytes(len(s) // 8, byteorder='big')

    def send_instpanel(self, string, is_menu=False):
        print("Showing '{}' on instrument panel".format(string))
        messages = self.encode_instpanel(string, is_menu)
        self.bus.send(messages[0])
        time.sleep(0.01)
        self.bus.send(messages[1])

    def send_music(self, track, artist, folder=None):
        messages = self.encode_music(track, artist, folder)
        for message in messages:
            self.bus.send(message)
            time.sleep(0.01)

    def clear_instpanel(self):
        print("Clearing instrument panel")
        self.bus.send(
            Message(arbitration_id=CANID_BM_TEXT_MESSAGE, data=bytearray(MESSAGE_INSTPANEL_CLEAR.bytes))
        )
