# XML Parser/Data Access Object BatchImportCurrentState.py
"""AUTO-GENERATED Source file for BatchImportCurrentState.py"""
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
    """History : {'name': u'History', 'level': 3, 'original_name': u'History', 'parents': [u'CurrentState'], 'path': [None, u'CurrentRun', u'CurrentState'], 'children': []}"""
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'CurrentRun', u'CurrentState']
        API.xml.base_xml.XMLNode.__init__(self, "History", attrs, None, [])

class Master_class(API.xml.base_xml.XMLNode):
    """Master : {'name': u'Master', 'level': 3, 'original_name': u'Master', 'parents': [u'CurrentState'], 'path': [None, u'CurrentRun', u'CurrentState'], 'children': []}"""
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'CurrentRun', u'CurrentState']
        API.xml.base_xml.XMLNode.__init__(self, "Master", attrs, None, [])

class Alert_class(API.xml.base_xml.XMLNode):
    """Alert : {'name': u'Alert', 'level': 2, 'original_name': u'Alert', 'parents': [u'CurrentRun'], 'path': [None, u'CurrentRun'], 'children': []}"""
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'CurrentRun']
        API.xml.base_xml.XMLNode.__init__(self, "Alert", attrs, None, [])

class CurrentState_class(API.xml.base_xml.XMLNode):
    """CurrentState : {'name': u'CurrentState', 'level': 2, 'original_name': u'CurrentState', 'parents': [u'CurrentRun'], 'path': [None, u'CurrentRun'], 'children': [u'Master', u'History']}"""
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'CurrentRun']
        self.Master = []
        self.History = []
        API.xml.base_xml.XMLNode.__init__(self, "CurrentState", attrs, None, [])

class CurrentRun_class(API.xml.base_xml.XMLNode):
    """CurrentRun : {'name': u'CurrentRun', 'level': 1, 'original_name': u'CurrentRun', 'parents': [None], 'path': [None], 'children': [u'Alert', u'CurrentState']}"""
    def __init__(self, attrs):
        self.level = 1
        self.path = [None]
        self.Alert = []
        self.CurrentState = []
        API.xml.base_xml.XMLNode.__init__(self, "CurrentRun", attrs, None, [])

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

        elif name == "Master":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(Master_class(p_attrs))
            self.in_value_tag = True

        elif name == "Alert":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(Alert_class(p_attrs))
            self.in_value_tag = True

        elif name == "CurrentRun":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(CurrentRun_class(p_attrs))

        elif name == "CurrentState":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(CurrentState_class(p_attrs))

        elif name == "History":
            p_attrs = process_attrs(attrs)
            self.obj_depth.append(History_class(p_attrs))
            self.in_value_tag = True

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

        elif name == "Master":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            self.obj_depth[-2].Master.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.in_value_tag = False
            self.char_buffer = []

        elif name == "Alert":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            self.obj_depth[-2].Alert.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.in_value_tag = False
            self.char_buffer = []

        elif name == "CurrentRun":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            # root node is not added to a parent; stays on the "stack" for the return_object

        elif name == "CurrentState":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            self.obj_depth[-2].CurrentState.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete

        elif name == "History":
            if len(self.char_buffer) != 0:
                self.obj_depth[-1].value = "".join(self.char_buffer)
            self.obj_depth[-2].History.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.in_value_tag = False
            self.char_buffer = []

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


