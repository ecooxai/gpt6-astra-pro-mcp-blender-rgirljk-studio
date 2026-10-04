"""Bake only the authored sculpt colors, then add deterministic original skin variation."""
# Angular UVs preserve the front, cheeks and back of the head in one non-overlapping atlas.
uvlay=hm.data.uv_layers.get('SkinUV') or hm.data.uv_layers.new(name='SkinUV')
coords=[]
for v in hm.data.vertices:
    x,y,z=v.co;w,_=shape(z);a=math.asin(max(-1,min(1,x/max(w,.0005))))
    if y>center_y(z)+.00002:a=pi-a
    coords.append(((a/(2*pi)+.5)%1,(z-ZP[0])/(ZP[-1]-ZP[0])))
for poly in hm.data.polygons:
    us=[coords[hm.data.loops[li].vertex_index][0] for li in poly.loop_indices];seam=max(us)-min(us)>.5
    for li,u in zip(poly.loop_indices,us):
        vi=hm.data.loops[li].vertex_index;uvlay.data[li].uv=(u+1 if seam and u<.5 else u,coords[vi][1])
uvlay.active_render=True
N=2048
atlas=bpy.data.images.new('Original sculpt-color skin atlas',width=N,height=N,alpha=True,float_buffer=True)
atlas.colorspace_settings.name='sRGB'
nt=headskin.node_tree;out=nt.nodes.get('Material Output');bsdf=nt.nodes.get('Principled BSDF')
tex=nt.nodes.new('ShaderNodeTexImage');tex.image=atlas;tex.label='Original vertex-color bake and deterministic pigment variation';nt.nodes.active=tex
for n in nt.nodes:n.select=False
tex.select=True
vc=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeVertexColor');emission=nt.nodes.new('ShaderNodeEmission');nt.links.new(vc.outputs['Color'],emission.inputs['Color']);emission.inputs['Strength'].default_value=1
nt.links.new(emission.outputs[0],out.inputs['Surface'])
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
bpy.ops.object.select_all(action='DESELECT');hm.select_set(True);bpy.context.view_layer.objects.active=hm
bpy.ops.object.bake(type='EMIT',margin=10,use_clear=True)
nt.links.new(bsdf.outputs[0],out.inputs['Surface']);nt.nodes.remove(emission)
pixels=np.array(atlas.pixels[:],dtype=np.float32).reshape(N,N,4)
yy,xx=np.mgrid[0:N,0:N].astype(np.float32);u=xx/N;v=yy/N
rng=np.random.default_rng(41723)
fine=rng.normal(0,1,(N,N)).astype(np.float32)
fine=(fine*4+np.roll(fine,1,0)+np.roll(fine,-1,0)+np.roll(fine,1,1)+np.roll(fine,-1,1))/8
slow=np.zeros((N,N),np.float32)
for frequency,amp in [(8,.52),(17,.27),(37,.14),(81,.07)]:
    phase=rng.uniform(0,2*pi);slow+=amp*np.sin(2*pi*(u*frequency+v*frequency*.67)+phase)*np.cos(2*pi*v*frequency*.42+phase*.7)
for c,slow_amp in enumerate([.026,-.012,-.017]):pixels[:,:,c]*=1+.010*fine+slow_amp*slow
pixels[:,:,:3]=np.clip(pixels[:,:,:3],0,1);atlas.pixels.foreach_set(pixels.ravel());atlas.update()
atlas.filepath_raw=str(BUILD/'Original sculpt-color skin atlas.png');atlas.file_format='PNG';atlas.save();atlas.pack()
nt.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
hm['original_procedural_skin_atlas']=True
print('ORIGINAL_SCULPT_COLOR_ATLAS_BAKED',N,flush=True)
del pixels,yy,xx,u,v,fine,slow,coords
