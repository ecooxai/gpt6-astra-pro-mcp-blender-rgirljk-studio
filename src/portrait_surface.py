"""Authored facial surface with exact eye and mouth boundary loops."""
from mathutils.geometry import delaunay_2d_cdt
EC=.0345; EW=.0195; EZ=.019; MW=.0335; BN=96
BASE=np.array([.54,.335,.255])
def skin_color(x,z):
    b=.11*(gauss(x,z,.048,-.029,.025,.023)+gauss(x,z,-.048,-.029,.025,.023))
    c=np.array([BASE[0]+b*.16,BASE[1]-b*.13,BASE[2]-b*.035])
    for es in [-1,1]:
        t=(x-es*EC)/.024
        if abs(t)<1:
            mid=.039+.005*(1-t*t)+.0012*es*t;w=.0028*max(.02,1-t*t)**.6
            a=.80*exp(-((z-mid)/w)**2)*max(0,1-t*t)**.35
            c=c*(1-a)+np.array([.045,.026,.020])*a
    return c
def center_y(z):
    return smooth_profile(z,[-.122,-.115,-.10,-.08,-.05,-.015],[-.035,-.020,-.016,-.009,0,.010]) if z<-.015 else .010
def face_y(x,z):
    w,d=shape(z);y=center_y(z)-d*sqrt(max(0,1-(x/max(w,.001))**2))
    y-=.018*gauss(x,z,0,-.023,.013,.013)+.008*gauss(x,z,0,.006,.010,.031)
    y-=.006*(gauss(x,z,.012,-.031,.006,.006)+gauss(x,z,-.012,-.031,.006,.006))
    y-=.007*(gauss(x,z,.048,-.021,.027,.027)+gauss(x,z,-.048,-.021,.027,.027))
    y+=.0065*(gauss(x,z,EC,.022,.022,.014)+gauss(x,z,-EC,.022,.022,.014))
    y-=.007*gauss(x,z,0,-.058,.033,.022)
    y-=.0035*gauss(x,z,0,-.099,.025,.015)
    for fx,fz in [(.021,-.029),(.027,-.036),(.032,-.044),(.035,-.051)]:
        y+=.00055*gauss(abs(x),z,fx,fz,.0038,.007)
    return y

def eye_xz(s,a,outer=False):
    u=cos(a);v=sin(a);h=abs(v)**1.18
    w=.0232 if outer else EW
    return s*EC+w*u,EZ+.0015*s*u+((.0130 if v>=0 else -.0105) if outer else (.0070 if v>=0 else -.0042))*h

def eye_y(s,x,z):
    return face_y(s*EC,EZ)+.007-.012*sqrt(max(.02,1-((x-s*EC)/.025)**2-((z-EZ)/.019)**2))

def mouth_xz(a,outer=False):
    u=cos(a);h=abs(sin(a))**1.25
    top=-.050-.004*u*u;bottom=-.069+.015*u*u
    x=MW*u;z=top if sin(a)>=0 else bottom
    if outer:
        x*=1.055;z+=(.0048 if sin(a)>=0 else -.0060)*h
    return x,z

def in_hole(x,z):
    for s in [-1,1]:
        u=(x-s*EC)/.0232
        if abs(u)<1:
            h=(1-u*u)**.59;mid=EZ+.0015*s*u
            if mid-.0105*h<z<mid+.0130*h:return True
    u=x/(MW*1.055)
    if abs(u)<1:
        h=(1-u*u)**.625
        if -.069+.015*u*u-.006*h<z<-.050-.004*u*u+.0048*h:return True
    return False

head.scale=(1.03,1.0,.96);head.location.z=1.540
skin.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(*BASE,1)
skin.node_tree.nodes.get("Principled BSDF").inputs["Subsurface Weight"].default_value=.12
P2=[];E2=[]
def uvfront(x,z):return Vector((.085*math.asin(max(-1,min(1,x/shape(z)[0]))),z))
def edge_loop(loop):
    start=len(P2);P2.extend(loop);E2.extend((start+i,start+(i+1)%len(loop)) for i in range(len(loop)))
