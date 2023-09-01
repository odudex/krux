# The MIT License (MIT)

# Copyright (c) 2021-2022 Krux contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# pylint: disable=E1101
import io
import math
import qrcode
from .ur.ur_encoder import UREncoder
from .ur.ur_decoder import URDecoder
from .ur.ur import UR

FORMAT_NONE = 0
FORMAT_PMOFN = 1
FORMAT_UR = 2


class QRPartParser:
    """Responsible for parsing either a singular or animated series of QR codes
    and returning the final decoded, combined data
    """

    def __init__(self):
        self.parts = {}
        self.total = -1
        self.format = None
        self.decoder = URDecoder()

    def parsed_count(self):
        """Returns the number of parsed parts so far"""
        if self.format == FORMAT_UR:
            # Single-part URs have no expected part indexes
            if self.decoder.fountain_decoder.expected_part_indexes is None:
                return 1 if self.decoder.result is not None else 0
            completion_pct = self.decoder.estimated_percent_complete()
            return math.ceil(completion_pct * self.total_count())
        return len(self.parts)

    def total_count(self):
        """Returns the total number of parts there should be"""
        if self.format == FORMAT_UR:
            # Single-part URs have no expected part indexes
            if self.decoder.fountain_decoder.expected_part_indexes is None:
                return 1
            return self.decoder.expected_part_count()
        return self.total

    def parse(self, data):
        """Parses the QR data, extracting part information"""
        if self.format is None:
            self.format = detect_format(data)

        if self.format == FORMAT_NONE:
            self.parts[1] = data
            self.total = 1
        elif self.format == FORMAT_PMOFN:
            part, index, total = parse_pmofn_qr_part(data)
            self.parts[index] = part
            self.total = total
        elif self.format == FORMAT_UR:
            self.decoder.receive_part(data)

    def is_complete(self):
        """Returns a boolean indicating whether or not enough parts have been parsed"""
        if self.format == FORMAT_UR:
            return self.decoder.is_complete()
        return (
            self.total != -1
            and self.parsed_count() == self.total_count()
            and sum(self.parts.keys()) == sum(range(1, self.total + 1))
        )

    def result(self):
        """Returns the combined part data"""
        if self.format == FORMAT_UR:
            return UR(self.decoder.result.type, bytearray(self.decoder.result.cbor))
        code_buffer = io.StringIO("")
        for _, part in sorted(self.parts.items()):
            code_buffer.write(part)
        code = code_buffer.getvalue()
        code_buffer.close()
        return code


def to_qr_codes(data, max_width, qr_format):
    """Returns the list of QR codes necessary to represent the data in the qr format, given
    the max_width constraint
    """
    if qr_format == FORMAT_NONE:
        code = qrcode.encode_to_string(data)
        yield (code, 1)
    else:
        num_parts = find_min_num_parts(data, max_width, qr_format)
        while math.ceil(data_len(data) / num_parts) > 128:
            num_parts += 1
        part_size = math.ceil(data_len(data) / num_parts)

        if qr_format == FORMAT_PMOFN:
            for i in range(num_parts):
                part_number = "p%dof%d " % (i + 1, num_parts)
                part = None
                if i == num_parts - 1:
                    part = part_number + data[i * part_size :]
                else:
                    part = part_number + data[i * part_size : i * part_size + part_size]
                code = qrcode.encode_to_string(part)
                yield (code, num_parts)
        elif qr_format == FORMAT_UR:
            encoder = UREncoder(data, part_size, 0)
            while True:
                part = encoder.next_part()
                code = qrcode.encode_to_string(part)
                yield (code, encoder.fountain_encoder.seq_len())


def add_qr_frame(qr_code):
    """Add a 1 block white border around the code before displaying"""
    qr_code = qr_code.strip()
    lines = qr_code.split("\n")
    size = len(lines)
    size += 2
    new_lines = ["0" * size]
    for line in lines:
        new_lines.append("0" + line + "0")
    new_lines.append("0" * size)
    return size, "\n".join(new_lines)


def get_size(qr_code):
    """Returns the size of the qr code as the number of chars until the first newline"""
    size = 0
    while qr_code[size] != "\n":
        size += 1
    return size


def data_len(data):
    """Returns the length of the payload data, accounting for the UR type"""
    if isinstance(data, UR):
        return len(data.cbor)
    return len(data)


def find_min_num_parts(data, max_width, qr_format):
    """Finds the minimum number of QR parts necessary to encode the data in
    the specified format within the max_width constraint
    """
    num_parts = 1
    part_size = math.ceil(data_len(data) / num_parts)
    while True:
        part = ""
        if qr_format == FORMAT_PMOFN:
            part_number = "p1of%d " % num_parts
            part = part_number + data[0:part_size]
        elif qr_format == FORMAT_UR:
            encoder = UREncoder(data, part_size, 0)
            part = encoder.next_part()
        # The worst-case number of bytes needed to store one QR Code, up to and including
        # version 40. This value equals 3918, which is just under 4 kilobytes.
        if len(part) < 3918:
            code = qrcode.encode_to_string(part)
            if get_size(code) <= max_width:
                break
        num_parts += 1
        part_size = math.ceil(data_len(data) / num_parts)
    return num_parts


def parse_pmofn_qr_part(data):
    """Parses the QR as a P M-of-N part, extracting the part's content, index, and total"""
    of_index = data.index("of")
    space_index = data.index(" ")
    part_index = int(data[1:of_index])
    part_total = int(data[of_index + 2 : space_index])
    return data[space_index + 1 :], part_index, part_total


def detect_format(data):
    """Detects the QR format of the given data"""
    qr_format = FORMAT_NONE
    try:
        if data.startswith("p") and data.index("of") <= 5:
            qr_format = FORMAT_PMOFN
        elif data.lower().startswith("ur:"):
            qr_format = FORMAT_UR
    except:
        pass
    return qr_format
