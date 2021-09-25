using System.IO;
using System.Threading.Tasks;
using osu.Game.IO.Legacy;

namespace astrid.Packets
{
    public class PacketHandlers
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
