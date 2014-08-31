# coding=utf-8
__version__ = 38
import os
import sys
import hashlib
import datetime
import fileinput
import shutil
import re
import csv
from optparse import OptionParser

class ABase(object):
    """
    The ABase class needs to be inherited by all classes (aka at.py utilities).
    The core flag pattern and file look up mechanics are set here and should be used.

    The base OptionParser flags of -d (directory) -l (search parameters list)
    and -e/-i (include list or exclude list) are set out here. Along with the 
    logic for gathering up a file list to be used by the specific inheriting utility.

    The path (absolute or relative) passed to the -d flag is has a list of the 
    file objects with in it retrieved. This is not recursive over subdirectories.
    This list is then used to filter based on the -e,-i, and -l flags.

    Only one of -e or -i is to be passed. When -e is passed, the strings in
    self.arg_list are checked against the file names found in self.dir
    and if an items of arg_list is a substring of the file name, that file
    will be removed from the items placed into self.file_list.
    For the -i flag the items in self.arg_list are checked against the 
    file listing and only exact string matches are removed from self.file_list.
    """

    def __init__(self):
        """
        Any unset var should be give the value of None
        """
        self.exin = None
        self.dir  = None
        self.arg_list  = []
        # error 0 on success, 1 on error
        self.error = 1
        self.file_list = []
        self.parser = OptionParser()
        self.char_map = {'nul': '\0', 'space': ' ',
                    'tab': '\t', 'doublequote': '"',
                    'singlequote': "'"}

    def print_to_log(self, output):
        """
        method should be used for all log writes. At current it only prints via print.
        But passing logging through the method keeps the package flexable for the future.
        """
        print(output)

    def add_parser_options(self):
        """
        sets out the flags that OptionParser will use, the base flags of -i -e -d and -l 
        are core to the use pattern of at.py and rarely will need to be complete overwritten.

        """
        #pass -i for using an include list
        self.parser.add_option("-i","--include", action="store_false", dest="exin")
        #pass -e for using an exclude list, this is also the default
        self.parser.add_option("-e","--exclude", action="store_true", dest="exin", default=True)
        #set the directory to check
        self.parser.add_option("-d", "--dir", dest="dir", default="tempimport")
        #pass a list of files to include, or extentions to exclude
        #example -l file1,file2,file3 do not put spaces between the items in the list
        #quote any file with a space in the name
        self.parser.add_option("-l", "--list", dest="list")

    def run_parser(self, values):
        """
        This should almost always be overwritten for the utility at hand. Having a clear write out of 
        the flags passed is paramount to troubleshooting. This is also the place to handle the limitations
        of what you can pass via windows console, special chars etc.
        """
        options, args = self.parser.parse_args(args=values )
        self.exin = options.exin
        self.dir = options.dir
        if options.list:
            self.arg_list = options.list.split(',')

        self.print_to_log(
            "Current command line args:  Exclude (True) / Include (False): %s Directory: %s Ex/Include List: %s" % (
            str(self.exin), str(self.dir), str(self.arg_list)))

    def get_timestamp(self, day_diff=0):
        """
        Creates a string of the time at current

        """
        diff = datetime.timedelta(days=day_diff)
        now = datetime.datetime.now() - diff
        return now.strftime('%Y')+'-'+now.strftime('%m')+'-'+now.strftime('%d')+'T'+now.strftime('%H')+':'+now.strftime('%M')+':'+now.strftime('%S')

    def get_path_parts(self, path):
        parts = []
        def consume_path_to_parts(path, parts):
            base, end = os.path.split(path)
            if end:
                parts.append(end)
                return consume_path_to_parts(base, parts)
            else:
                parts.append(base)
                parts.reverse()
                return parts
        return consume_path_to_parts(path, [])

    def make_path(self, path):
        def make_path(path_parts, curr_path):
            if not path_parts:
                return
            part = path_parts.pop(0)
            curr_path = os.path.join(curr_path, part)
            if not os.path.exists(curr_path):
                os.mkdir(curr_path)
            return make_path(path_parts, curr_path)
        path_parts = self.get_path_parts(path)
        return make_path(path_parts, path_parts[0])

    def get_flies(self):
        """
        Build up the list of files
        """
        # find files in the directory
        # http://diveintopython.org/file_handling/os_module.html
        files_in_path = [f for f in os.listdir(self.dir)
                         if os.path.isfile(os.path.join(self.dir, f))]

        ex_or_in = None
        val = 0
        if self.exin:
            #we are excluding files
            val = 1
            ex_or_in = lambda item, file_name, check: 0 if item in file_name else 1 & check
            if not files_in_path:
                self.print_to_log("xxxXXXX No files found, given the parameters passed this is in error, exiting XXXXxxx")
                sys.exit(1)
        else:
            #include files
            val = 0
            ex_or_in = lambda item, file_name, check: 1 if item == file_name else 0 | check
        # for each file in the directory
        for file_name in files_in_path:
            check = val
            # are any of the exclude items in the file name?
            for item in self.arg_list:
                check = ex_or_in(item, file_name, check)
                # if none of the exclude items are in the file name add it to the list of files to hash
            if check:
                self.print_to_log('The file will be checked: ' + file_name)
                self.file_list.append(self.dir + '\\' + file_name)
            else:
                self.print_to_log('Not Being checked: ' + file_name)

