"""Authored facial surface with exact eye and mouth boundary loops."""
from mathutils.geometry import delaunay_2d_cdt
EC=.0345; EW=.0195; EZ=.019; MW=.0335; BN=96
BASE=np.array([.54,.335,.255])
# Rounded chin cap and fuller smiling jaw, smoothly joined to the authored profile.
WP[1:7]=[.029,.046,.064,.079,.087,.088]
_base_shape=shape
def shape(z):
    w,d=_base_shape(z)
    if z<-.096:
        capw=.0515*sqrt(max(0,1-((z+.082)/.040)**2))
        capd=.0554*sqrt(max(0,1-((z+.075)/.047)**2))
        t=max(0,min(1,(z+.111)/.015));t=t*t*(3-2*t)
        w=capw*(1-t)+w*t;d=capd*(1-t)+d*t
    return max(.0005,w),max(.0005,d)
def skin_color(x,z):
    b=.18*(gauss(x,z,.048,-.029,.025,.023)+gauss(x,z,-.048,-.029,.025,.023))
    c=np.array([BASE[0]+b*.16,BASE[1]-b*.13,BASE[2]-b*.035])
    for es in [-1,1]:
        t=(x-es*EC)/.024
        if abs(t)<1:
            mid=.039+.005*(1-t*t)+.0012*es*t;w=.0028*max(.02,1-t*t)**.6
            a=.94*exp(-((z-mid)/w)**2)*max(0,1-t*t)**.35
            c=c*(1-a)+np.array([.014,.008,.006])*a
    return c
def center_y(z):
    return smooth_profile(z,[-.122,-.115,-.10,-.08,-.05,-.015,.010],[-.035,-.020,-.016,-.009,0,.010,.010]) if z<.010 else .010
def face_y(x,z):
    w,d=shape(z);y=center_y(z)-d*sqrt(max(0,1-(x/max(w,.001))**2))
    y-=.021*gauss(x,z,0,-.023,.013,.013)+.008*gauss(x,z,0,.006,.010,.031)
    y-=.007*(gauss(x,z,.013,-.030,.007,.007)+gauss(x,z,-.013,-.030,.007,.007))
    y+=.0013*(gauss(x,z,.019,-.026,.003,.007)+gauss(x,z,-.019,-.026,.003,.007))
    y-=.0028*(gauss(x,z,.040,-.035,.019,.018)+gauss(x,z,-.040,-.035,.019,.018))
    y-=.007*(gauss(x,z,.048,-.021,.027,.027)+gauss(x,z,-.048,-.021,.027,.027))
    y+=.0065*(gauss(x,z,EC,.022,.022,.014)+gauss(x,z,-EC,.022,.022,.014))
    y-=.007*gauss(x,z,0,-.058,.033,.022)
    y-=.0035*gauss(x,z,0,-.099,.025,.015)
    for fx,fz in [(.021,-.029),(.027,-.036),(.032,-.044),(.035,-.051)]:
        y+=.00105*gauss(abs(x),z,fx,fz,.0038,.007)
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

def nostril_xz(side,a,outer=False):
    rx=.0044 if outer else .0024;rz=.0026 if outer else .0010
    x=side*.0115+rx*cos(a);z=-.033+rz*sin(a)-side*.18*(x-side*.0115)
    return x,z

def in_hole(x,z):
    for side in [-1,1]:
        u=(x-side*.0115)/.0044;v=(z+.033+side*.18*(x-side*.0115))/.0026
        if u*u+v*v<1:return True
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

head.scale=(1.045,1.0,.93);head.location.z=1.540
skin.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(*BASE,1)
skin.node_tree.nodes.get("Principled BSDF").inputs["Subsurface Weight"].default_value=.12
P2=[];E2=[]
def uvfront(x,z):return Vector((.085*math.asin(max(-1,min(1,x/shape(z)[0]))),z))
def edge_loop(loop):
    start=len(P2);P2.extend(loop);E2.extend((start+i,start+(i+1)%len(loop)) for i in range(len(loop)))
zl=np.unique(np.concatenate([np.linspace(ZP[0],ZP[-1],181),np.linspace(ZP[0],-.110,40)]))
edge_loop([Vector((-.085*pi/2,float(z))) for z in zl]+[Vector((.085*pi/2,float(z))) for z in zl[::-1]])
for side in [-1,1]:edge_loop([uvfront(*eye_xz(side,2*pi*j/BN,True)) for j in range(BN)])
edge_loop([uvfront(*mouth_xz(2*pi*j/BN,True)) for j in range(BN)])
for side in [-1,1]:edge_loop([uvfront(*nostril_xz(side,2*pi*j/BN,True)) for j in range(BN)])
# Locally denser eyebrow sampling keeps the pigment shape feathered, not blurry.
for side in [-1,1]:
    for t in np.linspace(-.99,.99,65):
        x=side*EC+.024*t;mid=.039+.005*(1-t*t)+.0012*side*t;th=.0028*max(.02,1-t*t)**.6
        for v in np.linspace(-1.7,1.7,11):
            z=mid+float(v)*th
            if not in_hole(x,z):P2.append(uvfront(x,z))
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
for kind in [-1,1,0,-2,2]:
    start=len(V);nr=12
    for i in range(nr):
        v=i/(nr-1)
        for j in range(BN):
            a=2*pi*j/BN
            if abs(kind)==1:
                xi,zi=eye_xz(kind,a);xo,zo=eye_xz(kind,a,True)
                x=xi*(1-v)+xo*v;z=zi*(1-v)+zo*v
                yi=eye_y(kind,xi,zi)-.00015
                yo=face_y(xo,zo);dx=xo-xi;dz=zo-zi;ep=.015
                m0=(eye_y(kind,xi+ep*dx,zi+ep*dz)-eye_y(kind,xi-ep*dx,zi-ep*dz))/(2*ep)
                m1=(face_y(xo+ep*dx,zo+ep*dz)-face_y(xo-ep*dx,zo-ep*dz))/(2*ep)
                y=(2*v**3-3*v*v+1)*yi+(v**3-2*v*v+v)*m0+(-2*v**3+3*v*v)*yo+(v**3-v*v)*m1
                y-=.00030*sin(pi*v)**2*abs(sin(a));color=skin_color(x,z)
            elif abs(kind)==2:
                side=kind//2;xi,zi=nostril_xz(side,a);xo,zo=nostril_xz(side,a,True)
                x=xi*(1-v)+xo*v;z=zi*(1-v)+zo*v
                y=face_y(x,z)-.0006*(1-v)**2-.0012*v*(1-v)**2
                color=skin_color(x,z)*(1-.055*(1-v))
            else:
                xi,zi=mouth_xz(a);xo,zo=mouth_xz(a,True)
                x=xi*(1-v)+xo*v;z=zi*(1-v)+zo*v
                y=face_y(x,z)-abs(sin(a))*(.0010*(1-v)**2+.009*v*(1-v)**2)
                fade=v*v*(3-2*v);color=np.array([.41,.105,.125])*(1-fade)+skin_color(x,z)*fade
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
