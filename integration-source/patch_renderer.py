"""Private format 25 becomes ETC2 RGBA/EAC; its 4x4/16-byte ABI is retained."""
import pathlib,hashlib,struct,sys
OLD='199f1cf948c8da7b7bd6e7ed380010a4efb31bb6ecb3ec36dc669546509a83d2'
ADDRESS=0x68650+25*4
def patch(path):
    p=pathlib.Path(path);b=bytearray(p.read_bytes())
    if hashlib.sha256(b).hexdigest()!=OLD:raise RuntimeError('Unexpected renderer version; no bytes changed.')
    phoff=struct.unpack_from('<Q',b,32)[0];entsize,count=struct.unpack_from('<HH',b,54)
    offset=None
    for i in range(count):
        typ,flags,off,va,pa,filesize,memsize,align=struct.unpack_from('<IIQQQQQQ',b,phoff+i*entsize)
        if typ==1 and va<=ADDRESS<va+filesize:offset=off+ADDRESS-va;break
    assert offset is not None and struct.unpack_from('<I',b,offset)[0]==0x93b0
    struct.pack_into('<I',b,offset,0x9278);p.write_bytes(b)
    print('ETC2 texture-table patch:',hex(offset),hashlib.sha256(b).hexdigest())
if __name__=='__main__':patch(sys.argv[1])
