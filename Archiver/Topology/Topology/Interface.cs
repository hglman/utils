using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace Topology
{
    [System.Serializable]
    class TopoGeneric { }

    [System.Serializable]
    class DataBase : TopoGeneric {
        public string DbName;
        public string ServerName;
    }

    [System.Serializable]
    class VmBox : TopoGeneric
    {
        public DataBase db;
        public string VmBoxIp;
    }

    [System.Serializable]
    class BatchImport : TopoGeneric
    {
        public VmBox vmBoxObj;
        public string vmnBoxPath;
        public string q2BatchVersion;
    }

    [System.Serializable]
    class FileArchiverUtil : TopoGeneric
    {
        public VmBox vmBoxObj;
        public string VmBoxPath;
        public string FileArchiveconfigXML;
        public Dictionary<string, string> FileVersionDict;
    }
}
