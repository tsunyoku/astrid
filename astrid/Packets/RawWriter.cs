using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using osu.Game.IO.Legacy;

namespace astrid.Packets
{
    /// <summary>
    /// Writer class used to write multiple packets simultaneously.
    /// </summary>
    public class RawWriter
    {
        private readonly MemoryStream _buffer;

        public RawWriter() => _buffer = new MemoryStream();

        public async Task Write(Packet packet)
        {
            await using (var writer = new SerializationWriter(new MemoryStream()))
            {
                writer.Write((short)packet.Type);
                writer.Write((byte)0);
                writer.Write(packet.Data);

                var _base = (MemoryStream)writer.BaseStream;

                _base.WriteTo(_buffer);
            }
        }
    }
}
