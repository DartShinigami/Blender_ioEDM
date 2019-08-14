import tempfile
import struct
from collections import Counter

from .mathtypes import matrix_to_sequence

class BaseWriter(object):
  def __init__(self, filename):
    self.filename = filename
    self.stream = None 

    self.body = tempfile.TemporaryFile()
    self.head = tempfile.TemporaryFile();
    
    self.typeLog = Counter()
    self.strings = []
     
  def find_string(self, strAs):
    i = 0
    ln = len( self.strings )
    while i < ln :
      if self.strings[i] == strAs :
        return i;
      i += 1
    self.strings.append( strAs )
    return ln    
    
  def phase1(self):
    self.stream = self.body
    
  def phase2(self):
    self.stream = self.head

  def finish(self):
    if not self.body: 
      return False
    
    if not self.head:
      return False
      
    edmFile = open( self.filename, "wb" );
  
    streamBodyLen = self.body.tell()
    streamHeadLen = self.head.tell()
    
    self.body.seek( 0, 0 )
    self.head.seek( 0, 0 )
    
    readTakeBuffSize = 1024
    
    # read streamOne into the edm file
    readTake = 0
    while streamHeadLen != 0:
      if ( streamHeadLen > readTakeBuffSize ):
        readTake = readTakeBuffSize;
      else:
        readTake = streamHeadLen
        
      buf = self.head.read( readTake )
      edmFile.write( buf )
      streamHeadLen -= readTake
      
      
    # read streamTwo into the edm file
    readTake = 0
    while streamBodyLen != 0:
      if ( streamBodyLen > readTakeBuffSize ):
        readTake = readTakeBuffSize;
      else:
        readTake = streamBodyLen
        
      buf = self.body.read( readTake )
      edmFile.write( buf )
      streamBodyLen -= readTake
  
    edmFile.close()
    self.close()

  def close(self):
    if self.body :
      self.body.close()
      self.body = None
      
    if self.head :
      self.head.close()
      self.head = None
      
    self.stream = None

  def write(self, data):
    self.stream.write(data)
    
  def write_stringtable(self):
    print( "Writing string table" )
  
    sizePos = self.stream.tell()
    # write dummy size
    self.write_uint(0)
    # Now the string table its self
    i = 0
    ln = len(self.strings)
    while i < ln :
      s = self.strings[i].encode("windows-1251") 
      # the string 
      self.write(s)
      # the null
      self.write_uchar(0)
      
      print( "index:", i, " str:", s)
      i = i+1
    
    # Another null just to finish it all off
    self.write_uchar(0)
    
    endPos = self.stream.tell();
    # work out size, remember not to take into about the size of size
    strTableSize = endPos - ( sizePos + 4 )
    self.stream.seek(sizePos, 0)
    self.write_uint(strTableSize)
    self.stream.seek(endPos, 0)

  def write_uchar(self, value):
    self.stream.write(struct.pack("B", value))

  def write_uchars(self, values):
    self.stream.write(struct.pack("{}B".format(len(values)), *values))

  def write_ushort(self, value):
    self.stream.write(struct.pack("<H", value))

  def write_ushorts(self, values):
    self.stream.write(struct.pack("<{}H".format(len(values)), *values))

  def write_uint(self, value):
    self.stream.write(struct.pack("<I", value))

  def write_uints(self, values):
    self.stream.write(struct.pack("<{}I".format(len(values)), *values))

  def write_int(self, value):
    self.stream.write(struct.pack("<i", value))

  def write_ints(self, values):
    self.stream.write(struct.pack("<{}i".format(len(values)), *values))

  def write_float(self, value):
    self.stream.write(struct.pack("<f", value))

  def write_floats(self, values):
    self.stream.write(struct.pack("<{}f".format(len(values)), *values))

  def write_double(self, value):
    self.stream.write(struct.pack("<d", value))

  def write_doubles(self, values):
    self.stream.write(struct.pack("<{}d".format(len(values)), *values))

  def write_string(self, value, lookup=True):
    if lookup :
      idx = self.find_string( value )
      self.write_uint(idx)
    else :
      data = value.encode("windows-1251")
      self.write_uint(len(data))
      self.write(data)

  def write_list(self, data, writer):
    self.write_uint(len(data))
    for entry in data:
      writer(self, entry)

  def write_vec2f(self, vector):
    self.write_floats([vector[0], vector[1]])
  
  def write_vec3f(self, vector):
    self.write_floats([vector[0], vector[1], vector[2]])

  def write_vec3d(self, vector):
    self.write_doubles([vector[0], vector[1], vector[2]])

  def write_vecf(self, vector):
    self.write_floats(vector)

  def write_vecd(self, vector):
    self.write_doubles(vector)

  def write_matrixf(self, matrix):
    self.write_floats(matrix_to_sequence(matrix))

  def write_matrixd(self, matrix):
    self.write_doubles(matrix_to_sequence(matrix))

  def write_quaternion(self, quat):
    self.write_doubles([quat[1], quat[2], quat[3], quat[0]])

  def write_named_type(self, item, typename=None):
    name = typename or item.forTypeName
    self.write_string(name)
    item.write(self)

  def mark_written(self, name, count=1):
    self.typeLog[name] += count
