"""Original surface-fitted hair locks, wisps and flyaways; no imported hair assets."""
from mathutils.bvhtree import BVHTree
hair_bvh=BVHTree.FromPolygons([v.co.copy() for v in hair_ob.data.vertices],[tuple(f.vertices) for f in hair_ob.data.polygons],all_triangles=False)
lockmat=hairbase.copy();lockmat.name="Groom - layered dark locks"
lockmat.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.40
lockmat.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value=.31
flymat=material("Groom - airy dark fibres",(.008,.0065,.0065),.42)
flymat.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value=.28

def front_surface(x,z):
    y=face_y(x,z)
    hit,_,_,_=hair_bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)),1)
    if hit is not None:y=min(y,hit.y)
    return y

def forehead_lock(name,points,width,phase=0):
    ps=bez([(x,0,z) for x,z in points],56);vs=[];fs=[];uv=[]
    for i,c in enumerate(ps):
        t=i/55;tangent=(ps[min(55,i+1)]-ps[max(0,i-1)]).normalized();across=Vector((-tangent.z,0,tangent.x))
        w=width*sin(pi*min(.9999,t))**.60*(1-.55*t)
        for j,u in enumerate(np.linspace(-1,1,7)):
            q=c+across*(float(u)*w)
            q.y=front_surface(q.x,q.z)-(.00035+.00085*sin(pi*t))-.00055*(1-u*u)*sin(pi*t)
            vs.append(q);uv.append((phase+float(u)*.011,t))
    for i in range(55):
        for j in range(6):k=i*7+j;fs.append((k,k+7,k+8,k+1))
    ob=mesh(name,vs,fs,lockmat,parent=head,uv=uv)
    mod=ob.modifiers.new("Fine hair lock thickness","SOLIDIFY");mod.thickness=.00013
    return ob
for k in range(5):
    d=(k-2)*.0013
    forehead_lock("Fringe - attached sweeping wisp "+str(k),[(.050+d,.129),(.074+d,.089),(.049+d,.048),(.020+k*.002,.029+k*.001)],.0028-k*.00025,.17+k*.05)
# Replace the old packed, straight face-framing strips with individually tapered curves.
for ob in list(CHAR.objects):
    if ob.name.startswith("Soft face-framing strands"):bpy.data.objects.remove(ob,do_unlink=True)
for side in [-1,1]:
    for k in range(5):
        delta=(k-2)*.0013;ps=bez([(side*(.080+delta),0,.020),(side*(.089+delta),0,-.037),(side*(.064+delta),0,-.105),(side*(.067+delta),0,-.162-k*.006)],62)
        vs=[];fs=[];uv=[];strandpts=[]
        for i,c in enumerate(ps):
            t=i/61
            if c.z>-.107:y=front_surface(c.x,c.z)-.0013
            else:
                blend=min(1,(-c.z-.107)/.045);y=front_surface(c.x,-.107)*(1-blend)+(-.073+.006*sin(t*9+side))*blend-.0013
            c.y=y;c.x+=side*.0016*sin(t*10+k*.2)*t*t
            tangent=(ps[min(61,i+1)]-ps[max(0,i-1)]).normalized();axis=Vector((1,0,0));axis=(axis-tangent*axis.dot(tangent)).normalized()
            w=(.0008+.0002*k)*(1-t)**.65*sin(pi*min(.999,t*1.2+.01))**.25
            for j,u in enumerate(np.linspace(-1,1,5)):
                q=c+axis*float(u)*w;q.y-=.0003*(1-u*u);vs.append(q);uv.append((.3+k*.07+float(u)*.003,t))
            strandpts.append(c)
        for i in range(61):
            for j in range(4):idx=i*5+j;fs.append((idx,idx+5,idx+6,idx+1))
        mesh("Groom - soft framing curl "+str(side)+" "+str(k),vs,fs,lockmat,parent=head,uv=uv)
    # A dozen overlapping locks break the large ponytail volume into naturally varied tips.
    for k in range(12):
        a=2*pi*k/12+.16*side;end=.94+.085*random.random();vs=[];fs=[];uv=[];nt=52;width=random.uniform(.0036,.0060)
        for i in range(nt):
            t=i/(nt-1);tt=.05+(end-.05)*t;angle=a+.09*sin(t*8+side+k)
            c=pony_point(side,tt,angle,1.030+.018*sin(pi*t));c.z-=.014*t**4
            c.x+=.005*cos(a)*t**5;c.y+=.003*sin(a)*t**4
            before=pony_point(side,max(0,tt-.003),angle,1.03);after=pony_point(side,min(1.04,tt+.003),angle,1.03)
            tangent=(after-before).normalized();axis=Vector((-sin(angle),.77*cos(angle),0));axis=(axis-tangent*axis.dot(tangent)).normalized()
            w=width*sin(pi*min(.999,t+.008))**.6*(1-.4*t)
            for j,u in enumerate(np.linspace(-1,1,7)):
                q=c+axis*float(u)*w;vs.append(q);uv.append((k/12+float(u)*.014,t))
        for i in range(nt-1):
            for j in range(6):idx=i*7+j;fs.append((idx,idx+7,idx+8,idx+1))
        mesh("Groom - waved ponytail lock "+str(side)+" "+str(k),vs,fs,lockmat,parent=head,uv=uv)
# Sparse geometry retained in light mode supplies a soft silhouette without a huge fibre mesh.
for k in range(96):
    th=random.uniform(-pi,pi);start=random.uniform(.05,.50);end=min(1.035,start+random.uniform(.22,.55));pts=[]
    for i,t0 in enumerate(np.linspace(start,end,28)):
        t=float(t0);q=hairpoint(th+.26*(1-t),min(t,1.03),.0006+.0035*sin(pi*i/27)**1.5)
        q.x+=.0014*sin(t*19+k)*sin(pi*i/27);pts.append(q)
    line("Groom - fine silhouette flyaways",pts,flymat,.000065,head,[.18+.62*sin(pi*i/27)**.6 for i in range(28)])
print("LAYERED_SURFACE_GROOM_READY",flush=True)
