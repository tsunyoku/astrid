from collections import namedtuple

from constants.types import osuTypes

import struct

Message = namedtuple('Message', ['from_username', 'msg', 'target_username', 'from_id'])
Channel = namedtuple('Channel', ['name', 'desc', 'players'])

types = {
    osuTypes.i8: lambda rd: rd.read_i8(),
    osuTypes.u8: lambda rd: rd.read_u8(),
    osuTypes.i16: lambda rd: rd.read_i16(),
    osuTypes.u16: lambda rd: rd.read_u16(),
    osuTypes.i32: lambda rd: rd.read_i32(),
    osuTypes.u32: lambda rd: rd.read_u32(),
    osuTypes.f32: lambda rd: rd.read_f32(),
    osuTypes.i64: lambda rd: rd.read_i64(),
    osuTypes.u64: lambda rd: rd.read_u64(),
    osuTypes.f64: lambda rd: rd.read_f64(),
    osuTypes.message: lambda rd: rd.read_msg(),
    osuTypes.channel: lambda rd: rd.read_chan(),
    osuTypes.match: lambda rd: rd.read_match(),
    osuTypes.i32_list: lambda rd: rd.read_i32l(),
    osuTypes.i32_list4l: lambda rd: rd.read_i32l_4(),
    osuTypes.string: lambda rd: rd.read_string(),
    osuTypes.raw: lambda rd: rd.read_raw()
}

def handle_packet(data: bytes, structs: tuple) -> list:
    """Function to handle packet bytes from the client, with given types for each packet."""

    reader = Reader(data)
    data = []

    for _struct in structs:
        unpack_func = types.get(_struct, None)

        if not unpack_func: data += b''
        data += unpack_func(reader)

    return data

class Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.offset = 0
        self.packet_id, self.length = self.init_packet()

    def init_packet(self) -> tuple:
        """Get packet id and length from packet data."""

        data = struct.unpack("<HxI", self.data[:7])
        self.offset += 7

        return (data[0], data[1])

    def read(self, offset: int) -> bytes:
        """
        Reads data from packet with a given offset.

        Arguments:
            offset (int) - given offset to read data from
        """

        data = self.data[self.offset:self.offset + offset]
        self.offset += offset
        
        return data

    def read_int(self, size: int, signed: bool) -> int:
        """
        Parses bytes from an osu packet into an integer.

        Arguments:
            size (int) - offset size to pass into read function
            signed (bool) - bool to decide if the int result is signed or unsigned
        """

        return int.from_bytes(
            self.read(size), 
            'little', 
            signed=signed
        )

    def read_float(self, size: int) -> float:
        """
        Parses bytes from an osu packet into a float.

        Arguments:
            size(int) - offset size to pass into read function
        """

        return struct.unpack(
            "<f", 
            self.read(size)
        )

    def read_i8(self) -> int: return self.read_int(1, True)
    def read_u8(self) -> int: return self.read_int(1, False)
    
    def read_i16(self) -> int: return self.read_int(2, True)
    def read_u16(self) -> int: return self.read_int(2, False)

    def read_i32(self) -> int: return self.read_int(4, True)
    def read_u32(self) -> int: return self.read_int(4, False)
    def read_f32(self) -> float: return self.read_float(4)

    def read_i64(self) -> int: return self.read_int(8, True)
    def read_u64(self) -> int: return self.read_int(8, False)
    def read_f64(self) -> float: return self.read_float(8)

    def read_raw(self) -> bytes: return self.read(self.length)

    def read_i32_list(self) -> list:
        length = self.read_i16()

        data = struct.unpack(f"<{'I' * length}", self.data[self.offset:self.offset + length * 4])
        self.offset += length * 4

        return data
    
    def read_i32_4list(self) -> list:
        length = self.read_i32()

        data = struct.unpack(f"<{'I' * length}", self.data[self.offset:self.offset + length * 4])
        self.offset += length * 4

        return data

    def read_string(self) -> str:
        if self.read_u8() != 0x0b: return ''

        length = shift = 0

        while True:
            body = self.read_u8()

            length |= (body & 0b01111111) << shift
            if (body & 0b10000000) == 0: break

            shift += 7

        return self.read(length).decode()

    def read_msg(self) -> Message:
        return Message(
            from_username = self.read_string(),
            msg = self.read_string(),
            target_username = self.read_string(),
            from_id = self.read_i32()
        )

    def read_channel(self) -> Channel:
        return Channel(
            name = self.read_string(),
            desc = self.read_string(),
            players = self.read_i32()
        )


