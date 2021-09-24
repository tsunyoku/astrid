using osu.Game.IO.Legacy;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace astrid.Packets
{
    public static class Reader
    {
        public static Packet Read(MemoryStream _data)
        {
            var reader = new SerializationReader(_data);
            var packetID = (PacketType)reader.ReadInt16();

            reader.ReadByte(); // ignored byte

            var len = reader.ReadInt32();
            var data = reader.ReadBytes(len);

            return new Packet { Type = packetID, Data = data };
        }
    }
}
