import sys
import re

class BigWig_converter(object):
    """
    Bed to BigWig converter
    """
    
    def __init__(self, infile):
        self.infile = open(infile, "r").readlines()
        #self.infile.sort(key=lambda l: float(l.split("\t")[1]) if not l.startswith("track") else None)
        self.header = _get_header(infile)
        self.record_lines = []

    def get_info(self, start_line, next_line):
        """
        Returns info about coords step, chromosome number
        and start coord.
        
        start_line - first line in the record
        next_line - next line to extract step 
        """    
        splitted_1 = start_line.split("\t")
        splitted_2 = next_line.split("\t")
        step = int(splitted_2[1]) - int(splitted_1[1])
        chrom = splitted_1[0]
        start_value = splitted_1[1]
        span = int(splitted_1[2]) - int(splitted_1[1])
        
        rec_name = 'fixedStep chrom=%s start=%s  step=%s span=%s' % (chrom, start_value, step, span)
        return rec_name
    
    def get_values(self):
        """
        Gets values and adds them to record_lines.
        """
        fixed_wig = []
        
        for idx,record in enumerate(self.infile[1:-1]):
                self.record_lines.append(self.get_info(record, self.infile[idx+2]))
                self.record_lines.append(record.split("\t")[3].rstrip())           
                
    def make_header(self):
        """
        Creates new header line.
        """
        splitted_header = self.header.split(" ")
        name_desc = " ".join(splitted_header[2:]).rstrip()
        new_header = 'track type=wiggle_0 %s' % (name_desc)
        print new_header
        self.record_lines.append(new_header)
       
    def reduce_redundancy(self):
        pass

    def do(self):
        self.make_header()
        self.get_values()

class BedGraph_converter(object):
    """
    BigWig to Bed converter
    """
    
    def __init__(self, infile):
        self.infile = open(infile, "r").readlines()
        self.header = _get_header(infile)
        self.record_lines = []
        self.isFixed = False

    def isFixedWig(self):
        """
        Checks wiggle format.
        """
        if self.infile[1].startswith("fixedStep"):
            self.isFixed = True

    def make_from_fixed(self):
        """
        Makes bed records from fixedStep type wig file.
        """
        chrom, start_value, span, step = self.get_info()
        new_start_value = start_value

        for record in self.infile:
            new_record = ""
            if record.startswith("track") or record.startswith("fixedStep"):
                pass
            else:
                end_value = int(new_start_value) + int(span)
                print end_value
                new_record = "%s %s %s %s" % (chrom, new_start_value, end_value, record.rstrip())
                self.record_lines.append(new_record)
                new_start_value += step


    def make_from_variable(self):
        """
        Make bed records from variableStep type wig file.
        """
        
        for idx,record in enumerate(self.infile):
            new_record = ""
            if record.startswith("track"):
                pass
            if record.startswith("variableStep"):
                chrom, start_value, span, step = self.get_info(record)
                print chrom, start_value, span, step
                
                for chr_record in self.infile[idx+1:]:
                        if chr_record.startswith("variableStep"):
                                break
                        else:
                                new_start_value = int(chr_record.split(" ")[0])
                                value = chr_record.split(" ")[1]
                                end_value = new_start_value + int(span)
                                new_record = "%s %s %s %s" % (chrom, new_start_value, end_value, value.rstrip())
                                self.record_lines.append(new_record)

    def get_info(self, header_line):
        """
        Returns necessary info from header line.
        """
        splitted_1 = header_line.split(" ")
        print splitted_1
        
        step = None
        chrom = ""
        start_value = 0
        span = 0

        for info in splitted_1:
            if info.startswith("chrom"):
               chrom = info.split("=")[1]
            if info.startswith("start"):
                start_value = int(info.split("=")[1])
            if info.startswith("span"):
                span = int(info.split("=")[1])
            if info.startswith("step"):
                step = int(info.split("=")[1])

        return (chrom, start_value, span, step)

    def make_header(self):
        """
        Makes header for new bed file.
        """
        splitted_header = self.header.split(" ")
        name_desc = " ".join(splitted_header[2:]).rstrip()
        new_header = 'track type=bedGraph %s' % (name_desc)
        print new_header
        self.record_lines.append(new_header)

    def do(self):
        self.isFixedWig()
        print self.isFixed
        self.make_header()

        if self.isFixed:
            self.make_from_fixed()
        else:
            self.make_from_variable()


def _check_format(infile):
    """
    Checks input file format and decides
    whether we use Parse_bigwig or bedgraph converter
    """
    infile = _get_header(infile)
    format = ""

    if "bedGraph" in infile:
        format = "bed"
    if "wiggle_0" in infile:
        format = "wig"

    return format

def _get_header(infile):
    """
    Yields file header
    """
    with open(infile, "r") as f:
        first_line = f.readline()
    
    return first_line


if __name__ == '__main__':
    if len(sys.argv) != 2:
        exit("USAGE: converter.py input_file_path")
    else:
        input_file = sys.argv[1]

    format = _check_format(input_file)

    if format == "bed":
        bw = BigWig_converter(input_file)
        bw.do()
        out_list = bw.record_lines
    elif format == "wig":
        bg = BedGraph_converter(input_file)
        bg.do()
        out_list = bg.record_lines

    with open("converted_file."+format, "w") as converted_file:
        for line in out_list:
            converted_file.write(line+"\n")

    converted_file.close()
        
