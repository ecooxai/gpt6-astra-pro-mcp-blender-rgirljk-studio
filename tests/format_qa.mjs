/** Validate original and compressed exports; compression is decoded before binary validation. */
import fs from 'node:fs';
import path from 'node:path';
import {NodeIO,getBounds} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {MeshoptDecoder} from 'meshoptimizer';
import validator from 'gltf-validator';
const revision=Number(process.argv[2]);
if(!Number.isInteger(revision)||revision<1)throw new Error('Usage: node tests/format_qa.mjs REVISION');
await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const report={revision,validator:validator.version(),checkedAt:new Date().toISOString(),files:[],passed:false};
const base='gpt6_astra_pro_mcp_blender_rgirljk',rev=String(revision).padStart(2,'0');
try{
 for(const suffix of ['','_web','_lite','_lite_web']){
  const name=`${base}${suffix}_r${rev}.glb`,file=path.join('build',name),raw=new Uint8Array(fs.readFileSync(file));
  const doc=await io.readBinary(raw),scene=doc.getRoot().listScenes()[0];if(!scene)throw new Error('No scene in '+name);
  const bounds=getBounds(scene);let triangles=0;
  for(const mesh of doc.getRoot().listMeshes())for(const primitive of mesh.listPrimitives())triangles+=(primitive.getIndices()?.getCount()||primitive.getAttribute('POSITION').getCount())/3;
  const compression=doc.getRoot().listExtensionsUsed().find(e=>e.extensionName==='EXT_meshopt_compression');
  let validatedBytes=raw;if(compression){compression.dispose();validatedBytes=await io.writeBinary(doc)}
  const validation=await validator.validateBytes(validatedBytes,{uri:name,maxIssues:1000,externalResourceFunction:async uri=>{throw new Error('External resource is forbidden: '+uri)}});
  const size=bounds.max.map((v,i)=>v-bounds.min[i]);
  const bounded=[...bounds.min,...bounds.max].every(Number.isFinite)&&size[1]>1.3&&size[1]<2.0&&size[0]>.25&&size[0]<.8&&size[2]>.15&&size[2]<.8;
  const entry={file:name,bytes:raw.length,decodedForValidation:!!compression,meshes:doc.getRoot().listMeshes().length,triangles,bounds,size,errors:validation.issues.numErrors,warnings:validation.issues.numWarnings,infos:validation.issues.numInfos,messages:validation.issues.messages,worldBoundsPassed:bounded,passed:validation.issues.numErrors===0&&bounded};
  report.files.push(entry);console.log(name,JSON.stringify({errors:entry.errors,warnings:entry.warnings,triangles,size,passed:entry.passed}));
 }
 report.passed=report.files.length===4&&report.files.every(f=>f.passed);
}catch(error){report.failure=String(error)}
fs.writeFileSync(`build/format_qa_r${rev}.json`,JSON.stringify(report,null,2));
console.log('FORMAT_QA_PASSED',report.passed);if(!report.passed)process.exitCode=1;
