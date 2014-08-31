using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Xml;

namespace Topology
{
    class Program
    {
        static void Main(string[] args)
        {
            System.Xml.Serialization.XmlSerializer xs;
            switch (args[0])
            {
                case "VmBox":
                    var vmb = Builder.VmBoxBuilder(args.Skip(1));
                    Console.Write(vmb);
                    break;
                case "Batchimport":
                    List<BatchImport> bi = Builder.BatchImportBuilder(args.Skip(1));
                    xs = new System.Xml.Serialization.XmlSerializer(bi.GetType(), new Type[] { typeof(BatchImport) });
                    xs.Serialize(Console.Out, bi);
                    Environment.Exit(0);
                    break;
                default:
                    Console.WriteLine(string.Format("Invalid Param {1}", args[0]));
                    Environment.Exit(1);
                    break;
            }
        }
   } 
}
