"""Fit authored front straps to the actual blouse/sleeve geometry."""
from mathutils.bvhtree import BVHTree
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
vv=[];ff=[]
for ob in CHAR.objects:
    if ob.type!="MESH" or not (ob.name.startswith("Blouse") or ob.name.startswith("Sleeve")):continue
    ev=ob.evaluated_get(dg);me=ev.to_mesh();base=len(vv)
    vv.extend(ob.matrix_world@v.co for v in me.vertices)
    ff.extend(tuple(base+i for i in poly.vertices) for poly in me.polygons)
    ev.to_mesh_clear()
cloth_bvh=BVHTree.FromPolygons(vv,ff,all_triangles=False)
def fitted_strap(q,name):
    if q.y>=-.018:return q
    hit,normal,idx,dist=cloth_bvh.ray_cast(Vector((q.x,-.50,q.z)),Vector((0,1,0)),1.0)
    if hit is None:return q
    if "buckle" in name.lower():off=-.009+max(-.006,min(.006,q.y+.092))
    elif "stitch" in name.lower():off=-.0068
    elif "webbing" in name.lower():off=-.0045
    else:off=-.006
    return Vector((q.x,hit.y+off,q.z))
count=0
for ob in list(CHAR.objects):
    if not any(key in ob.name for key in ["padded shoulder strap","webbing return","Strap buckle","Strap stitching"]):continue
    mat=ob.matrix_world.copy();inv=mat.inverted()
    if ob.type=="MESH":
        for v in ob.data.vertices:
            q=mat@v.co;n=fitted_strap(q,ob.name);count+=(q-n).length>1e-6;v.co=inv@n
        ob.data.update()
    elif ob.type=="CURVE":
        for sp in ob.data.splines:
            for v in sp.points:
                q=mat@Vector(v.co[:3]);n=fitted_strap(q,ob.name);count+=(q-n).length>1e-6;n=inv@n;v.co=(*n,1)
print("STRAP_VERTICES_FITTED",count,flush=True)