class FileParser(ABase):

    def __init__(self):
        super(FileParser, self).__init__()
        self.delimiter = None
        self.number = None
        self.width = None

    def add_parser_options(self):
        #set the directory to check
        self.parser.add_option("-d", "--dir", dest="dir", default="tempimport")
        #pass a listing of files and the parameter need for the fileparse
        #the list needs to be in the form (filename,width),(filename,delimiter,number)
        #any mixing of delimited and fixed with is fine
        self.parser.add_option("-l", "--list", dest="list")

    def run_parser(self, values):
        """
        pull out the different file options
        """
        options, args = self.parser.parse_args(args=values )
        self.exin = False
        self.dir = options.dir
        if options.list:
            #i suppose this could end up being a security issue
            self.arg_list = eval(options.list)

        self.print_to_log(
            "Current command line args: Directory: %s Ex/Include List: %s \n Current file parser parameters: %s" % (
                str(self.dir), str(self.arg_list), str(self.arg_list)))

    def parse_route(self):
        """
        select the type of parse wanted
        """
        self.error = 0
        for item in self.arg_list:
            if len(item) == 2:
                self.make_log_write(self.fixed_width_parse(item), item)
            elif len(item) == 3:
                self.make_log_write(self.delimited_parse(item), item)
            else:
                raise Exception('Invalid Parameters: %s please correct' % item)

    def make_log_write(self, result, item):
        print(result)
        self.print_to_log("File %s has been checked, Parsing results: " % (os.path.join(self.dir, item[0])))
        text = ""
        if len(item) == 2:
            text = "Line length %s on the lines %s"
        else:
            text = "Delimiter count %s on the lines %s"
        #write out the line number for each result group
        for key, value in result.iteritems():
            if key != item[1]:
                self.print_to_log("**ERROR** %s " % (text % (key, value)))
            else:
                self.print_to_log(text % (key, value))

    def fixed_width_parse(self, item):
        """

        """
        result = {}
        try:
            f = open(os.path.join(self.dir, item[0]), 'U')
            line_num = 0
            for line in f:
                line_num += 1
                #store list of line numbers for each line length found
                if len(line) in result:
                    result[len(line)].append(line_num)
                else:
                    result[len(line)] = [line_num]
                #check if failure
                if len(line) != item[1]:
                    self.error = 1
            f.close()
        except IOError:
            self.print_to_log('File not found: %s' % (str(os.path.join(self.dir, item[0]))))
        except:
            self.print_to_log('Unknown Error, Exiting')
            raise
        return result

    def delimited_parse(self, item):
        """

        """
        result = {}
        try:
            f = open(os.path.join(self.dir, item[0]), 'U')
            line_num = 0
            for line in f:
                line_num += 1
                #store list of line numbers for each line length found
                count = line.count(item[2])
                if count in result:
                    result[count].append(line_num)
                else:
                    result[count] = [line_num]
                    #check if failure
                if count != item[1]:
                    self.error = 1
            f.close()
        except IOError:
            self.print_to_log('File not found: %s' % (str(os.path.join(self.dir, item[0]))))
        except:
            self.print_to_log('Unknown Error, Exiting')
            raise
        return result

    def run(self, values):
        self.add_parser_options()
        self.run_parser(values)
        self.parse_route()

