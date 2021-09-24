 using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace astrid.Packets
{
    public struct Packet
    {
        public PacketType Type { get; set; }
        public byte[] Data { get; set; }
    }
}
