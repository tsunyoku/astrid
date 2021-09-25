using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;

namespace astrid
{
    public static class ConfigParser
    {
        public static string SolutionPath()
        {
            var directory = new DirectoryInfo(Directory.GetCurrentDirectory());

            while (directory != null && !directory.GetFiles("*.sln").Any())
            {
                directory = directory.Parent;
            }

            if (directory == null) { return null; }
            return directory.FullName;
        }

        public static Config ParseConfig()
        {
            var route_dir = SolutionPath();
            if (route_dir == null) // not using vs path, we can try current dir
            {
                if (!File.Exists("./sample_config.json")) {
                    Console.WriteLine("Error finding route path...");
                    Environment.Exit(1);
                }

                route_dir = Directory.GetCurrentDirectory();
            }

            if (!File.Exists($"{route_dir}/config.json"))
            {
                Console.WriteLine("No config file... Creating default!");
                File.Copy($"{route_dir}/sample_config.json", $"{route_dir}/config.json");
                Environment.Exit(1);
            }

            var config_string = File.ReadAllText($"{route_dir}/config.json");
            var config = JsonConvert.DeserializeObject<Config>(config_string);

            return config;
        }
    }

    public struct Config
    {
        public Dictionary<string, string> SQLInfo { get; set; }

        public override string ToString() => JsonConvert.SerializeObject(this);
    }
}
