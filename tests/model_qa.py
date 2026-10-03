"""Validate authored model files and geometry metadata; never analyze reference pixels."""
from pathlib import Path
import sys,json,struct,math,re
root=Path(__file__).resolve().parents[1];rev=int(sys.argv[1]);base='gpt6_astra_pro_mcp_blender_rgirljk';report={'revision':rev,'files':[],'checks':{}}
for suffix in ['', '_web', '_lite', '_lite_web']:
    path=root/'build'/f'{base}{suffix}_r{rev:02d}.glb'
    if not path.exists():continue
    raw=path.read_bytes();magic,version,length=struct.unpack_from('<4sII',raw,0)
    assert magic==b'glTF' and version==2 and length==len(raw),f'Invalid GLB header: {path.name}'
    n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4E4F534A
    doc=json.loads(raw[20:20+n]);assert not doc.get('cameras');assert 'KHR_lights_punctual' not in doc.get('extensionsUsed',[])
    images=doc.get('images',[])
    for im in images:
        assert 'bufferView' in im and 'uri' not in im,f'External texture dependency: {im}'
        assert not re.search('reference|photo|scan|rgirljk',im.get('name',''),re.I),f'Unexpected texture source: {im}'
    triangles=0
    for mesh in doc.get('meshes',[]):
        for primitive in mesh['primitives']:
            assert primitive.get('mode',4)==4
            pa=doc['accessors'][primitive['attributes']['POSITION']]
            assert all(math.isfinite(x) and abs(x)<3 for x in pa['min']+pa['max'])
            triangles+=doc['accessors'][primitive['indices']]['count']//3 if 'indices' in primitive else pa['count']//3
    report['files'].append({'file':path.name,'bytes':len(raw),'meshes':len(doc.get('meshes',[])),'triangles':triangles,'embeddedTextures':[im.get('name') for im in images],'passed':True})
metrics=json.loads((root/'build'/f'geometry_metrics_r{rev:02d}.json').read_text());legs=metrics['leg_segments_metres']
errors={bone:abs(legs['L'][bone]-legs['R'][bone]) for bone in ['femur','tibia']}
assert max(errors.values())<1e-5,errors
source=(root/'src/build_character.py').read_text();forbidden=['bpy.ops.import_scene','bpy.data.images.load','bpy.data.libraries.load']
assert not any(token in source for token in forbidden)
report['checks']={'glbHeaders':True,'finitePositionBounds':True,'embeddedOriginalTexturesOnly':True,'noStudioLightsOrCameras':True,'noExternalArtImportCalls':True,'legLengthDifferenceMetres':errors}
report['passed']=bool(report['files']);out=root/'build'/f'model_qa_r{rev:02d}.json';out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