class CharStripper(ABase):

    def __init__(self):
        super(CharStripper, self).__init__()
        self.char_to_strip = None
        self.char_for_replace = None

    def add_parser_options(self):
        super(CharStripper, self).add_parser_options()
        #char to strip from file
        self.parser.add_option("-s", "--toStrip", dest='strip')
        #char to replace the stripped char with
        self.parser.add_option("-r", "--toReplace", dest='replace', default='')

    def run_parser(self, values):
        """
        overwrite when using different options
        """
        options, args = self.parser.parse_args(args=values )
        self.exin = options.exin
        self.dir = options.dir
        self.char_to_strip = options.strip
        self.char_for_replace = options.replace
        if self.char_to_strip in self.char_map:
            self.char_to_strip = self.char_map[self.char_to_strip]
        if self.char_for_replace in self.char_map:
            self.char_for_replace = self.char_map[self.char_for_replace]
        if options.list:
            self.arg_list = options.list.split(',')

        self.print_to_log(
            "Current command line args:  Exclude (True) / Include (False): %s Directory: %s Ex/Include List: %s Char to Strip: '%s' Char for use in Replacement: '%s'" % (
            str(self.exin), str(self.dir), str(self.arg_list), str(self.char_to_strip), str(self.char_for_replace)))


    def char_strip(self):
        """
        reads each char, tests for char_to_strip and returns
        This will inplace replace the unwanted chars in a file
        with the new char given by char_for_replace

        will not handle exceptions
        
        Need to update to be able to handle non ascii char
        """

        if not self.file_list:
            self.print_to_log("No files fit parameters, exiting")
            return None


        result = []

        #pass list of files, set to inplace, and byte mode
        fi = fileinput.FileInput(self.file_list,
                                 inplace=1,
                                 mode='U')
        fname = ""
        count = 0
        self.error = 0
        for line in fi:

            #create info for logging
            if fi.isfirstline():
                #skip for first file
                if fi.lineno() > 1:
                    result.append("Processed %s replaced '%s' by '%s' a total of %s" % (
                        fname, self.char_to_strip, self.char_for_replace, str(count)))
                    count = 0
                    fname = fi.filename()
            ltemp = ''
            #test and replace
            for char in line:
                if char == self.char_to_strip:
                    count += 1
                    #if you need to handle occurrences in the batch file
                    self.error = 1
                    char = self.char_for_replace
                ltemp += char
            sys.stdout.write(ltemp)
            fname  = fi.filename()
        #logging for last file
        result.append("Processed %s replaced '%s' by '%s' a total of %s" % (
                fname, self.char_to_strip, self.char_for_replace, str(count)))
        fi.close()
        #write out to log
        for item in result:
            self.print_to_log(item)

    def run(self,values):
        self.add_parser_options()
        self.run_parser(values)
        self.get_flies()
        self.char_strip()

