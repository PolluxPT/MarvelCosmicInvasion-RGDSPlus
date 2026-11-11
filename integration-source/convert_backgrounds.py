import pathlib,struct,json,hashlib,time
import texture2ddecoder,etcpak
from PIL import Image
SRC=pathlib.Path('baseline/APPS/MarvelCosmicInvasion_RGDSPlus/gamedata/Content')
DST=pathlib.Path('build/APPS/MarvelCosmicInvasion_RGDSPlus/gamedata/Content')
def read7(b,o):
    v=0;s=0
    while True:
        c=b[o];o+=1;v|=(c&127)<<s
        if c<128:return v,o
        s+=7
def header(b):
    assert b[:3]==b'XNB' and not b[5]&0xc0
    n,o=read7(b,10)
    for _ in range(n):size,o=read7(b,o);o+=size+4
    _,o=read7(b,o);_,o=read7(b,o)
    return o,struct.unpack_from('<iiii',b,o)
def pad(image):
    w,h=image.size;pw=(w+3)//4*4;ph=(h+3)//4*4
    if (w,h)==(pw,ph):return image
    out=Image.new('RGBA',(pw,ph));out.paste(image,(0,0))
    if pw>w:out.paste(image.crop((w-1,0,w,h)).resize((pw-w,h)),(w,0))
    if ph>h:out.paste(out.crop((0,h-1,pw,h)).resize((pw,ph-h)),(0,h))
    return out
def main():
    manifest=[];start=time.monotonic()
    for p in sorted(SRC.rglob('*.xnb')):
        relative=p.relative_to(SRC);b=p.read_bytes();o,(fmt,w,h,levels)=header(b)
        is_bg=relative.parts[0]=='BG' or relative.parts[:2]==('Animations','BG')
        if fmt not in (25,26,27,28) or (not is_bg and fmt!=25):continue
        block={25:4,26:5,27:6,28:8}[fmt];pos=o+16;payload=bytearray();oldbytes=0;newbytes=0
        for level in range(levels):
            mw=max(1,w>>level);mh=max(1,h>>level);size=struct.unpack_from('<I',b,pos)[0];pos+=4
            data=b[pos:pos+size];pos+=size;oldbytes+=size
            assert size==((mw+block-1)//block)*((mh+block-1)//block)*16
            bgra=texture2ddecoder.decode_astc(data,mw,mh,block,block)
            image=Image.frombytes('RGBA',(mw,mh),bgra,'raw','BGRA');padded=pad(image)
            encoded=etcpak.compress_etc2_rgba(padded.tobytes(),*padded.size)
            assert len(encoded)==((mw+3)//4)*((mh+3)//4)*16
            decoded=texture2ddecoder.decode_etc2a8(encoded,mw,mh);assert len(decoded)==mw*mh*4
            payload+=struct.pack('<I',len(encoded))+encoded;newbytes+=len(encoded)
        assert pos==len(b)
        out=bytearray(b[:o]);out+=struct.pack('<iiii',25,w,h,levels)+payload;struct.pack_into('<I',out,6,len(out))
        target=DST/relative;target.write_bytes(out)
        manifest.append({'file':str(relative),'width':w,'height':h,'levels':levels,'original_format':fmt,'old_payload_bytes':oldbytes,'etc2_payload_bytes':newbytes,'sha256':hashlib.sha256(out).hexdigest()})
        if len(manifest)%20==0:print('Converted',len(manifest),'textures;',round(time.monotonic()-start,1),'seconds',flush=True)
    pathlib.Path('build/TextureConversion.json').write_text(json.dumps({'format':'ETC2 RGBA8/EAC, private FNA format 25','files':manifest,'count':len(manifest),'old_payload_bytes':sum(x['old_payload_bytes'] for x in manifest),'new_payload_bytes':sum(x['etc2_payload_bytes'] for x in manifest)},indent=2)+'\n')
    print('Completed',len(manifest),'textures;',round(time.monotonic()-start,1),'seconds',flush=True)
if __name__=='__main__':main()
