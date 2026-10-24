#!/usr/bin/env python3
"""Offline structural checks, not UI/rendering or Apple availability tests."""
from pathlib import Path
import struct, re, collections, json, hashlib, subprocess
BASELINE='af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6'
def baseline(path): return subprocess.check_output(['git','show',BASELINE+':'+path])
b=baseline('calf-cupertino-icons/src/commonMain/composeResources/font/sf_symbols.ttf')
n=struct.unpack_from('>H',b,4)[0]
t={struct.unpack_from('>4sIII',b,12+16*i)[0].decode():struct.unpack_from('>4sIII',b,12+16*i)[2:] for i in range(n)}
def u16(o): return struct.unpack_from('>H',b,o)[0]
def s16(o): return struct.unpack_from('>h',b,o)[0]
start,_=t['cmap']; maps=[]
for i in range(u16(start+2)):
 platform,encoding,offset=struct.unpack_from('>HHI',b,start+4+8*i); o=start+offset; fmt=u16(o); cmap={}
 if fmt==4:
  count=u16(o+6)//2; endoff=o+14; startoff=endoff+count*2+2; deltaoff=startoff+count*2; rangeoff=deltaoff+count*2
  for j in range(count):
   end=u16(endoff+2*j);begin=u16(startoff+2*j);delta=s16(deltaoff+2*j);roff=u16(rangeoff+2*j)
   for c in range(begin,min(end,0xfffe)+1):
    gid=(c+delta)&0xffff if roff==0 else u16(rangeoff+2*j+roff+2*(c-begin))
    if roff and gid: gid=(gid+delta)&0xffff
    if gid: cmap[c]=gid
 elif fmt==6:
  first,count=u16(o+6),u16(o+8)
  cmap={first+j:u16(o+10+2*j) for j in range(count) if u16(o+10+2*j)}
 elif fmt==12:
  groups=struct.unpack_from('>I',b,o+12)[0]
  for j in range(groups):
   a,z,g=struct.unpack_from('>III',b,o+16+12*j)
   cmap.update({c:g+c-a for c in range(a,z+1) if g+c-a})
 else: raise AssertionError(('Unhandled cmap',platform,encoding,fmt))
 # Font glyph lookup must use Unicode cmap, not Mac Roman cmap.
 if platform in (0,3): maps.append(cmap)
cmap={k:v for m in maps for k,v in m.items()}
const_text=baseline('calf-cupertino-icons/src/commonMain/kotlin/com/mohamedrejeb/calf/cupertino/icons/CupertinoIcons.kt').decode()
consts=re.findall(r'^\s*const val (`?\w+`?): Int = (0x[0-9A-Fa-f]+)\s*$',const_text,re.M); code={name.strip('`'):int(v,16) for name,v in consts}
cat=baseline('sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/CupertinoIconsCatalogData.kt').decode()
entries=[(a,b.strip('`'),c) for a,b,c in re.findall(r'IconEntry\("([^"]+)", CupertinoIcons\.(`?\w+`?), "([^"]+)"\)',cat)]
sf=baseline('calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/sf/symbols/SFSymbol.kt').decode()
syms=re.findall(r'^\s*const val (`?\w+`?) = "([^"]+)"\s*$',sf,re.M)
result={'baseline':BASELINE,'font_sha256':hashlib.sha256(b).hexdigest(),'font_bytes':len(b),'unicode_cmap_nonzero_mappings':len(cmap),'cupertino_constants':len(consts),'cupertino_unique_names':len(code),'cupertino_unique_codepoints':len(set(code.values())),'cupertino_missing_glyphs':[k for k,v in code.items() if v not in cmap],'cupertino_outside_BMP':[k for k,v in code.items() if not 0<=v<=65535],'catalogue_entries':len(entries),'catalogue_unique_names':len({v[0] for v in entries}),'catalogue_missing_references':[v for v in entries if v[1] not in code],'catalogue_unrepresented_constants':sorted(set(code)-{v[1] for v in entries}),'catalogue_categories':dict(collections.Counter(v[2] for v in entries)),'sf_symbols':len(syms),'sf_unique_identifiers':len({v[0] for v in syms}),'sf_unique_values':len({v[1] for v in syms}),'sf_duplicate_values':[v for v,c in collections.Counter(v[1] for v in syms).items() if c>1],'unparsed_cupertino_declarations':const_text.count('const val')-len(consts),'unparsed_sf_declarations':sf.count('const val')-len(syms)}
assert not any(result[k] for k in ['cupertino_missing_glyphs','cupertino_outside_BMP','catalogue_missing_references','catalogue_unrepresented_constants','sf_duplicate_values','unparsed_cupertino_declarations','unparsed_sf_declarations'])
assert result['cupertino_constants']==result['cupertino_unique_names']==result['catalogue_entries']==result['catalogue_unique_names']==1322
assert result['sf_symbols']==result['sf_unique_identifiers']==result['sf_unique_values']==6984
print(json.dumps(result,indent=2))
