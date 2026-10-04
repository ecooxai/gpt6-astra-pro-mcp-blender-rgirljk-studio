"""Check glTF conformance, decoded scene geometry, source provenance and limb lengths."""
from pathlib import Path
import sys,json,struct,re,subprocess,math
root=Path(__file__).resolve().parents[1];rev=int(sys.argv[1]);base='gpt6_astra_pro_mcp_blender_rgirljk'
report={'revision':rev,'files':[],'checks':{},'passed':False}
try:
    subprocess.run(['node','tests/format_qa.mjs',str(rev)],cwd=root,check=True)
    fmt=json.loads((root/'build'/f'format_qa_r{rev:02d}.json').read_text())
    for item in fmt['files']:
        path=root/'build'/item['file'];raw=path.read_bytes();magic,version,length=struct.unpack_from('<4sII',raw,0)
        assert magic==b'glTF' and version==2 and length==len(raw),path.name
        n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4E4F534A;doc=json.loads(raw[20:20+n])
        assert not doc.get('cameras');assert 'KHR_lights_punctual' not in doc.get('extensionsUsed',[])
        for im in doc.get('images',[]):
            assert 'bufferView' in im and 'uri' not in im,im
            assert not re.search('reference|photo|scan|rgirljk',im.get('name',''),re.I),im
        report['files'].append({k:item[k] for k in ['file','bytes','meshes','triangles','size','bounds','errors','warnings','passed']})
    # Quantized accessor bounds are integer-domain values; only decoded/world bounds are compared in metres.
    pairs=[(fmt['files'][0],fmt['files'][1]),(fmt['files'][2],fmt['files'][3])]
    deviations=[max(abs(a['bounds'][k][i]-b['bounds'][k][i]) for k in ['min','max'] for i in range(3)) for a,b in pairs]
    assert max(deviations)<.001,deviations
    metrics=json.loads((root/'build'/f'geometry_metrics_r{rev:02d}.json').read_text());legs=metrics['leg_segments_metres']
    errors={bone:abs(legs['L'][bone]-legs['R'][bone]) for bone in ['femur','tibia']};assert max(errors.values())<1e-5,errors
    source_dir=root/'build/jobs'/f'r{rev:03d}'/'source'
    source='\n'.join(f.read_text() for f in source_dir.glob('*.py') if f.name not in ['model_qa.py','format_qa.py'])
    assert not any(token in source for token in ['bpy.ops.import_scene','bpy.data.images.load','bpy.data.libraries.load'])
    report['checks']={'fourGLBVariantsValidated':True,'decodedWorldBounds':True,'embeddedOriginalTexturesOnly':True,'noStudioLightsOrCameras':True,'noExternalArtImportCallsInModelSource':True,'compressionBoundsDifferenceMetres':deviations,'legLengthDifferenceMetres':errors}
    report['passed']=True
except Exception as e:report['failure']=repr(e)
(root/'build'/f'model_qa_r{rev:02d}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if not report['passed']:raise SystemExit(1)
