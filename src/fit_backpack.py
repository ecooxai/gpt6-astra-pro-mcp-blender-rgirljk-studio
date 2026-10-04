"""Smooth, narrow backpack straps fitted by centerline and tangent frame."""
from mathutils.bvhtree import BVHTree
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
vv=[];ff=[]
for ob in CHAR.objects:
    if ob.type!="MESH" or not ob.name.startswith("Blouse"):continue
    ev=ob.evaluated_get(dg);me=ev.to_mesh();base=len(vv)
    vv.extend(ob.matrix_world@v.co for v in me.vertices)
    ff.extend(tuple(base+i for i in q.vertices) for q in me.polygons);ev.to_mesh_clear()
cloth_bvh=BVHTree.FromPolygons(vv,ff,all_triangles=False)
for ob in list(CHAR.objects):
    if any(k in ob.name for k in ["padded shoulder strap","webbing return","Strap buckle","Strap stitching"]):bpy.data.objects.remove(ob,do_unlink=True)

def contact_frame(q):
    c=q.copy();axis=Vector((1,0,0));normal=Vector((0,-1,0))
    hit,_,_,_=cloth_bvh.ray_cast(Vector((q.x,-.50,q.z)),Vector((0,1,0)),1)
    blend=max(0,min(1,(.012-q.y)/.045));blend=blend*blend*(3-2*blend)
    if hit is not None and blend>0:
        c.y=c.y*(1-blend)+(hit.y-.006)*blend
        w,d=blouse_profile(q.z);u=max(-.94,min(.94,q.x/w))
        slope=d*u/(w*sqrt(max(.03,1-u*u)))
        axis=Vector((1,slope*blend,0)).normalized();normal=Vector((axis.y,-axis.x,0))
    return c,axis,normal

def fitted_band(name,points,widths,mat,thickness):
    cs=catmull(points,72);vs=[];fs=[];edgel=[];edger=[]
    for i,q in enumerate(cs):
        t=i/(len(cs)-1);c,axis,n=contact_frame(q);w=float(np.interp(t,np.linspace(0,1,len(widths)),widths))
        for j,u in enumerate(np.linspace(-1,1,7)):
            v=c+axis*(float(u)*w)+n*(.001*(1-u*u));vs.append(v)
        edgel.append(vs[-7]+n*.0003);edger.append(vs[-1]+n*.0003)
    for i in range(len(cs)-1):
        for j in range(6):k=i*7+j;fs.append((k,k+7,k+8,k+1))
    ob=mesh(name,vs,fs,mat);m=ob.modifiers.new("Strap cloth thickness","SOLIDIFY");m.thickness=thickness;m.offset=-1
    if "padded" in name:
        line("Fitted strap edge stitches",edgel,stitch,.00022)
        line("Fitted strap edge stitches",edger,stitch,.00022)
    return ob
for s in [-1,1]:
    fitted_band("Fitted padded backpack strap "+str(s),[(s*.107,.128,1.324),(s*.127,.012,1.350),(s*.119,-.059,1.318),(s*.112,-.072,1.248)],[.016,.019,.018,.014],navy,.0045)
    fitted_band("Fitted narrow return webbing "+str(s),[(s*.112,-.072,1.265),(s*.118,-.046,1.182),(s*.134,.008,1.112),(s*.108,.120,1.09)],[.0075,.0075,.007,.007],webbing,.0022)
    for z in [1.250,1.221]:
        c,axis,n=contact_frame(Vector((s*.112,-.072,z)));c+=n*.003
        angle=math.atan2(axis.y,axis.x)
        for dx in [-.0105,.0105]:
            o=box("Fitted buckle side "+str(s),c+axis*dx,(.003,.005,.019),buckle,.0010);o.rotation_euler.z=angle
        for dz in [-.008,0,.008]:
            o=box("Fitted buckle crossbar "+str(s),c+Vector((0,0,dz)),(.024,.005,.0028),buckle,.0008);o.rotation_euler.z=angle
print("SMOOTH_BACKPACK_STRAPS_BUILT",flush=True)
