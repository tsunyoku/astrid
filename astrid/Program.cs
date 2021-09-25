using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WatsonWebserver;
using MySqlConnector;
using astrid.Packets;

using HttpMethod = WatsonWebserver.HttpMethod;

namespace astrid
{
    class Program
    {
        static string serverMOTD = "astrid.\n\nmy shitty attempt at writing a C# bancho!";

        static void Main(string[] args)
        {
            Server app = new Server("127.0.0.1", 9292);
            Config config = ConfigParser.ParseConfig();

            string MySQLString = $"Server={config.SQLInfo["Server"]};User ID={config.SQLInfo["Username"]};" +
                                 $"Password={config.SQLInfo["Password"]};Database={config.SQLInfo["Database"]}";

            //MySQLConnection sql = new Connection(MySQLString);

            app.Routes.Static.Add(HttpMethod.GET, "/", BanchoWebRoute);
            app.Routes.Static.Add(HttpMethod.POST, "/", BanchoConnection);
            app.Start();

            Console.WriteLine("astrid started!");
            Console.ReadLine();
        }

        public static void ParseHeaders(Dictionary<string, string> headers)
        {
            foreach (string key in headers.Keys.ToArray())
            {
                headers[key] = headers[key].ToLower();
            }
        }

        static async Task BanchoWebRoute(HttpContext ctx)
        {
            await ctx.Response.Send(serverMOTD);
        }

        static async Task BanchoConnection(HttpContext ctx)
        {
            var headers = ctx.Request.Headers;
            ParseHeaders(headers); // bruh

            var agent = headers.GetValueOrDefault("user-agent", null);
            if (agent == null || agent != "osu!") { 
                await BanchoWebRoute(ctx);
                return;
            }

            if (!headers.ContainsKey("osu-token")) { 
                await LoginUser(ctx);
                return;
            }
        }

        static async Task LoginUser(HttpContext ctx)
        {
            var data = ctx.Request.DataAsBytes;
            var data_string = ctx.Request.DataAsString; // idk if i'll need this

            var info = (data_string.Split("\n")).ToList();
            info.RemoveAt(info.Count - 1);

            if (info.Count != 3)
            {
                ctx.Response.Headers.Add("cho-token", "no");
                await ctx.Response.Send(await PacketHandlers.UserID(-2));
                return;
            }

            var client_info = info[2].Split("|").ToList();
            if (client_info.Count != 5)
            {
                ctx.Response.Headers.Add("cho-token", "no");
                await ctx.Response.Send(await PacketHandlers.UserID(-2));
                return;
            }

            string username = info[0];
            byte[] password = Encoding.UTF8.GetBytes(info[1]);


        }
    }
}