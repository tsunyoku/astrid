from enum import IntEnum

class osuTypes(IntEnum):
    i8  = 0
    u8  = 1
    i16 = 2
    u16 = 3
    i32 = 4
    u32 = 5
    f32 = 6
    i64 = 7
    u64 = 8
    f64 = 9

    message = 11
    channel = 12
    match = 13

    i32_list   = 17
    i32_list4l = 18
    string     = 19
    raw        = 20