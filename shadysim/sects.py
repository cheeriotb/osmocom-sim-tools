#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  Copyright (C) 2018 cheeriotb <cheerio.the.bear@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 2 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#/

from pySim.transport.pcsc import PcscSimLink

import argparse
import sys

class CommandInterface(object):
    def __init__(self, transport):
        self.transport = transport

    def extract_value(self, response):
        tag_first = int(response[0:2], 16)
        response = response[2:]

        # If all the bits 1-5 in the first byte are 1, the tag is encoded in the long format.
        # The tag number is encoded in the following octets,
        # where bit 8 of each is 1 if there are more octets, and bits 1–7 encode the tag number.
        if (tag_first & 0x1F) == 0x1F:
            while True:
                tag_subsequent = int(response[0:2], 16)
                response = response[2:]
                if (tag_subsequent & 0x80) != 0x80:
                    break

        length = 0
        length_byte = int(response[0:2], 16)
        response = response[2:]

        # The long form consist of 1 initial octet followed by 1 or more subsequent octets,
        # containing the length. In the initial octet, bit 8 is 1,
        # and bits 1–7 (excluding the values 0 and 127) encode the number of octets that follow.
        if length_byte > 127:
            length_size = length_byte - 128
            while length_size:
                length_byte = int(response[0:2], 16)
                response = response[2:]
                length = (length << 8) + length_byte
                length_size -= 1
        else:
            length = length_byte

        return (response[:length * 2], response[length * 2:])

    def send_apdu_raw(self, apdu):
        if len(apdu) < (4 * 2):
            raise ValueError("Specified C-APDU is too short : " + apdu)
        (response, sw) = self.transport.send_apdu(apdu)
        sw1 = int(sw[0:2], 16)
        if sw1 == 0x6C:
            (response, sw) = self.transport.send_apdu(apdu[:-2] + sw[2:4])
            sw1 = int(sw[0:2], 16)
        output = response
        while sw1 == 0x61 or sw1 == 0x9F:
            apdu = apdu[0:2] + 'C00000' + sw[2:4]
            (response, sw) = self.transport.send_apdu(apdu)
            output = output + response
            sw1 = int(sw[0:2], 16)
        return (output, sw)

    def send_terminal_profile(self):
        (response, sw) = self.transport.send_apdu('A010000011FFFF000000000000000000000000000000')
        if sw[0:2] == '91':
            self.transport.send_apdu('A0120000' + sw[2:4])
            return self.transport.send_apdu('A01400000C810301030002028281030100')
        return (response, sw)

    def open_logical_channel(self):
        (response, sw) = self.transport.send_apdu('0070000001')
        if sw[0:2] != '90':
            raise RuntimeError('Unexpected SW for MANAGE CHANNEL : ' + sw)
        if len(response) != 2:
            raise RuntimeError('The size of the response data is wrong : ' + response)
        return int(response[0:2], 16)

    def close_logical_channel(self, channel_number):
        (response, sw) = self.transport.send_apdu('007080' + format(channel_number, '02X'))
        if sw[0:2] != '90':
            raise RuntimeError('Unexpected SW for MANAGE CHANNEL : ' + sw)

    def select_application(self, channel_number, aid):
        (response, sw) = self.send_apdu_raw(format(channel_number, '02X') + 'A40400' \
                + format(len(aid) // 2, '02X') + aid + '00')
        if sw[0:2] != '90':
            raise RuntimeError('Unexpected SW for SELECT : ' + sw)
        return response

    def select_application_with_check_response(self, channel_number, aid):
        response = self.select_application(channel_number, aid)

        # The length of the select response shall be greater than 2 bytes
        if len(response) < 3:
            raise RuntimeError('The size of the response data is wrong : ' + response)

        (target, remain) = self.extract_value(response)
        while len(target) > 0:
            (value, target) = self.extract_value(target)

    def send_apdu_on_channel(self, channel_number, apdu):
        cla = int(apdu[0:2], 16)
        if channel_number < 4:
            cla = (cla & 0xBC) | channel_number
        elif channel_number < 20:
            secure = False if (cla & 0x0C) != 0 else True
            cla = (cla & 0xB0) | 0x40 | (channel_number - 4)
            if secure:
                cla = cla | 0x20
        else:
            raise ValueError("Specified channel number is out of range : " + channel_number)
        apdu = format(cla, '02X') + apdu[2:]

        return self.send_apdu_raw(apdu)

    def send_apdu(self, aid, apdu):
        channel_number = self.open_logical_channel()
        self.select_application(channel_number, aid)
        (response, sw) = self.send_apdu_on_channel(channel_number, apdu)
        self.close_logical_channel(channel_number)
        return (response, sw)

class OmapiTest(object):
    def __init__(self, commandif):
        self.commandif = commandif

    def testTransmitApdu(self):
        print('started: ' + sys._getframe().f_code.co_name)
        selectable_aid = 'A000000476416E64726F696443545331'

        # a. 0xA000000476416E64726F696443545331
        #   ii.The applet should return no data when it receives the following APDUs in Transmit:
        #         i.0x00060000
        #        ii.0x80060000
        #       iii.0xA0060000
        #        iv.0x94060000
        #         v.0x000A000001AA
        #        vi.0x800A000001AA
        #       vii.0xA00A000001AA
        #      viii.0x940A000001AA

        no_data_apdu_list = [
            '00060000',
            '80060000',
            'A0060000',
            '94060000',
            '000A000001AA',
            '800A000001AA',
            'A00A000001AA',
            '940A000001AA'
        ]

        for apdu in no_data_apdu_list:
            (response, sw) = self.commandif.send_apdu(selectable_aid, apdu)
            if len(response) > 0:
                raise RuntimeError('Unexpected output data is received : ' + response)
            if sw != '9000':
                raise RuntimeError('SW is not 9000 : ' + sw)

        # a. 0xA000000476416E64726F696443545331
        #   iii. The applet should return 256-byte data for the following Transmit APDUs:
        #         i.0x0008000000
        #        ii.0x8008000000
        #       iii.0xA008000000
        #        iv.0x9408000000
        #         v.0x000C000001AA00
        #        vi.0x800C000001AA00
        #       vii.0xA00C000001AA00
        #      viii.0x940C000001AA00

        data_apdu_list = [
            '0008000000',
            '8008000000',
            'A008000000',
            '9408000000',
            '000C000001AA00',
            '800C000001AA00',
            'A00C000001AA00',
            '940C000001AA00'
        ]

        for apdu in data_apdu_list:
            (response, sw) = self.commandif.send_apdu(selectable_aid, apdu)
            if len(response) != (256 * 2):
                raise RuntimeError('The length of output data is unexpected : ' + response)
            if sw != '9000':
                raise RuntimeError('SW is not 9000 : ' + sw)

        print('finished: ' + sys._getframe().f_code.co_name)

    def testLongSelectResponse(self):
        print('started: ' + sys._getframe().f_code.co_name)
        aid = 'A000000476416E64726F696443545332'

        channel_number = self.commandif.open_logical_channel()
        response = self.commandif.select_application_with_check_response(channel_number, aid)
        self.commandif.close_logical_channel(channel_number)

        print('finished: ' + sys._getframe().f_code.co_name)

    def execute_all(self):
        self.testTransmitApdu()
        self.testLongSelectResponse()

parser = argparse.ArgumentParser(description='Android Secure Element CTS')
parser.add_argument('-p', '--pcsc', nargs='?', const=0, type=int)
args = parser.parse_args()

transport = None
if args.pcsc is not None:
    transport = PcscSimLink(args.pcsc)
else:
    transport = PcscSimLink()

commandif = CommandInterface(transport)
transport.wait_for_card()
commandif.send_terminal_profile()

omapi = OmapiTest(commandif)
omapi.execute_all()