class CSVCharStripper(ABase):

    def __init__(self):
        super(CSVCharStripper, self).__init__()
        self.char_to_strip = None
        self.char_for_replace = None


    def add_parser_options(self):
        super(CSVCharStripper, self).add_parser_options()
        #char to strip from file
        self.parser.add_option("-s", "--toStrip", dest='strip')
        #char to replace the stripped char with
        self.parser.add_option("-r", "--toReplace", dest='replace', default='')


    def run_parser(self, values):
        """
        overwrite when using different options
        """
        options, args = self.parser.parse_args(args=values )
        self.exin = options.exin
        self.dir = options.dir
        self.char_to_strip = options.strip
        self.char_for_replace = options.replace

        if self.char_to_strip in self.char_map:
            self.char_to_strip = self.char_map[self.char_to_strip]
        if self.char_for_replace in self.char_map:
            self.char_for_replace = self.char_map[self.char_for_replace]
        if options.list:
            self.arg_list = options.list.split(',')

        self.print_to_log(
            "Current command line args:  Exclude (True) / Include (False): %s Directory: %s Ex/Include List: %s Char to Strip: '%s' Char for use in Replacement: '%s'" % (
                str(self.exin), str(self.dir), str(self.arg_list), str(self.char_to_strip), str(self.char_for_replace)))


    def stripchar(self):
        """
        self.file_list holds a list of all the file names to look at
        self.char_to_strip holds the character to remove from the csv file
        self.char_for_replace holds the char to add in place of the stripped char

        Work through the file_list and change each char_to_strip to char_for_replace
        after parsing the file as a csv via the csv module

        ie

        if char_to_strip = ','
        and char_for_replace = '_'

        A sample file line:
        12,12.34,20120815,"awesome, time",123
        becomes:
        12,12.34,20120815,"awesome _ time",123
        """
        self.error = 0
        regexobj =  re.compile(self.char_to_strip)

        def process_file(in_file, out_file):
            reader = csv.reader(in_file)
            writer = csv.writer(out_file, reader.dialect)
            char_strip_count = 0
            curr_line_number = 0
            line_changed = []

            for line in reader:
                curr_line_number += 1
                temp = []
                #alt_line = [[new row], replacement count]]
                line_alt_count = 0
                for item in line:
                    new_item, count_temp = regexobj.subn(self.char_for_replace, item)
                    temp.append(new_item)
                    line_alt_count += count_temp
                if line_alt_count:
                    self.error = 1
                    line_changed.append(curr_line_number)
                    char_strip_count += line_alt_count
                    #keep only one line in memory
                writer.writerow(temp)
            self.print_to_log(
                """Processed file: \"%s\", replaced %s characters on %s lines \r\nAltered Lines: %s"""
                % (str(out_file.name), str(char_strip_count), str(len(line_changed)), str(line_changed)))

        for f in self.file_list:
            try:
                shutil.copyfile(f, f + '.backup')
                in_file = open(f + '.backup', 'rU')
                out_file = open(f, 'wb')
                process_file(in_file, out_file)
                in_file.close()
                out_file.close()
                os.remove(f + '.backup')
            except OSError:
                self.print_to_log('Can not make backup of file: %s' % f)
                self.error = 1
            except IOError:
                self.print_to_log('Can not open backup file or write to new file: %s' % f)
                self.error = 1
            except:
                self.print_to_log('Total Failure on file %s' % f)
                self.error = 1

    def run(self, values):
        self.add_parser_options()
        self.run_parser(values)
        self.get_flies()
        self.stripchar()

class FileToASCII(ABase):
    """
    default is now set to add a space, to keep from destroying fixed length files
    """

    def __init__(self):
        super(FileToASCII, self).__init__()
        self.char_for_replace = None 

    def add_parser_options(self):
        super(FileToASCII, self).add_parser_options()
        #char to replace the stripped char with
        self.parser.add_option("-r", "--toReplace", dest='replace', default='')

    def run_parser(self, values):
        """
        overwrite when using different options
        """
        options, args = self.parser.parse_args(args=values )
        self.exin = options.exin
        self.dir = options.dir
        if (not options.replace) or self.char_for_replace == 'space':
            self.char_for_replace = ' '
        else:
            self.char_for_replace = options.replace
        if options.list:
            self.arg_list = options.list.split(',')

        self.print_to_log(
            "Current command line args:  Exclude (True) / Include (False): %s Directory: %s Ex/Include List: %s Char for use in Replacement: '%s'" % (
                str(self.exin), str(self.dir), str(self.arg_list), str(self.char_for_replace)))

    def to_ascii(self):
        """

        """

        if not self.file_list:
            self.print_to_log("No files fit parameters, exiting")
            return None
        
        result = {}
        #pass list of files, set to inplace, and byte mode
        fi = fileinput.FileInput(self.file_list,
                                 inplace=1,
                                 mode='U')
        fname = ""
        self.error = 0
        good_char = frozenset('''
        \t\n\r!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_
         `abcdefghijklmnopqrstuvwxyz{|}~\x7f\x80''')
        for line in fi:
            #create info for logging
            if fi.isfirstline():
                result[fi.filename()] = {}
            ltemp = ''
            #test and replace
            for char in line:
                if char not in good_char:
                    self.error = 1
                    if char in result[fi.filename()]:
                        result[fi.filename()][ord(char)] += 1
                    else:
                        result[fi.filename()][ord(char)] = 1
                    char = self.char_for_replace
                ltemp += char
            sys.stdout.write(ltemp)
        fi.close()
        #write out to log
        for filename, log in result.iteritems():
            line = 'Processed file: %s' % filename
            if not log:
                line += ' no chars replaced'
                self.print_to_log(line)
            else:
                line += ' Chars replaced as listed below'
                self.print_to_log(line)
                for char, count in log.iteritems():
                    self.print_to_log('Replaced %s with %s a total of %s'%
                        (char, self.char_for_replace, str(count)))

    def run(self,values):
        self.add_parser_options()
        self.run_parser(values)
        self.get_flies()
        self.to_ascii()

