using osu.Game.IO.Legacy;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace astrid.Packets
{
    public static class Writer
    {
        public static async Task<byte[]> UserID(int id)
        {
            var packet = new Packet
            {
                Type = PacketType.CHO_USER_ID
            };

            await using (var writer = new SerializationWriter(new MemoryStream()))
            {
                writer.Write(id);
                packet.Data = ((MemoryStream)writer.BaseStream).ToArray();
            }

            return packet.Data;
        }
    }
}