zl=np.linspace(ZP[0],ZP[-1],181)
edge_loop([Vector((-.085*pi/2,float(z))) for z in zl]+[Vector((.085*pi/2,float(z))) for z in zl[::-1]])
for side in [-1,1]:edge_loop([uvfront(*eye_xz(side,2*pi*j/BN,True)) for j in range(BN)])
edge_loop([uvfront(*mouth_xz(2*pi*j/BN,True)) for j in range(BN)])
for z in zl[1:-1]:
    for th in np.linspace(-pi/2,pi/2,127)[1:-1]:
        x=shape(float(z))[0]*sin(float(th))
        if not in_hole(x,float(z)):P2.append(Vector((.085*float(th),float(z))))
cv,ce,cf,*_=delaunay_2d_cdt(P2,E2,[],0,1e-8,False)
V=[];F=[];cols=[]
for a,z in cv:
    z=float(z);x=shape(z)[0]*sin(float(a)/.085)
    V.append((x,face_y(x,z),z));cols.append((*skin_color(x,z),1))
for ids in cf:
    cx=sum(V[k][0] for k in ids)/len(ids);cz=sum(V[k][2] for k in ids)/len(ids)
    if not in_hole(cx,cz):F.append(tuple(ids))
# Complete back of head, joined at the same profile samples as the facial patch.
start=len(V);ns=96
for z in zl:
    z=float(z);w,d=shape(z)
    for th in np.linspace(pi/2,3*pi/2,ns+1):
        th=float(th);x=w*sin(th);b=-cos(th)
        y=center_y(z)+d*b+.010*b*exp(-((z-.025)/.095)**2)
        y+=(face_y(math.copysign(w,x),z)-center_y(z))*abs(sin(th))**12
        V.append((x,y,z));cols.append((*skin_color(x,z),1))
for i in range(len(zl)-1):
    for j in range(ns):
        k=start+i*(ns+1)+j;F.append((k,k+1,k+ns+2,k+ns+1))
# Eyelids and lips are part of the same mesh, not floating overlays.
for kind in [-1,1,0]:
    start=len(V);nr=12
    for i in range(nr):
        v=i/(nr-1)
        for j in range(BN):
            a=2*pi*j/BN
            if kind:
                xi,zi=eye_xz(kind,a);xo,zo=eye_xz(kind,a,True)
                x=xi*(1-v)+xo*v;z=zi*(1-v)+zo*v
                yi=eye_y(kind,xi,zi)-.00015
                y=yi*(1-v)+face_y(xo,zo)*v-.00055*sin(pi*v)*abs(sin(a))
                color=skin_color(x,z)
            else:
                xi,zi=mouth_xz(a);xo,zo=mouth_xz(a,True)
                x=xi*(1-v)+xo*v;z=zi*(1-v)+zo*v
                y=face_y(x,z)-.0010*(1-v)-.0025*sin(pi*v)*abs(sin(a))
                fade=v*v*(3-2*v);color=np.array([.37,.082,.099])*(1-fade)+skin_color(x,z)*fade
            V.append((x,y,z));cols.append((*color,1))
    for i in range(nr-1):
        for j in range(BN):
            k=start+i*BN+j;q=start+i*BN+(j+1)%BN
            F.append((k,k+BN,q+BN,q))
headskin=skin.copy();headskin.name="Face - continuous blended skin and lips"
nt=headskin.node_tree;vc=nt.nodes.new("ShaderNodeVertexColor");vc.layer_name="Col"
nt.links.new(vc.outputs["Color"],nt.nodes.get("Principled BSDF").inputs["Base Color"])
hm=mesh("Face - unified sculpted skin with exact eyelids and lips",V,F,headskin,parent=head)
ca=hm.data.color_attributes.new(name="Col",type="FLOAT_COLOR",domain="POINT")
ca.data.foreach_set("color",np.array(cols,dtype=np.float32).ravel())
import bmesh
bm=bmesh.new();bm.from_mesh(hm.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(hm.data);bm.free()
for poly in hm.data.polygons:poly.use_smooth=True
hm.data.update();NZ=181;NT=320
print("CONTINUOUS_FACE_BUILT",len(hm.data.vertices),len(hm.data.polygons),flush=True)