class HashCheck(ABase):
    """

    """
    #375 for cya
    number_of_log_days = 375
    log_path = r'hashcheck'
    log_header = 'status|date first entered|sha1 hash|hash occurences count|date last encountered|file(s) hash occured\n'

    def __init__(self):
        """
        cmd_line_run = True, then will print
        execution steps, if False will suppress them
        """
        super(HashCheck, self).__init__()
        self.hash_log_curr  = {}
        self.hash_curr_files  = {}
        self.log_cut_off_date = self.get_timestamp(self.number_of_log_days)
        #holds hash codes for which duplicates are excitable
        self.valid = None

    def add_parser_options(self):
        super(HashCheck, self).add_parser_options()
        #pass a list of hash codes which can be encountered multiple times
        #with out causing error, such as file passed when there are no transaction
        self.parser.add_option("-v", "--valid", dest="valid")

    def run_parser(self, values):
        """

        """
        options, args = self.parser.parse_args(args=values )
        self.exin = options.exin
        self.dir = options.dir
        if options.list:
            self.arg_list = options.list.split(',')
        if options.valid:
            self.valid = options.valid.split(',')

        self.print_to_log(
            "Current command line args:  Exclude (True) / Include (False): %s Directory: %s Ex/Include List: %s Valid duplicate hash values%s" % (
            str(self.exin), str(self.dir), str(self.arg_list), str(self.valid)))

    def get_hash_log_curr(self):
        """
        test and open the log file
        """
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        try:
            log = open(self.log_path + r'\hash_log.txt', 'U')
            #first line is header, skip
            log.readline()
            for line in log:
                try:
                    line = line.replace('\n','')
                    # log maintenance. only keep number of days designated
                    line = line.split('|')
                    if len(line) != 6:
                        raise Exception
                    if line[4] > self.log_cut_off_date:
                        self.hash_log_curr[line[2]] = line
                except:
                    self.print_to_log('Bad log Line: ' + str(line))
            self.print_to_log('Hash Log read Successfully')
        except IOError:
            self.print_to_log('No log found')
            self.hash_log_curr = None
        except IndexError:
            self.print_to_log('Bad Log File')
            raise
        except:
            self.print_to_log('Unknown Error, Exiting ')
            raise

    def get_hash(self, f):
        hash_obj = hashlib.new('sha1')
        for line in f:
            hash_obj.update(line)
        return hash_obj.hexdigest()

    def get_hash_curr_files(self):
        """
        make a dict of log lines for all the curr files to hash
        """
        temp = None
        for f in self.file_list:
            if not os.stat(f).st_size:
                self.print_to_log('Skipping Zero Length File: ' + f)
            else:
                try:

                    batch_file = open(f,'U')
                    time_stamp = self.get_timestamp()
                    temp = ['pass',
                            time_stamp,
                            self.get_hash(batch_file),
                            '1',
                            time_stamp,
                            batch_file.name[batch_file.name.rfind('\\') + 1 :]]

                    batch_file.close()
                    self.hash_curr_files[temp[2]] = temp
                    self.print_to_log("successfully hashed file: " + temp[5])
                except IOError:
                    self.print_to_log('Cannot Open File: ' + f)
                except:
                    self.print_to_log('Unknown Error, Exiting')
                    raise

    def hash_check_files(self):
        """
         errorlevel_output will be returned and interpreted as %ERRORLEVEL% by batch, 0=good
        """
        temp_error = 0
        if not self.hash_log_curr:
            self.hash_log_curr = self.hash_curr_files
        else:
            for key, value in self.hash_curr_files.iteritems():
                if key in self.hash_log_curr:
                    #test for valid hash
                    if self.valid is not None:
                    #test any valid hahses are given
                        if key in self.valid:
                            # a hash code that is ok to duplicate
                            self.print_to_log('Valid Duplicate HashCode, skipping: ' + value[5])
                            self.hash_log_curr[key][3] = str(int(self.hash_log_curr[key][3]) + 1)
                            self.hash_log_curr[key][4] = value[4]
                            continue
                    # not valid duplicate hash
                    # a dupulicate hash found which is a failure and should abort import
                    self.hash_log_curr[key][0] = 'Fail'
                    self.hash_log_curr[key][3] = str(int(self.hash_log_curr[key][3]) + 1)
                    self.hash_log_curr[key][4] = value[4]
                    self.hash_log_curr[key][5] += ', ' + value[5]
                    self.print_to_log('Duplicate hash found for file: ' + value[5])
                    temp_error = 1
                else:
                    #a new hash, no issues
                    self.hash_log_curr[key] = value
                    self.print_to_log('New Hash for file: ' + value[5])
        self.error = temp_error

    def write_log(self):
        """
        writes out log file, if no data present it writes nothing
        """
        if self.hash_log_curr:
            temp_dict = {}
            count = 0
            for key, value in self.hash_log_curr.iteritems():
                temp_dict[value[4] + str(count)] = key
                count += 1
            temp_sort = temp_dict.keys()
            temp_sort.sort()
            temp_sort.reverse()

            try:
                log = open(self.log_path + r'\hash_log.txt', 'w')
                # log header
                log.write(self.log_header)
                # write hash_log_content to log
                for key in temp_sort:
                    value = self.hash_log_curr[temp_dict[key]]
                    log.write(value[0]+'|'+value[1]+'|'+value[2]+'|'+value[3]+'|'+value[4]+'|'+value[5] + '\n')
                log.close()
                self.print_to_log('New log writen to file: ' + self.log_path + r'\hash_log.txt' )
            except IOError:
                self.print_to_log('Cannot open log file to write')
                raise
            except:
                self.print_to_log('Unknown Error')
                raise

    def run(self,values):
        self.add_parser_options()
        self.run_parser(values)
        self.get_hash_log_curr()
        self.get_flies()
        self.get_hash_curr_files()
        self.hash_check_files()
        self.write_log()

