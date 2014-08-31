using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Xml;
using System.Xml.Serialization;

namespace Topology
{
    [System.Serializable]
    public class TopoGeneric { }

    public class DataBase : TopoGeneric
    {
        [XmlAttribute]
        public string DbName;
        [XmlAttribute]
        public string ServerName;
    }

    public class Drive : TopoGeneric
    {
        [XmlAttribute]
        public string DriveLetter;
        [XmlAttribute]
        public string TotalSpace;
        [XmlAttribute]
        public string FreeSpace;
    }

    public class VmBox : TopoGeneric
    {
        [XmlAttribute]
        public string Ip;
        [XmlAttribute]
        public string Name;
        public List<Drive> DriveList;
    }

    public class BatchImport : TopoGeneric
    {
        public DataBase db;
        [XmlAttribute]
        public VmBox vmBoxObj;
        [XmlAttribute]
        public string vmnBoxPath;
        [XmlAttribute]
        public string q2BatchVersion;
    }

    public class FileArchiverUtil : TopoGeneric
    {
        [XmlAttribute]
        public VmBox vmBoxObj;
        [XmlAttribute]
        public string VmBoxPath;
        [XmlAttribute]
        public string FileArchiveconfigXML;
        public List<KeyValuePair<string, string>> FileVersionDict;
    }
}
