# XML Parser/Data Access Object BatchThreshold.py
"""AUTO-GENERATED Source file for BatchThreshold.py"""
import xml.sax
import Queue
import API.xml.base_xml

def process_attrs(attrs):
    """Process sax attribute data into local class namespaces"""
    if attrs.getLength() == 0:
        return {}
    tmp_dict = {}
    for name in attrs.getNames():
        tmp_dict[name] = attrs.getValue(name)
    return tmp_dict

class History_class(API.xml.base_xml.XMLNode):
    """History : {'name': u'History', 'level': 2, 'original_name': u'History', 'parents': [u'BatchThreshold'], 'path': [None, u'BatchThreshold'], 'children': []}"""
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'BatchThreshold']
        API.xml.base_xml.XMLNode.__init__(self, "History", attrs, None, [])

class Master_class(API.xml.base_xml.XMLNode):
    """Master : {'name': u'Master', 'level': 2, 'original_name': u'Master', 'parents': [u'BatchThreshold'], 'path': [None, u'BatchThreshold'], 'children': []}"""
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'BatchThreshold']
        API.xml.base_xml.XMLNode.__init__(self, "Master", attrs, None, [])

class Time_class(API.xml.base_xml.XMLNode):
    """Time : {'name': u'Time', 'level': 2, 'original_name': u'Time', 'parents': [u'BatchThreshold'], 'path': [None, u'BatchThreshold'], 'children': []}"""
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'BatchThreshold']
        API.xml.base_xml.XMLNode.__init__(self, "Time", attrs, None, [])

class BatchThreshold_class(API.xml.base_xml.XMLNode):
    """BatchThreshold : {'name': u'BatchThreshold', 'level': 1, 'original_name': u'BatchThreshold', 'parents': [None], 'path': [None], 'children': [u'History', u'Time', u'Master']}"""
    def __init__(self, attrs):
        self.level = 1
        self.path = [None]
        self.History = []
        self.Time = []
        self.Master = []
        API.xml.base_xml.XMLNode.__init__(self, "BatchThreshold", attrs, None, [])

class NodeHandler(xml.sax.handler.ContentHandler):
    """SAX ContentHandler to map XML input class/object"""
    def __init__(self, return_q):     # overridden in subclass
        self.obj_depth = [None]
        self.return_q = return_q
        self.in_value_tag = False
        self.char_buffer = []
        xml.sax.handler.ContentHandler.__init__(self)   # superclass init

    def startElement(self, name, attrs): # creating the node along the path being tracked
        """Override base class ContentHandler method"""
        if ':' in name:
            name = name.replace(':', '_')
        if '-' in name:
            name = name.replace('-', '_')
        if '.' in name:
            name = name.replace('.', '_')
        if name == "":
            raise ValueError, "XML Node name cannot be empty"

        elif name == "History":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(History_class(p_attrs))
            self.in_value_tag = True

        elif name == "Time":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(Time_class(p_attrs))
            self.in_value_tag = True

        elif name == "Master":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(Master_class(p_attrs))
            self.in_value_tag = True

        elif name == "BatchThreshold":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(BatchThreshold_class(p_attrs))

    def endElement(self, name): # need to append the node that is closing in the right place
        """Override base class ContentHandler method"""
        if ':' in name:
            name = name.replace(':', '_')
        if '-' in name:
            name = name.replace('-', '_')
        if '.' in name:
            name = name.replace('.', '_')
        if name == "":
            raise ValueError, "XML Node name cannot be empty"

        elif name == "History":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            self.obj_depth[-2].History.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.in_value_tag = False
            self.char_buffer = []

        elif name == "Time":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            self.obj_depth[-2].Time.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.in_value_tag = False
            self.char_buffer = []

        elif name == "Master":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            self.obj_depth[-2].Master.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.in_value_tag = False
            self.char_buffer = []

        elif name == "BatchThreshold":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            # root node is not added to a parent; stays on the "stack" for the return_object

    def characters(self, in_chars):
        """Override base class ContentHandler method"""
        if self.in_value_tag == True:
            self.char_buffer.append(in_chars)

    def endDocument(self):
        """Override base class ContentHandler method"""
        self.return_q.put(self.obj_depth[-1])

def obj_wrapper(xml_stream):
    """Call the handler against the XML, then get the returned object and pass it back up"""
    try:
        return_q = Queue.Queue()
        xml.sax.parseString(xml_stream, NodeHandler(return_q))
        return (True, return_q.get())
    except Exception, e:
        return (False, (Exception, e))