class FileLengthTest(ABase):

    def __init__(self):
        super(FileLengthTest, self).__init__()
        self.type = None

    def add_parser_options(self):
        super(FileLengthTest, self).add_parser_options()
        self.parser.add_option("-z", "--zeroLength", action="store_true", dest="type")
        self.parser.add_option("-x", "--fileExists", action="store_false", dest="type")

    def run_parser(self, values):
        """
        overwrite when using different options
        """
        options, args = self.parser.parse_args(args=values )
        self.exin = options.exin
        self.dir = options.dir
        self.type = options.type
        if options.list:
            self.arg_list = options.list.split(',')

        self.print_to_log(
            "Current command line args:  Exclude (True) / Include (False): %s Directory: %s Ex/Include List: %s Type: %s" % (
                str(self.exin), str(self.dir), str(self.arg_list), str(self.type)))

    def type_route(self):
        if self.type:
            self.get_flies()
            self.file_length_test()
        else:
            self.file_exists_test()

    def file_length_test(self):
        self.error = 0
        if not self.exin:
            self.file_exists_test()
        for f in self.file_list:
            if not os.stat(f).st_size:
                self.print_to_log('Zero length file found: ' + f)
                self.error = 1

    def file_exists_test(self):
        self.error = 0
        if self.exin:
            raise Exception('Incorrect Parameters, must name files for existence test, use flags -i and -l')

        files_in_path = [f for f in os.listdir(self.dir)
                         if os.path.isfile(os.path.join(self.dir, f))]

        # are any of the exclude items in the file name?
        for item in self.arg_list:
            if item not in files_in_path:
                print("File: %s doesn't exist" % (str(item)))
                self.error = 1
            else:
                print("File: %s was found" % (str(item)))

    def run(self, values):
        self.add_parser_options()
        self.run_parser(values)
        self.type_route()

