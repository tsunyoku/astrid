using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using MySqlConnector;

namespace astrid
{
    public class MySQLConnection
    {
        private MySqlConnection _conn;

        public MySQLConnection(string conn_str) => _conn = new MySqlConnection(conn_str);
        public async Task Initialise() => await _conn.OpenAsync();

        public MySqlCommand ParseQuery(string query, List<object> args) // god this is cursed
        {
            var cmd = new MySqlCommand();
            cmd.Connection = _conn;

            int arg_count = 0;

            foreach (Match match in Regex.Matches(query, "%s")) // parse query escapes
            {
                int index1 = match.Index + 1;
                int index2 = index1 + 1;

                query = query.Insert(index1, "@");
                query = query.Insert(index2, arg_count.ToString());

                arg_count++;
            }

            cmd.CommandText = query;
            for (int i = 0; i < args.Count; i++) { cmd.Parameters.AddWithValue($"@{i}", args[i]); }

            return cmd;
        }

        public async Task Execute(string query, List<object> args)
        {
            var cmd = ParseQuery(query, args);
            await cmd.ExecuteNonQueryAsync();
        }

        public async Task<object> FetchRow(string query, List<object> args)
        {
            query += " LIMIT 1"; // XDDDDDDDDD
            var cmd = ParseQuery(query, args);

            return await cmd.ExecuteReaderAsync(); // i think?
        }
    }
}
