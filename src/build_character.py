"""Original procedural character. No source photographs or external model assets are loaded.
Run using Blender 4.2+: blender -b -t 8 --python src/build_character.py -- --revision 1
Coordinates: X left/right, -Y forward, Z up; dimensions in metres.
"""
import bpy, math, random, os, sys, json, argparse
import numpy as np
from mathutils import Vector
from math import sin,cos,pi,sqrt,exp
from pathlib import Path
random.seed(731)
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'preview'; BUILD=ROOT/'build'
a=argparse.ArgumentParser();a.add_argument('--revision',type=int,default=1);a.add_argument('--samples',type=int,default=32);a.add_argument('--views',default='front,face');a.add_argument('--size',type=int,default=900);a.add_argument('--no-export',action='store_true');args=a.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT.mkdir(exist_ok=True);BUILD.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
CHAR=bpy.data.collections.new('CHARACTER • Original procedural geometry');bpy.context.scene.collection.children.link(CHAR)
STUDIO=bpy.data.collections.new('STUDIO • Presentation only');bpy.context.scene.collection.children.link(STUDIO)

def move_col(o,col=CHAR):
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);return o

def material(name,color,rough=.45,metal=0,sss=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if sss:p.inputs['Subsurface Weight'].default_value=sss;p.inputs['Subsurface Radius'].default_value=(1,.42,.25);p.inputs['Subsurface Scale'].default_value=.08
    return m
skin=material('Skin • warm porcelain',(.61,.367,.263),.47,sss=.065)
lips=material('Lips • soft rose',(.46,.177,.15),.39,sss=.035)
crease=material('Soft warm skin creases',(.33,.155,.108),.63)
oral=material('Mouth interior',(.055,.011,.016),.68)
teeth=material('Teeth • natural ivory',(.84,.80,.67),.29)
white=material('Shirt • soft cotton',(.77,.80,.86),.82)
seamwhite=material('Shirt seams',(.58,.63,.72),.89)
navy=material('Backpack • navy woven fabric',(.026,.043,.078),.84)
webbing=material('Strap webbing',(.012,.015,.021),.88)
buckle=material('Buckles • charcoal polymer',(.018,.022,.027),.33)
sole=material('Loafer soles • rubber',(.012,.013,.016),.52)
leather=material('Loafers • black polished leather',(.009,.010,.014),.29)
stitch=material('Leather stitching',(.072,.075,.086),.47)
sock=material('Socks • ribbed midnight cotton',(.022,.030,.051),.85)
sclera=material('Eyes • warm whites',(.80,.80,.74),.26)
irismat=material('Iris • deep brown',(.072,.030,.013),.29)
irislight=material('Iris • amber fibres',(.145,.070,.023),.36)
pupilmat=material('Pupil and limbal ring',(.005,.004,.004),.21)
highlight=material('Eye highlights',(.95,.97,1),.10)
hairmats=[material('Hair • espresso '+str(i),(.009+i*.0022,.006+i*.0015,.005+i*.0013),.47+i*.016) for i in range(6)]
browmat=material('Eyebrows and lashes',(.027,.016,.011),.74)
for m in hairmats:
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Anisotropic'].default_value=.34

def mesh(name,verts,faces,mat,smooth=True,parent=None,uv=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);CHAR.objects.link(o)
    if mat:me.materials.append(mat)
    for p in me.polygons:p.use_smooth=smooth
    if uv:
        lay=me.uv_layers.new(name='OriginalUV')
        for p in me.polygons:
            for li in p.loop_indices:lay.data[li].uv=uv[me.loops[li].vertex_index]
    if parent:o.parent=parent
    return o

def uvball(name,loc,scale,mat,parent=None,seg=40,rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;move_col(o);o.data.materials.append(mat)
    for f in o.data.polygons:f.use_smooth=True
    if parent:o.parent=parent
    return o

def box(name,loc,scale,mat,r=.006,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);move_col(o);o.data.materials.append(mat)
    if r:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=r;mod.segments=3
        mod=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    if parent:o.parent=parent
    return o

CURVES={}
def line(name,points,mat,radius=.0006,parent=None,radii=None):
    key=(mat.name,round(radius,7),parent.name if parent else '',name.split('•')[0])
    if key not in CURVES:
        cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=radius;cu.bevel_resolution=0 if radius<.0005 else 2;cu.resolution_u=1
        ob=bpy.data.objects.new(name,cu);CHAR.objects.link(ob);cu.materials.append(mat)
        if parent:ob.parent=parent
        CURVES[key]=cu
    cu=CURVES[key];sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for i,p in enumerate(points):sp.points[i].co=(*p,1);sp.points[i].radius=radii[i] if radii is not None else 1

def bez(pts,n=40):
    p=[Vector(v) for v in pts];return [(1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3] for t in map(float,np.linspace(0,1,n))]

def catmull(pts,n=60):
    ps=[Vector(pts[0])]+[Vector(x) for x in pts]+[Vector(pts[-1])];out=[]
    for t in map(float,np.linspace(0,len(pts)-1,n)):
        i=min(int(t),len(pts)-2);u=t-i;p0,p1,p2,p3=ps[i:i+4]
        out.append(.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u**3))
    return out

def tube(name,pts,rads,mat,n=56,sides=40,ratio=1,ribs=0,parent=None):
    cs=catmull(pts,n);rs=np.interp(np.linspace(0,1,n),np.linspace(0,1,len(rads)),rads);verts=[];faces=[]
    for i,c in enumerate(cs):
        tang=(cs[min(i+1,n-1)]-cs[max(0,i-1)]).normalized();axis=Vector((1,0,0));axis=(axis-tang*axis.dot(tang)).normalized();other=tang.cross(axis)
        for j in range(sides):
            th=2*pi*j/sides;rr=rs[i]*(1+ribs*cos(th*48));verts.append(c+axis*(rr*cos(th))+other*(rr*ratio*sin(th)))
    for i in range(n-1):
        for j in range(sides):k=i*sides+j;q=i*sides+(j+1)%sides;faces.append((k,q,q+sides,k+sides))
    faces.append(tuple(range(sides-1,-1,-1)));faces.append(tuple((n-1)*sides+j for j in range(sides)))
    return mesh(name,verts,faces,mat,parent=parent)

def fabric(name,kind):
    N=512;yy,xx=np.mgrid[0:N,0:N];u=xx/N;v=yy/N
    if kind=='plaid':
        col=np.zeros((N,N,4),dtype=np.float32);col[:,:,:3]=(.105,.125,.172)
        band=lambda x,c,w: np.clip(1-(np.abs((x-c+.5)%1-.5)-w)*180,0,1)
        broad=np.maximum(band(u,.23,.073),band(v,.22,.075));thin=np.maximum(band(u,.73,.012),band(v,.71,.012));hair=np.maximum(band(u,.09,.004),band(v,.065,.004))
        col[:,:,:3]+=broad[:,:,None]*np.array([.118,.132,.153]);col[:,:,:3]+=thin[:,:,None]*np.array([.088,.10,.115]);col[:,:,:3]+=hair[:,:,None]*np.array([.055,.06,.07])
        dark=np.maximum(band(u,.23,.014),band(v,.22,.015));col[:,:,:3]-=dark[:,:,None]*np.array([.063,.067,.077])
        weave=(np.sin(xx*pi)*.002+((xx+yy)%3-1)*.005);col[:,:,:3]+=weave[:,:,None]
    else:
        col=np.zeros((N,N,4),dtype=np.float32);col[:,:,:3]=(.095,.128,.205)
        g=((v+u*.18)% .225);gold=(g<.011);col[gold,:3]=(.85,.63,.30)
        small=((v+u*.18+.08)%.225)<.0018;col[small,:3]=(.20,.23,.31)
        col[:,:,:3]+=(((xx+yy)%4-1.5)*.003)[:,:,None]
    col[:,:,3]=1;im=bpy.data.images.new(name,width=N,height=N,alpha=True);im.pixels.foreach_set(col.ravel());im.pack();im.filepath_raw=str(BUILD/(name+'.png'));im.file_format='PNG';im.save()
    m=material(name,(.3,.3,.3),.8);nd=m.node_tree.nodes.new('ShaderNodeTexImage');nd.image=im;nd.extension='REPEAT';m.node_tree.links.new(nd.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);return m
plaid=fabric('Original mathematical tartan','plaid');tiemat=fabric('Original diagonal gold tie weave','tie')

# Head: anatomical cross-section loft with integrated nose, cheeks and eye sockets.
head=bpy.data.objects.new('HEAD • six-degree natural tilt',None);CHAR.objects.link(head);head.location=(.013,-.014,1.534);head.rotation_euler=(math.radians(-2),math.radians(6),math.radians(-2));head.scale=(.94,.94,.94)
ZP=[-.122,-.115,-.10,-.08,-.05,-.015,.02,.055,.085,.115,.14,.153]
WP=[.001,.022,.040,.059,.076,.084,.087,.086,.081,.068,.043,.001]
DP=[.003,.027,.047,.059,.066,.073,.078,.082,.087,.078,.048,.001]
def smooth_profile(x,xs,ys):
    i=max(0,min(len(xs)-2,int(np.searchsorted(xs,x)-1)));h=xs[i+1]-xs[i];t=max(0,min(1,(x-xs[i])/h))
    def slope(j):
        if j==0:return (ys[1]-ys[0])/(xs[1]-xs[0])
        if j==len(xs)-1:return (ys[-1]-ys[-2])/(xs[-1]-xs[-2])
        a=(ys[j]-ys[j-1])/(xs[j]-xs[j-1]);b=(ys[j+1]-ys[j])/(xs[j+1]-xs[j])
        return 0 if a*b<=0 else 2*a*b/(a+b)
    return (2*t**3-3*t*t+1)*ys[i]+(t**3-2*t*t+t)*h*slope(i)+(-2*t**3+3*t*t)*ys[i+1]+(t**3-t*t)*h*slope(i+1)
def shape(z):return smooth_profile(z,ZP,WP),smooth_profile(z,ZP,DP)
def gauss(x,z,cx,cz,wx,wz):return exp(-((x-cx)/wx)**2-((z-cz)/wz)**2)
def face_y(x,z):
    w,d=shape(z);co=sqrt(max(0,1-(x/max(w,.001))**2));y=.010-d*co
    y-=.030*gauss(x,z,0,-.023,.013,.012)+.014*gauss(x,z,0,.004,.009,.032)
    y-=.008*gauss(x,z,0,-.031,.027,.011)
    y-=.009*(gauss(x,z,.047,-.028,.026,.024)+gauss(x,z,-.047,-.028,.026,.024))
    y+=.010*(gauss(x,z,.032,.018,.024,.013)+gauss(x,z,-.032,.018,.024,.013))
    y-=.006*gauss(x,z,0,-.056,.036,.023)
    return y
V=[];F=[];cols=[];NZ=148;NT=224
for i,z in enumerate(np.linspace(ZP[0],ZP[-1],NZ)):
    w,d=shape(z)
    for j in range(NT):
        th=2*pi*j/NT;x=w*sin(th);front=cos(th);y=.010-d*front
        if front>0:y+=(face_y(x,z)-(.010-d*max(front,0)))*front**.65
        else:y+=.012*(-front)*exp(-((z-.025)/.095)**2)
        V.append((x,y,z));bl=.20*(gauss(x,z,.052,-.031,.023,.024)+gauss(x,z,-.052,-.031,.023,.024))*max(front,0);cols.append((.61+bl*.22,.367-bl*.18,.263-bl*.07,1))
for i in range(NZ-1):
    for j in range(NT):
        ids=(i*NT+j,i*NT+(j+1)%NT,(i+1)*NT+(j+1)%NT,(i+1)*NT+j);cx=sum(V[k][0] for k in ids)/4;cz=sum(V[k][2] for k in ids)/4;cy=sum(V[k][1] for k in ids)/4;u=cx/.0305
        hole=abs(u)<1 and -.069+.026*u*u<cz<-.049+.006*u*u and cy<-.025
        if not hole:F.append(ids)
headskin=skin.copy();headskin.name='Face skin • original vertex blush';cn=headskin.node_tree.nodes.new('ShaderNodeVertexColor');cn.layer_name='Col';headskin.node_tree.links.new(cn.outputs['Color'],headskin.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
hm=mesh('Face • sculpted continuous anatomical surface',V,F,headskin,parent=head);ca=hm.data.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT');ca.data.foreach_set('color',np.array(cols,dtype=np.float32).ravel())
# neck and covered upper chest
neck=tube('Neck and upper chest',[(-.002,.014,1.304),(.005,.011,1.363),(.012,.010,1.440)],[.057,.042,.046],skin,n=32,sides=56,ratio=.89)
for side in [-1,1]:
    uvball('Ear • '+str(side),(side*.086,.010,-.013),(.017,.011,.031),skin,head)
    uvball('Ear concha • '+str(side),(side*.092,-.000,-.013),(.008,.003,.016),crease,head,24,16)
    ep=[(side*(.088+.012*sin(t)),-.002-.002*sin(t),-.011+.026*cos(t)) for t in np.linspace(-.2,pi*1.7,48)]
    line('Ear helix',ep,skin,.0027,head)
    # Almond whites precisely fitted to the face, rather than exposed sphere eyes.
    cx=side*.032;cz=.019;w=.0215;verts=[];faces=[]
    def eyey(x,z):return face_y(x,z)-.0016-.0032*exp(-((x-cx)/.022)**2-((z-cz)/.012)**2)
    for i,t in enumerate(np.linspace(-1,1,49)):
        x=cx+w*t;lift=.0017*side*t;h=max(0,1-t*t)**.62
        for j,v in enumerate(np.linspace(-1,1,13)):
            z=cz+lift+v*(.0073 if v>0 else .0055)*h;verts.append((x,eyey(x,z),z))
    for i in range(48):
        for j in range(12):k=i*13+j;faces.append((k,k+13,k+14,k+1))
    mesh('Eye white • '+str(side),verts,faces,sclera,parent=head)
    # Iris disks follow the curvature of the eye, with a fine dark limbal ring.
    for radius,mat,offset in [(.0086,pupilmat,.00025),(.0080,irismat,.00038),(.0035,pupilmat,.00058)]:
        vs=[(cx,eyey(cx,cz)-offset,cz)]
        for t in np.linspace(0,2*pi,65)[:-1]:
            xx=cx+radius*cos(t);zz=cz+radius*sin(t);u=(xx-cx)/w;h=max(0,1-u*u)**.62;zz=max(cz+.0017*side*u-.0055*h+.00015,min(cz+.0017*side*u+.0073*h-.00015,zz));vs.append((xx,eyey(xx,zz)-offset,zz))
        mesh('Iris or pupil • '+str(side),vs,[(0,j+1,(j+1)%64+1) for j in range(64)],mat,parent=head)
    for k in range(33):
        th=2*pi*k/33;pts=[]
        for rr in np.linspace(.0037,.0071,5):
            x=cx+rr*cos(th);z=cz+rr*sin(th);u=(x-cx)/w;h=max(0,1-u*u)**.62;z=max(cz+.0017*side*u-.0055*h+.0002,min(cz+.0017*side*u+.0073*h-.0002,z));pts.append((x,eyey(x,z)-.00051,z))
        line('Iris fibres',pts,irislight,.00009,head)
    uvball('Eye catchlight',(cx-.0018,eyey(cx-.0018,cz+.0024)-.0008,cz+.0024),(.0011,.00045,.0011),highlight,head,20,12)
    uvball('Eye secondary glint',(cx+.0016,eyey(cx+.0016,cz-.0017)-.0007,cz-.0017),(.00042,.0003,.00042),highlight,head,16,8)
    for upper in [True,False]:
        pts=[];lash=[];rads=[]
        for t in np.linspace(-1,1,50):
            x=cx+w*t;z=cz+.0017*side*t+(.0073 if upper else -.0055)*max(0,1-t*t)**.62;pts.append((x,eyey(x,z)-.0007,z));rads.append(.25+.75*max(0,1-t*t)**.4)
        line('Upper eyelid' if upper else 'Lower eyelid',pts,skin,.0011 if upper else .00065,head,rads)
        if upper:
            line('Upper lashes',[(x,y-.0015,z-.00010) for x,y,z in pts],browmat,.00055,head,rads)
            cp=[(x,face_y(x,z+.005)-.0005,z+.005) for x,y,z in pts[5:-5]];line('Upper lid crease',cp,crease,.00032,head)
    pts=[]
    for t in np.linspace(-1,1,34):
        x=cx+.024*t;z=.039+.0052*(1-t*t)+.002*side*t;pts.append((x,face_y(x,z)-.0012,z))
    line('Eyebrows',pts,browmat,.00165,head,[.15+.85*(sin(pi*i/33)**.65) for i in range(34)])
    for k in range(23):
        t=-.9+1.8*k/22;x=cx+.024*t;z=.039+.0052*(1-t*t)+.002*side*t
        line('Brow hairs',[(x,face_y(x,z)-.0025,z-.001),(x+.0012*side,face_y(x,z+.002)-.0025,z+.002)],hairmats[2],.0002,head)
    # Small nostril creases placed on the integrated nasal alae.
    pts=[]
    for t in np.linspace(0,pi,18):
        x=side*(.010+.0038*cos(t));z=-.035+.0014*sin(t);pts.append((x,face_y(x,z)-.0008,z))
    line('Nostril crease',pts,crease,.0007,head)
# Smiling oral cavity, upper and lower lip contours and individual teeth.
verts=[];faces=[]
for i,u in enumerate(np.linspace(-1,1,65)):
    x=.0312*u;top=-.049+.006*u*u;bottom=-.069+.026*u*u
    for j,t in enumerate(np.linspace(0,1,9)):
        z=bottom*(1-t)+top*t;verts.append((x,face_y(x,z)+.003,z))
for i in range(64):
    for j in range(8):k=i*9+j;faces.append((k,k+9,k+10,k+1))
mesh('Smile • dark inner mouth',verts,faces,oral,parent=head)
for upper in [True,False]:
    pts=[]
    for u in np.linspace(-1,1,70):
        x=.032*u;z=(-.049+.006*u*u) if upper else (-.069+.026*u*u)
        if upper:z+=.001*exp(-(u/.2)**2)
        pts.append((x,face_y(x,z)-.0015,z))
    line('Upper rose lip' if upper else 'Lower rose lip',pts,lips,.0017 if upper else .0025,head,[.23+.77*sin(pi*i/69)**.5 for i in range(70)])
for i in range(8):
    x=(i-3.5)*.0067;u=x/.032;top=-.049+.006*u*u;z=top-.0044
    o=box('Upper tooth '+str(i),(x,face_y(x,z)+.0001,z),(.0063,.006,.0073),teeth,.0017,head);o.rotation_euler.z=-x*3
for i in range(6):
    x=(i-2.5)*.0064;u=x/.032;z=-.066+.02*u*u
    box('Lower tooth '+str(i),(x,face_y(x,z)+.0013,z),(.006,.004,.0033),teeth,.0013,head)
# Hair cap and directional fibres. Every visible strand is original geometry.
V=[];F=[];nr=44;ns=120
for i,t in enumerate(np.linspace(.015,1,nr)):
    for j in range(ns):
        th=2*pi*j/ns;back=(1-cos(th))/2;pol=t*(1.39+1.16*back);x=.105*sin(pol)*sin(th);y=.014-.112*sin(pol)*cos(th);z=.035+.134*cos(pol);V.append((x,y,z))
for i in range(nr-1):
    for j in range(ns):k=i*ns+j;q=i*ns+(j+1)%ns;F.append((k,q,q+ns,k+ns))
mesh('Hair • fitted scalp shell',V,F,hairmats[1],parent=head)
for k in range(360):
    th0=2*pi*k/360;pts=[]
    for t in np.linspace(.08,1,36):
        th=th0+.16*sin(t*pi);pol=t*(1.39+1.16*(1-cos(th))/2);bump=.0008+.00035*sin(t*24+k)
        pts.append(((.105+bump)*sin(pol)*sin(th),.014-(.112+bump)*sin(pol)*cos(th),.035+(.134+bump)*cos(pol)))
    line('Scalp fibres',pts,hairmats[random.randrange(6)],.00022,head,[.4+.6*sin(pi*i/35)**.2 for i in range(36)])

def lock(name,controls,width,mat,parent=head,strands=14):
    cs=bez(controls,44);verts=[];faces=[];ribbon=[]
    for i,c in enumerate(cs):
        t=i/(len(cs)-1);tang=(cs[min(i+1,43)]-cs[max(0,i-1)]).normalized();axis=Vector((1,0,0));axis=(axis-tang*axis.dot(tang)).normalized();w=width*(.47+.7*sin(pi*t*.84))*(1-t)**.36+.00025
        row=[]
        for j,u in enumerate(np.linspace(-1,1,9)):
            p=c+axis*(w*u);p.y-=.0038*(1-u*u)*sin(pi*(t*.85+.08));verts.append(p);row.append(p)
        ribbon.append((c,axis,w))
    for i in range(43):
        for j in range(8):k=i*9+j;faces.append((k,k+9,k+10,k+1))
    o=mesh(name,verts,faces,mat,parent=parent);sol=o.modifiers.new('Hair ribbon thickness','SOLIDIFY');sol.thickness=.0007
    for k in range(strands):
        u=-.94+1.88*k/max(1,strands-1);pts=[]
        for i,(c,axis,w) in enumerate(ribbon):
            t=i/43;p=c+axis*(w*u);p.y-=.0038*(1-u*u)*sin(pi*(t*.85+.08))+.0005;pts.append(p)
        line('Lock fibres',pts,hairmats[(k+2)%6],.00018,parent,[.5+.5*sin(pi*i/43) for i in range(44)])
    return o
for k in range(9):
    f=k/8;lock('Fringe • sweeping strand group '+str(k),[(.045+.024*f,-.043+.006*f,.135-.004*f),(.026+.02*f,-.089,.112-.011*f),(-.025+.030*f,-.102,.055-.012*f),(-.075+.045*f,-.064-.027*f,.009+.027*f)],.011+f*.003,hairmats[k%3],strands=12)
for k in range(4):
    f=k/3;lock('Fringe • parted temple '+str(k),[(.066+.009*f,-.032,.132),(.088+.006*f,-.065,.072),(.086+.006*f,-.061,.012),(.079+.003*f,-.039,-.055-.018*f)],.009,hairmats[k%3],strands=10)
for side in [-1,1]:
    controls=[(side*.083,.047,-.026),(side*.143,.06,-.101),(side*.126,-.020,-.215),(side*.094,-.048,-.270)]
    cs=bez(controls,60);tube('Ponytail • volume '+str(side),[tuple(cs[i]) for i in [0,15,35,59]],[.021,.026,.019,.002],hairmats[0],n=60,sides=48,ratio=.80,parent=head)
    for k in range(14):
        th=2*pi*k/14;offx=.029*cos(th);offy=.028*sin(th);ctrl=[]
        for i,p in enumerate(controls):ctrl.append((p[0]+offx*(.6 if i==0 else 1),p[1]+offy,p[2]+(.013*sin(k*2.1) if i==3 else 0)))
        lock('Ponytail • layered lock '+str(side)+' '+str(k),ctrl,.009+random.random()*.005,hairmats[k%4],strands=12)
    for k in range(45):
        th=random.uniform(0,2*pi);off=random.uniform(.025,.042);pts=[]
        for i,c in enumerate(cs):
            t=i/59;rr=off*(.5+.5*sin(pi*t))*(1-.55*t);pts.append(c+Vector((rr*cos(th+t*2),rr*.8*sin(th+t*2),0)))
        line('Ponytail wisps',pts,hairmats[k%6],.00020,head,[sin(pi*(i/59*.96+.02))**.45 for i in range(60)])
    uvball('Ponytail elastic',(side*.085,.046,-.030),(.031,.024,.009),webbing,head)
    for k in range(6):
        lock('Face-framing flyaway',[(side*(.079+k*.001),-.023,.014),(side*(.092+k*.001),-.052,-.056),(side*.060,-.064,-.104),(side*(.064+k*.002),-.070,-.157-k*.002)],.0011,hairmats[(k+1)%6],strands=1)
# Tailored blouse loft. Front opening is genuinely open over the chest mesh.
TP=[(1.054,.118,.078),(1.073,.128,.083),(1.115,.123,.079),(1.170,.132,.085),(1.229,.145,.091),(1.285,.154,.085),(1.325,.161,.068),(1.348,.129,.055),(1.375,.051,.044)]
V=[];F=[];rows=72;ns=128
for i,z in enumerate(np.linspace(TP[0][0],TP[-1][0],rows)):
    w=float(np.interp(z,[p[0] for p in TP],[p[1] for p in TP]));d=float(np.interp(z,[p[0] for p in TP],[p[2] for p in TP]));t=(z-1.054)/.321
    for j in range(ns):
        th=2*pi*j/ns;x=w*sin(th);front=cos(th);y=.005-d*front
        wrinkle=.0009*sin(th*11+t*24)+.0005*sin(th*19-t*33)+.0011*sin(th*9+t*51)*exp(-((t-.13)/.20)**2)
        pull=.0035*sin(th*6+t*15)*exp(-((t-.61)/.25)**2)
        y-=(wrinkle+pull)*front;zz=z+.002*sin(th*8)*exp(-((t-.07)/.12)**2);V.append((x,y,zz))
for i in range(rows-1):
    for j in range(ns):
        ids=(i*ns+j,i*ns+(j+1)%ns,(i+1)*ns+(j+1)%ns,(i+1)*ns+j);x=sum(V[k][0] for k in ids)/4;z=sum(V[k][2] for k in ids)/4;y=sum(V[k][1] for k in ids)/4
        if not (y<-.025 and z>1.301 and abs(x)<(z-1.301)*.72):F.append(ids)
shirt=mesh('Blouse • fitted woven cloth and natural folds',V,F,white);md=shirt.modifiers.new('Cotton thickness','SOLIDIFY');md.thickness=.0012
# Open spread collar, placket and small buttons.
for s in [-1,1]:
    pts=[(s*.037,-.044,1.391),(s*.064,-.040,1.367),(s*.080,-.070,1.314),(s*.050,-.100,1.331),(s*.023,-.080,1.346)]
    c=mesh('Collar • '+str(s),pts,[(0,1,4),(1,2,3,4)],white,False);mod=c.modifiers.new('Collar cotton thickness','SOLIDIFY');mod.thickness=.0023;mod=c.modifiers.new('Collar softened edge','BEVEL');mod.width=.0013;mod.segments=3
    line('Collar topstitch',[(x,y-.0012,z) for x,y,z in pts+[pts[0]]],seamwhite,.00033)
    # Shoulder seam across the sleeve cap.
    pp=[(s*(.127+.033*t),-.043+.092*t,1.343-.017*sin(pi*t)) for t in np.linspace(0,1,32)];line('Shoulder seams',pp,seamwhite,.00045)
# Button placket raised from the cotton, visible beside the loose tie.
pp=[(.003,-.080,1.296),(.003,-.093,1.225),(.005,-.088,1.15),(.004,-.083,1.06)]
line('Shirt placket edge',[(x-.007,y-.001,z) for x,y,z in catmull(pp,50)],seamwhite,.0004)
for z in [1.273,1.217,1.157,1.098]:uvball('Shirt button',(.007,-.094 if z>1.19 else -.087,z),(.0032,.0012,.0032),white,seg=20,rings=12)
# Sleeves, cuff rolls and the arms behind the back.
for s in [-1,1]:
    pts=[(s*.154,.005,1.327),(s*.183,.007,1.281),(s*.186,.023,1.202),(s*.168,.047,1.128),(s*.157,.058,1.088)]
    cs=catmull(pts,60);V=[];F=[];nr=60;nt=64
    for i,c in enumerate(cs):
        t=i/(nr-1);tang=(cs[min(i+1,nr-1)]-cs[max(0,i-1)]).normalized();axis=Vector((1,0,0));axis=(axis-tang*axis.dot(tang)).normalized();other=tang.cross(axis);r=float(np.interp(t,[0,.25,.65,1],[.046,.045,.036,.030]))
        for j in range(nt):
            th=2*pi*j/nt;fold=.0009*sin(th*7+t*21)+.0005*sin(th*12-t*37)+.0009*sin(t*61+th*4)*exp(-((t-.8)/.2)**2);rr=r+fold;V.append(c+axis*rr*cos(th)+other*rr*.88*sin(th))
    for i in range(nr-1):
        for j in range(nt):k=i*nt+j;q=i*nt+(j+1)%nt;F.append((k,q,q+nt,k+nt))
    mesh('Sleeve • rolled cotton '+str(s),V,F,white)
    tube('Rolled cuff • '+str(s),[tuple(cs[-12]),tuple(cs[-6]),tuple(cs[-1])],[.0355,.036,.0318],white,n=16,sides=64,ratio=.90)
    c=cs[-10];tang=(cs[-1]-cs[-12]).normalized();axis=Vector((1,0,0));axis=(axis-tang*axis.dot(tang)).normalized();other=tang.cross(axis)
    line('Cuff stitching',[c+axis*.036*cos(t)+other*.032*sin(t) for t in np.linspace(0,2*pi,65)],seamwhite,.00045)
    tube('Forearm • behind back '+str(s),[(s*.161,.053,1.116),(s*.151,.071,1.066),(s*.124,.095,1.006),(s*.090,.132,.989)],[.028,.027,.022,.018],skin,n=48,sides=40,ratio=.87)
    palm=uvball('Hand palm • '+str(s),(s*.083,.133,.985),(.023,.014,.034),skin);palm.rotation_euler.y=s*-.42
    for k in range(4):
        x=s*(.064+k*.011);z=.968-(.002 if k in [1,2] else 0);length=[.033,.041,.039,.030][k]
        tube('Finger '+str(s)+' '+str(k),[(x,.131,z),(x-s*.004,.132,z-length*.45),(x-s*.006,.126,z-length*.86),(x-s*.007,.118,z-length)],[.006,.0057,.0047,.0038],skin,n=18,sides=16)
        uvball('Fingernail '+str(s)+' '+str(k),(x-s*.006,.117,z-length+.004),(.0035,.0006,.0045),lips,seg=16,rings=10)
    tube('Thumb • '+str(s),[(s*.060,.136,.992),(s*.047,.126,.976),(s*.049,.114,.961)],[.009,.007,.0055],skin,n=22,sides=18)
# Tie cloth panels with original UV stripes, a loose knot and continuous neck loop.
def strip(name,centers,widths,mat,thick=.002,uvscale=1):
    cs=catmull(centers,50);V=[];F=[];UV=[]
    for i,c in enumerate(cs):
        t=i/49;w=float(np.interp(t,np.linspace(0,1,len(widths)),widths))
        for j,u in enumerate(np.linspace(-1,1,9)):
            p=c+Vector((u*w,-.002*(1-u*u),0));V.append(p);UV.append(((u+1)/2,t*uvscale))
    for i in range(49):
        for j in range(8):k=i*9+j;F.append((k,k+9,k+10,k+1))
    o=mesh(name,V,F,mat,uv=UV);mod=o.modifiers.new('Cloth thickness','SOLIDIFY');mod.thickness=thick;return o
for s in [-1,1]:strip('Tie • loose neck band '+str(s),[(s*.044,-.059,1.357),(s*.036,-.086,1.317),(s*.017,-.102,1.282)],[.007,.009,.013],tiemat,uvscale=.35)
strip('Tie • dimensional loose knot',[(-.006,-.108,1.287),(-.002,-.116,1.264),(.002,-.111,1.245)],[.025,.019,.010],tiemat,thick=.004,uvscale=.20)
strip('Tie • long striped blade',[(.002,-.111,1.255),(-.009,-.106,1.187),(-.014,-.102,1.10),(-.015,-.115,1.011),(-.011,-.130,.950)],[.012,.022,.025,.027,.029,.030,.031,.031,.0007],tiemat,uvscale=1.20)
for sgn in [-1,1]:
    strip('Folded neckline edge '+str(sgn),[(sgn*.052,-.046,1.376),(sgn*.030,-.077,1.344),(sgn*.012,-.081,1.318),(sgn*.002,-.079,1.300)],[.005,.005,.005,.006],white,thick=.0018)
# Pleated tartan skirt, with sharp folded radial profiles and rounded cloth edges.
V=[];F=[];UV=[];nr=40;nt=320
for i,t in enumerate(np.linspace(0,1,nr)):
    z=1.061-.320*t;wx=.118+.083*(t**.83);dy=.087+.063*(t**.86);amp=.0015+.011*t**.72
    for j in range(nt+1):
        th=pi+2*pi*j/nt;fold=.68*cos(20*th)+.32*cos(40*th);r=amp*fold;x=(wx+r)*sin(th);y=.012-(dy+r*.85)*cos(th);zz=z+.003*sin(th*3+.3)*t**2;V.append((x,y,zz));UV.append((j/nt*7.5,(1-t)*2.4))
for i in range(nr-1):
    for j in range(nt):k=i*(nt+1)+j;F.append((k,k+1,k+nt+2,k+nt+1))
sk=mesh('Skirt • twenty sculpted pleats, original tartan',V,F,plaid,uv=UV);md=sk.modifiers.new('Tailored skirt thickness','SOLIDIFY');md.thickness=.0018
line('Skirt hem piping',V[-(nt+1):],navy,.00075)
# Waistband is cloth, not an exposed skin gap.
V=[];F=[];UV=[]
for i,z in enumerate([1.046,1.071]):
    for j in range(129):
        th=2*pi*j/128;V.append((.12*sin(th),.012-.089*cos(th),z));UV.append((j/128*7.5,i*.17))
for j in range(128):F.append((j,j+1,j+130,j+129))
mesh('Skirt waistband',V,F,plaid,uv=UV)
# Navy backpack: a complete bag, not just front straps.
box('Backpack • main structured fabric body',(0,.143,1.216),(.225,.116,.275),navy,.038)
box('Backpack • back pocket',(0,.208,1.175),(.180,.030,.147),navy,.026)
box('Backpack • pocket label',(0,.226,1.205),(.031,.002,.017),webbing,.002)
for s in [-1,1]:
    line('Backpack piping',[(s*.080,.204,1.326),(s*.106,.209,1.291),(s*.106,.215,1.139),(s*.080,.216,1.089)],webbing,.0016)
    pp=bez([(s*.123,.136,1.315),(s*.166,.027,1.440),(s*.135,-.081,1.364),(s*.131,-.084,1.251)],48)
    strip('Backpack • padded shoulder strap '+str(s),[tuple(pp[i]) for i in [0,14,28,47]],[.016,.019,.017,.014],navy,thick=.006)
    strip('Backpack • webbing return '+str(s),[(s*.131,-.082,1.264),(s*.132,-.084,1.196),(s*.127,-.037,1.108),(s*.120,.084,1.074)],[.009,.009,.008,.008],webbing,thick=.003)
    for z in [1.250,1.221]:
        for dx in [-.012,.012]:box('Strap buckle side',(s*.132+dx,-.091,z),(.004,.007,.022),buckle,.0014)
        for dz in [-.010,.010,0]:box('Strap buckle crossbar',(s*.132,-.093,z+dz),(.026,.007,.0033),buckle,.0012)
    line('Strap stitching',[(x+s*.011,y-.003,z) for x,y,z in pp[12:]],stitch,.00042)
    box('Backpack side pocket',(s*.121,.148,1.15),(.029,.084,.082),navy,.012)
    line('Backpack zipper',[(s*.074,.226,z) for z in np.linspace(1.145,1.228,30)],stitch,.00065)
    box('Zipper pull',(s*.074,.232,1.22),(.006,.003,.013),buckle,.002)
line('Backpack top handle',bez([(-.037,.159,1.352),(-.035,.164,1.394),(.035,.164,1.394),(.037,.159,1.352)],40),webbing,.005)
# Subtle embroidered shirt mark, original stitched motif rather than a borrowed logo.
for k in range(4):line('Shirt embroidered mark',[(.075+k*.0014,-.087,1.254),(.079+k*.0014,-.088,1.262),(.077+k*.0014,-.087,1.266)],material('Embroidery blue '+str(k),(.26,.46,.67),.9),.0005)
# Legs: matched anatomical segment lengths, asymmetrically posed.
LEGS=[{'side':'L','hip':(-.065,.032,.945),'knee':(-.015,-.073,.510),'ankle':(-.085,-.020,.113)}, {'side':'R','hip':(.074,.047,.950),'knee':(.059,.035,.502),'ankle':(.020,.015,.095)}]
measurements={}
for d in LEGS:
    hip,knee,ankle=map(Vector,[d['hip'],d['knee'],d['ankle']]);s=d['side'];mid=hip.lerp(knee,.42);below=knee.lerp(ankle,.35)
    tube('Leg • thigh and knee anatomy '+s,[hip,mid,knee,knee.lerp(ankle,.22)],[.063,.060,.038,.031],skin,n=72,sides=72,ratio=.92)
    measurements[s]={'femur':(hip-knee).length,'tibia':(knee-ankle).length,'hip':list(hip),'knee':list(knee),'ankle':list(ankle)}
    top=knee.lerp(ankle,.15);calf=knee.lerp(ankle,.36);low=knee.lerp(ankle,.84);end=ankle+Vector((0,-.007,-.027))
    tube('Sock • fine ribs '+s,[top,calf,low,ankle,end],[.0376,.0435,.029,.0265,.025],sock,n=70,sides=144,ratio=.92,ribs=.011)
    cuffend=top.lerp(calf,.20);tube('Sock • ribbed top band '+s,[top,cuffend],[.0385,.0405],sock,n=8,sides=144,ratio=.92,ribs=.012)
# Leather loafers: separate sole, stitched vamp, raised penny strap and open collar.
for side,cx,cy,base,yaw in [('L',-.085,-.051,.014,-.13),('R',.020,-.013,.005,.10)]:
    shoe=bpy.data.objects.new('Loafer assembly '+side,None);CHAR.objects.link(shoe);shoe.location=(cx,cy,base);shoe.rotation_euler.z=yaw
    nt=96
    def outline(th):return Vector((.044*sin(th)*(1+.11*cos(th)),-.032-.102*cos(th),0))
    V=[];F=[]
    for z,scale in [(0,1.00),(.005,1.025),(.016,1.035),(.023,1.00)]:
        for j in range(nt):p=outline(2*pi*j/nt);V.append((p.x*scale,p.y*scale,z))
    for i in range(3):
        for j in range(nt):k=i*nt+j;q=i*nt+(j+1)%nt;F.append((k,q,q+nt,k+nt))
    F.append(tuple(range(nt-1,-1,-1)));F.append(tuple(3*nt+j for j in range(nt)))
    mesh('Loafer • rubber sole '+side,V,F,sole,parent=shoe)
    V=[];F=[];nr=20
    for i,t in enumerate(np.linspace(0,1,nr)):
        for j in range(nt):
            th=2*pi*j/nt;out=outline(th);inn=Vector((.024*sin(th),.034-.030*cos(th),0));p=out.lerp(inn,t);z=.024+sin(t*pi/2)*(.058-.014*cos(th));z+=.005*sin(pi*t)*max(cos(th),0);V.append((p.x,p.y,z))
    for i in range(nr-1):
        for j in range(nt):k=i*nt+j;q=i*nt+(j+1)%nt;F.append((k,q,q+nt,k+nt))
    mesh('Loafer • formed leather upper '+side,V,F,leather,parent=shoe)
    line('Loafer collar piping',V[-nt:]+[V[-nt]],leather,.0021,shoe)
    line('Loafer sole welt',[(outline(t).x*1.012,outline(t).y*1.012,.022) for t in np.linspace(0,2*pi,100)],stitch,.0007,shoe)
    pts=[]
    for th in np.linspace(-1.50,1.50,65):
        out=outline(th);inn=Vector((.024*sin(th),.034-.030*cos(th),0));p=out.lerp(inn,.33);z=.024+sin(.33*pi/2)*(.058-.014*cos(th))+.005*sin(pi*.33)*max(cos(th),0);pts.append((p.x,p.y,z+.001))
    line('Loafer apron stitching',pts,stitch,.0008,shoe)
    strap=box('Loafer • penny saddle strap '+side,(0,-.037,.071),(.080,.025,.005),leather,.004,shoe)
    # Curve the strap gently over the vamp by adding a central top layer.
    line('Penny strap raised seam',[(-.039,-.050,.067),(-.021,-.051,.072),(0,-.052,.073),(.021,-.051,.072),(.039,-.050,.067)],stitch,.0008,shoe)
    box('Penny strap slot '+side,(0,-.038,.074),(.020,.003,.0012),sole,.001,shoe)

# Geometry-only inspection metrics: never pixel-analysis of the supplied photograph.
metrics={'revision':args.revision,'leg_segments_metres':measurements,'original_assets_only':True,'photo_used_as_texture':False,'mesh_objects':sum(o.type=='MESH' for o in CHAR.objects),'curve_objects':sum(o.type=='CURVE' for o in CHAR.objects),'notes':'Both hidden sides and hands are authored; no pre-existing character meshes, texture scans or downloaded HDRIs.'}
(BUILD/f'geometry_metrics_r{args.revision:02d}.json').write_text(json.dumps(metrics,indent=2))
# Render stage: studio lights and environment are excluded from the GLB.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=args.samples;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.045;scene.cycles.max_bounces=7;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=4;scene.cycles.transparent_max_bounces=4
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.05
world=bpy.data.worlds.new('Studio atmosphere');scene.world=world;world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.38,.44,.56,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.27
floor=material('Studio floor',(.10,.125,.16),.83)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.004));ob=bpy.context.object;ob.name='STUDIO • seamless backdrop';move_col(ob,STUDIO);ob.data.materials.append(floor)
def area(name,loc,power,size,col,target=(0,0,1)):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=col;o=bpy.data.objects.new(name,data);STUDIO.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Key • large warm softbox',(-2.2,-3.1,4.2),320,3.0,(1,.89,.79))
area('Fill • cool softbox',(2.1,-2.0,2.2),135,2.7,(.78,.87,1))
area('Hair rim • long warm highlight',(.8,1.6,3.2),265,2.0,(1,.91,.78))
area('Face catchlight',(-.25,-2.1,1.8),18,.6,(1,.95,.88),target=(0,0,1.5))
camdata=bpy.data.cameras.new('Portrait camera');cam=bpy.data.objects.new('Portrait camera',camdata);STUDIO.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.lens=70
views={'front':((0,-5.3,2.02),(0,0,.867),1.875,(2,3)),'face':((.01,-4.2,1.65),(.02,-.015,1.525),.43,(1,1)),'threequarter':((3.4,-5.3,2.3),(0,0,.865),1.91,(2,3)),'back':((0,5.3,2.1),(0,0,.865),1.91,(2,3)),'side':((5.3,-.05,2.0),(0,0,.865),1.91,(2,3))}
def setview(name):
    pos,target,scale,aspect=views[name];cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale;scene.render.resolution_y=args.size;scene.render.resolution_x=round(args.size*aspect[0]/aspect[1])
setview('front')
base='gpt6_astra_pro_mcp_blender_rgirljk'
if not args.no_export:
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(base+'.blend')))
    # Convert curve duplicates for glTF while preserving editable curves in the .blend.
    bpy.ops.object.select_all(action='DESELECT')
    for o in CHAR.objects:
        if o.type=='CURVE':o.select_set(True)
    if bpy.context.selected_objects:bpy.context.view_layer.objects.active=bpy.context.selected_objects[0];bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    for o in CHAR.objects:o.select_set(True)
    bpy.context.view_layer.objects.active=hm
    bpy.ops.export_scene.gltf(filepath=str(OUT/(base+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
    print('EXPORT_COMPLETE',str(OUT/(base+'.glb')),flush=True)
for name in args.views.split(','):
    if name not in views:continue
    setview(name);scene.render.filepath=str(OUT/f'{name}_r{args.revision:02d}.png');print('RENDER_BEGIN',name,flush=True);bpy.ops.render.render(write_still=True);print('RENDER_COMPLETE',name,flush=True)
print('BUILD_COMPLETE',args.revision,flush=True)