class FileBackup(ABase):

    def __init__(self):
        super(FileBackup, self).__init__()
        self.backupdir = None

    def add_parser_options(self):
        super(FileBackup, self).add_parser_options()
        self.parser.add_option("-b", "--backupdir", dest="backupdir")

    def run_parser(self, values):
        options, args = self.parser.parse_args(args=values )
        self.exin = options.exin
        self.dir = options.dir
        self.backupdir = options.backupdir

        if options.list:
            self.arg_list = options.list.split(',')

        self.print_to_log(
            "Current command line args:  Exclude (True) / Include (False): %s Directory: %s Ex/Include List: %s Backup Directory: %s" % (
                str(self.exin), str(self.dir), str(self.arg_list), str(self.backupdir)))

    def backup_files(self):
        """
        Will move the files specified to a subfolder of the dir directed
        named with the time stamp of the run

        """
        backup_path = os.path.join(self.backupdir, self.get_timestamp().replace(':', '-'))
        try:
            if not os.path.exists(backup_path):
                self.make_path(backup_path)
            if not os.path.exists(backup_path):
                raise IOError('Path was not made correctly')
            else:
                self.print_to_log('Backup path: %s' % backup_path)
            for item in self.file_list:
                try:
                    self.print_to_log('Backing up file: %s' % item)
                    shutil.copy(item, backup_path)
                except IOError, why:
                    self.error = 2
                    self.print_to_log(str(why))
                    self.print_to_log('Unable to archive file: %s continuing' % item)
        except IOError, why:
            self.print_to_log(str(why))
            self.print_to_log('Quiting with out archiving')
            self.error = 1

    def run(self, values):
        self.add_parser_options()
        self.run_parser(values)
        self.get_flies()
        self.backup_files()
        self.error = 0

class ExecSQL(ABase):
    """
    Sqlcmd -U FI#3 -P $333n -S 10.129 -d db -i D:\Imports\Scripts\testScript.sql

    goal is to replace the SQLCMD utility
    """

    def __init__(self):
        super(ExecSQL, self).__init__()
        self.SH = __import__('API.sql.helper')
        self.server = None
        self.password = None
        self.server = None
        self.database = None

    def add_parser_options(self):
        self.parser.add_option("-i", "-I", "--sql", dest="sql")
        self.parser.add_option("-u", "-U", "--user", dest="user")
        self.parser.add_option("-p", "-P", "--pass", dest="password")
        self.parser.add_option("-s", "-S", "--server", dest="server")
        self.parser.add_option("-d", "-D", "--database", dest="database")

    def run_parser(self, values):
        options, args = self.parser.parse_args(args=values )
        self.server = options.server
        self.password = options.password
        self.user = options.user
        self.database = options.database
        with open(options.sql) as _f:
            self.sql = _f.read()
        self.print_to_log(
            "Current command line args:  Server: %s User: %s Password: %s Database: %s SQL Script: %s" % (
                str(self.server), str(self.user), str(self.password), str(self.database), str(self.sql)))

    def make_sql_call(self):
        """
        make call to sql
        @return: if it worked
        """
        c_data = {'db_host': self.server,
            'db_user': self.user,
            'db_password': self.password,
            'db_database': self.database}
        db_conn = self.SH.sql.helper.sql_conn_obj(c_data)
        result, detail = db_conn.connect()
        self.print_to_log(detail)
        result, detail = db_conn.execute(self.sql)
        db_conn.shutdown()
        self.print_to_log(detail)

    def run(self, values):
        self.add_parser_options()
        self.run_parser(values)
        self.make_sql_call()

if __name__ == '__main__':
    func = sys.argv[1]
    tc = locals()[func]()
    print('--------*******xX Running function: ' + func + ' Xx********----------')
    tc.run(sys.argv[2:])
    print('--------*******xX Finished function: ' + func + ' Xx********----------')
    sys.exit(tc.error)
