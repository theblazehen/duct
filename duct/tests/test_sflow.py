from twisted.trial import unittest
from twisted.internet import defer

from duct.protocol.sflow import protocol


# Long strings are the devils play things
testPacket = b'\x00\x00\x00\x05\x00\x00\x00\x01\xac\x1e\x00\x05\x00\x00\x00\x00\x00\x00\x02L\x01?lD\x00\x00\x00\x05\x00\x00\x00\x01\x00\x00\x00\xc4\x00\x00\x01\xff\x00\x00\x00\x10\x00\x00\x00\x80\x00(\x1d6\x00\x00\x03\x9a\x00\x00\x00\x03\x00\x00\x00\x10\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x84\x00\x00\x00\x01\x00\x00\x00u\x00\x00\x00\x04\x00\x00\x00t\xe4\xce\x8f.\x8a\xd4\xd4\xcam\x97r*\x08\x00Ex\x00cM-\x00\x007\x11kh)\x86\xf4\x89\xac\x1e\x00O\x05\xd8\xe3\xeb\x00O\xe3\x9d\xd8\xd0m\x15B\x81;\xda\x98\xa7\xd0\x00\t\xc7\xbe>K\x9b\xd5\xd3n\x15\xb9U\x1c0\x1e]+i2\xc9\xb5N4\xca"G\x1f\xfe\x86H\x9b\xc0\xa0\xb9\x9d\x97\xb9yHMIzI\xf9\xc8\xcd\x88\xadgtx\x85\x90\xf1\xfa_\x98-\x1a\x00\x00\x00\x00\x00\x03\xe9\x00\x00\x00\x10\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x94\x00\x00\x01\xd4\x00\x00\x00\n\x00\x00\x00\x80\x00fH)\x00\x00\x04\x0b\x00\x00\x00\x03\x00\x00\x00\n\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00T\x00\x00\x00\x01\x00\x00\x00F\x00\x00\x00\x04\x00\x00\x00D(77\x1b\x02\xf4\xd4\xcam\x97r*\x08\x00E\x80\x004\xb6\x13@\x00&\x06\xdf\xa22\x11\xe0\x11\xac\x1e\x00M\x01\xbb\xee\xae\x953w\x93"j\xbb\x1d\x80\x10\x00S\x0f\xb6\x00\x00\x01\x01\x08\n\x83\xe4\x92\x18ASv\x1d\x00\x00\x00\x00\x03\xe9\x00\x00\x00\x10\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x94\x00\x00\x01\xd5\x00\x00\x00\n\x00\x00\x00\x80\x00fH)\x00\x00\x04\x10\x00\x00\x00\n\x00\x00\x00\x03\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00T\x00\x00\x00\x01\x00\x00\x00F\x00\x00\x00\x04\x00\x00\x00D\xd4\xcam\x97r*(\xcf\xe9Z\xd8a\x08\x00E\x00\x004\x13\x89@\x00@\x06~8\xac\x1e\x00ZRK\xaa?\xf1\xfe\xed\xe1"\xe8\x97\xd6c\xbfC\x0e\x80\x11 \x00N\x9c\x00\x00\x01\x01\x08\n;\x829Y\x00\x11\xa8\xc3\x00\x00\x00\x00\x03\xe9\x00\x00\x00\x10\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\xff\xff\xff\xff\x00\x00\x00\x02\x00\x00\x00\xa8\x00\x00\x00!\x00\x00\x00\x0c\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00X\x00\x00\x00\x0c\x00\x00\x00\x06\x00\x00\x00\x00\x00\x98\x96\x80\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x004\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x94\x00\x00\x02\x00\x00\x00\x00\x10\x00\x00\x00\x80\x00(\x1e\x1a\x00\x00\x03\x9b\x00\x00\x00\x10\x00\x00\x00\x03\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00T\x00\x00\x00\x01\x00\x00\x00F\x00\x00\x00\x04\x00\x00\x00D\xd4\xcam\x97r*\\\n[\xe0\xe4\x14\x08\x00E\x00\x004\x04\r@\x00@\x06\x11\xfa\xac\x1e\x00\xae\x17C`\xae\x8f\xe0\x01\xbb\xac ;\xa8\x10\xc0\xab\xd7\x80\x10/\xea\x0e\'\x00\x00\x01\x01\x08\n\x00JuM\xe0\xd3\x87\x87\x00\x00\x00\x00\x03\xe9\x00\x00\x00\x10\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\xff\xff\xff\xff'

class Test(unittest.TestCase):
    def test_decode(self):
        
        proto = protocol.Sflow(testPacket, '172.30.0.5')

        self.assertTrue(proto.version == 5)

        self.assertTrue(len(proto.samples) == 5)
