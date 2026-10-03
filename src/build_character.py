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
    if sss:p.inputs['Subsurface Weight'].default_value=sss;p.inputs['Subsurface Radius'].default_value=(1,.42,.25);p.inputs['Subsurface Scale'].default_value=.0016
    return m
skin=material('Skin • warm porcelain',(.62,.40,.315),.43,sss=.18)
lips=material('Lips • soft rose',(.46,.177,.15),.39,sss=.035)
earinner=material('Ear inner skin',(.55,.27,.225),.55,sss=.12)
crease=material('Soft warm skin creases',(.33,.155,.108),.63)
oral=material('Mouth interior',(.055,.011,.016),.68)
teeth=material('Teeth • natural ivory',(.84,.80,.67),.29)
white=material('Shirt • soft cotton',(.77,.80,.86),.82)
seamwhite=material('Shirt seams',(.58,.63,.72),.89)
navy=material('Backpack • navy woven fabric',(.011,.020,.043),.90)
webbing=material('Strap webbing',(.012,.015,.021),.88)
buckle=material('Buckles • charcoal polymer',(.018,.022,.027),.33)
sole=material('Loafer soles • rubber',(.012,.013,.016),.52)
leather=material('Loafers • black polished leather',(.009,.010,.014),.29)
stitch=material('Leather stitching',(.072,.075,.086),.47)
sock=material('Socks • ribbed midnight cotton',(.022,.030,.051),.85)
sclera=material('Eyes • warm whites',(.42,.43,.41),.30)
irismat=material('Iris • deep brown',(.009,.006,.004),.26)
irislight=material('Iris • amber fibres',(.041,.021,.009),.32)
pupilmat=material('Pupil and limbal ring',(.0015,.0012,.0010),.21)
highlight=material('Eye highlights',(.95,.97,1),.10)
hairmats=[material('Hair • espresso '+str(i),(.009+i*.0022,.006+i*.0015,.005+i*.0013),.47+i*.016) for i in range(6)]
browmat=material('Eyebrows and lashes',(.027,.016,.011),.74)
for eye_mat in [pupilmat,irismat,irislight]:
    ep=eye_mat.node_tree.nodes.get('Principled BSDF');ep.inputs['Specular IOR Level'].default_value=.055;ep.inputs['Roughness'].default_value=.42
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
        col=np.zeros((N,N,4),dtype=np.float32);col[:,:,:3]=(.080,.090,.122)
        band=lambda x,c,w: np.clip(1-(np.abs((x-c+.5)%1-.5)-w)*180,0,1)
        broad=np.maximum(band(u,.23,.073),band(v,.22,.075));thin=np.maximum(band(u,.73,.012),band(v,.71,.012));hair=np.maximum(band(u,.09,.004),band(v,.065,.004))
        col[:,:,:3]+=broad[:,:,None]*np.array([.083,.090,.110]);col[:,:,:3]+=thin[:,:,None]*np.array([.065,.071,.086]);col[:,:,:3]+=hair[:,:,None]*np.array([.055,.06,.07])
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
head=bpy.data.objects.new('HEAD • six-degree natural tilt',None);CHAR.objects.link(head);head.location=(.020,-.014,1.528);head.rotation_euler=(math.radians(-2),math.radians(6),math.radians(5));head.scale=(1.10,1.0,.86)
ZP=[-.122,-.115,-.10,-.08,-.05,-.015,.02,.055,.085,.115,.14,.160]
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
def shape(z):
    if z>=.085:
        f=sqrt(max(0,1-((z-.040)/.120)**2));return max(.0005,.087*f),max(.0005,.094*f)
    return smooth_profile(z,ZP,WP),smooth_profile(z,ZP,DP)
def gauss(x,z,cx,cz,wx,wz):return exp(-((x-cx)/wx)**2-((z-cz)/wz)**2)
def face_y(x,z):
    w,d=shape(z);co=sqrt(max(0,1-(x/max(w,.001))**2));y=.010-.020*exp(-((z+.108)/.022)**2)-d*co
    y-=.022*gauss(x,z,0,-.023,.0125,.0125)+.0105*gauss(x,z,0,.003,.009,.032)
    y-=.005*gauss(x,z,0,-.031,.027,.011)
    y-=.008*(gauss(x,z,.013,-.030,.0065,.0065)+gauss(x,z,-.013,-.030,.0065,.0065))
    y+=.0014*(gauss(x,z,.0105,-.035,.0034,.0017)+gauss(x,z,-.0105,-.035,.0034,.0017))
    y-=.001*gauss(x,z,0,-.038,.004,.003)
    y-=.0025*(gauss(x,z,.050,-.017,.025,.021)+gauss(x,z,-.050,-.017,.025,.021))
    if -.075<z<-.014 and abs(x)>.01:
        for fx,fz in [(.020,-.027),(.026,-.033),(.030,-.039),(.033,-.045),(.034,-.051),(.032,-.057),(.030,-.061)]:
            y+=.0011*gauss(abs(x),z,fx,fz,.0024,.0042)
    y-=.009*(gauss(x,z,.047,-.028,.026,.024)+gauss(x,z,-.047,-.028,.026,.024))
    y+=.010*(gauss(x,z,.037,.018,.022,.013)+gauss(x,z,-.037,.018,.022,.013))
    y-=.008*gauss(x,z,0,-.056,.036,.023)
    return y
V=[];F=[];cols=[];NZ=224;NT=320
for i,z in enumerate(np.linspace(ZP[0],ZP[-1],NZ)):
    w,d=shape(z)
    for j in range(NT):
        th=2*pi*j/NT;x=w*sin(th);front=cos(th);y=.010-.020*exp(-((z+.108)/.022)**2)-d*front
        if front>0:y+=(face_y(x,z)-(.010-.020*exp(-((z+.108)/.022)**2)-d*max(front,0)))*front**.65
        else:y+=.012*(-front)*exp(-((z-.025)/.095)**2)
        V.append((x,y,z));bl=.20*(gauss(x,z,.052,-.031,.023,.024)+gauss(x,z,-.052,-.031,.023,.024))*max(front,0);cols.append((.62+bl*.14,.40-bl*.12,.315-bl*.02,1))
for i in range(NZ-1):
    for j in range(NT):
        ids=(i*NT+j,i*NT+(j+1)%NT,(i+1)*NT+(j+1)%NT,(i+1)*NT+j);cx=sum(V[k][0] for k in ids)/4;cz=sum(V[k][2] for k in ids)/4;cy=sum(V[k][1] for k in ids)/4;u=cx/.034
        h=max(0,1-u*u)**.65
        hole=abs(u)<1 and -.070+.017*u*u-.0015*h<cz<-.047-.006*u*u+.0015*h and cy<-.025
        for es in [-1,1]:
            eu=(cx-es*.037)/.0184;eh=max(0,1-eu*eu)**.62
            if abs(eu)<1 and cy<-.025 and .019+.0017*es*eu-.0076*eh<cz<.019+.0017*es*eu+.0109*eh:hole=True
        if not hole:F.append(ids)
headskin=skin.copy();headskin.name='Face skin • original vertex blush';cn=headskin.node_tree.nodes.new('ShaderNodeVertexColor');cn.layer_name='Col';headskin.node_tree.links.new(cn.outputs['Color'],headskin.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
hm=mesh('Face • sculpted continuous anatomical surface',V,F,headskin,parent=head);ca=hm.data.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT');ca.data.foreach_set('color',np.array(cols,dtype=np.float32).ravel())
# Original subtle skin normal and roughness maps, generated from deterministic noise.
uvlay=hm.data.uv_layers.new(name='SkinUV')
for poly in hm.data.polygons:
    us=[((hm.data.loops[li].vertex_index%NT)/NT+.5)%1 for li in poly.loop_indices]
    seam=max(us)-min(us)>.5
    for li,u in zip(poly.loop_indices,us):
        vi=hm.data.loops[li].vertex_index;q=hm.data.vertices[vi].co;uvlay.data[li].uv=((q.x+.09)/.18,(q.z+.122)/.282)
H,W=1024,1024;rng=np.random.default_rng(6118);height=rng.normal(0,1,(H,W)).astype(np.float32)
for _ in range(3):height=(height*4+np.roll(height,1,0)+np.roll(height,-1,0)+np.roll(height,1,1)+np.roll(height,-1,1))/8
height/=max(float(height.std()),1e-6)
dx=(np.roll(height,-1,1)-np.roll(height,1,1))*.050;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*.050
normal=np.dstack((-dx,-dy,np.ones_like(dx)));normal/=np.linalg.norm(normal,axis=2,keepdims=True);rgba=np.ones((H,W,4),np.float32);rgba[:,:,:3]=normal*.5+.5
im=bpy.data.images.new('Original skin micro-normal',width=W,height=H,alpha=True);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(BUILD/'Original skin micro-normal.png');im.file_format='PNG';im.save();im.pack()
nt=headskin.node_tree;tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;n=nt.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.42;nt.links.new(tex.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],nt.nodes.get('Principled BSDF').inputs['Normal'])
rough=np.clip(.44+.024*height,.35,.54);rgba[:,:,:3]=rough[:,:,None]
im=bpy.data.images.new('Original skin micro-roughness',width=W,height=H,alpha=True);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(BUILD/'Original skin micro-roughness.png');im.file_format='PNG';im.save();im.pack();tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.links.new(tex.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Roughness'])
del height,dx,dy,normal,rgba,rough

# neck and covered upper chest
neck=tube('Neck and upper chest',[(-.002,.014,1.304),(.005,.011,1.367),(.006,.012,1.476)],[.053,.0355,.034],skin,n=32,sides=56,ratio=.89)
for side in [-1,1]:
    uvball('Ear • '+str(side),(side*.086,.010,-.013),(.015,.011,.031),skin,head)
    uvball('Ear concha • '+str(side),(side*.091,-.000,-.013),(.007,.003,.016),earinner,head,24,16)
    ep=[(side*(.088+.012*sin(t)),-.002-.002*sin(t),-.011+.026*cos(t)) for t in np.linspace(-.2,pi*1.7,48)]
    line('Ear helix',ep,skin,.0027,head)
    # Almond whites precisely fitted to the face, rather than exposed sphere eyes.
    cx=side*.037;cz=.019;w=.0168;verts=[];faces=[]
    def eyey(x,z):return face_y(cx,cz)+.015-.020*sqrt(max(.015,1-((x-cx)/.0235)**2-((z-cz)/.0215)**2))
    for i,t in enumerate(np.linspace(-1,1,49)):
        x=cx+w*t;lift=.0017*side*t;h=max(0,1-t*t)**.62
        for j,v in enumerate(np.linspace(-1,1,13)):
            z=cz+lift+v*(.0076 if v>0 else .0048)*h;verts.append((x,eyey(x,z),z))
    for i in range(48):
        for j in range(12):k=i*13+j;faces.append((k,k+13,k+14,k+1))
    mesh('Eye white • '+str(side),verts,faces,sclera,parent=head)
    # Iris disks follow the curvature of the eye, with a fine dark limbal ring.
    for radius,mat,offset in [(.0082,pupilmat,.00025),(.0078,irismat,.00038),(.0036,pupilmat,.00058)]:
        vs=[(cx,eyey(cx,cz+.0030)-offset,cz+.0030)]
        for t in np.linspace(0,2*pi,65)[:-1]:
            xx=cx+radius*cos(t);zz=cz+.0030+radius*sin(t);u=(xx-cx)/w;h=max(0,1-u*u)**.62;zz=max(cz+.0017*side*u-.0048*h+.00015,min(cz+.0017*side*u+.0076*h-.00015,zz));vs.append((xx,eyey(xx,zz)-offset,zz))
        mesh('Iris or pupil • '+str(side),vs,[(0,j+1,(j+1)%64+1) for j in range(64)],mat,parent=head)
    for k in range(33):
        th=2*pi*k/33;pts=[]
        for rr in np.linspace(.0032,.0065,5):
            x=cx+rr*cos(th);z=cz+.0030+rr*sin(th);u=(x-cx)/w;h=max(0,1-u*u)**.62;z=max(cz+.0017*side*u-.0048*h+.0002,min(cz+.0017*side*u+.0076*h-.0002,z));pts.append((x,eyey(x,z)-.00051,z))
        line('Iris fibres',pts,irislight,.00009,head)
    uvball('Eye catchlight',(cx-.0018,eyey(cx-.0018,cz+.0024)-.0008,cz+.0024),(.0011,.00045,.0011),highlight,head,20,12)
    uvball('Eye secondary glint',(cx+.0016,eyey(cx+.0016,cz-.0017)-.0007,cz-.0017),(.00042,.0003,.00042),highlight,head,16,8)
    for upper in [True,False]:
        vs=[];fs=[];edge=[]
        for i,tt in enumerate(np.linspace(-1,1,65)):
            t=float(tt);x=cx+w*t;h=max(0,1-t*t)**.62;z0=cz+.0017*side*t+(.0076 if upper else -.0048)*h;y0=eyey(x,z0)-.0006;edge.append((x,y0,z0))
            for v in np.linspace(0,1,9):
                v=float(v);xx=cx+(x-cx)*(1+.14*v);z=z0+(1 if upper else -1)*(.0065 if upper else .0050)*h*v
                y=(1-v)*y0+v*(face_y(xx,z)-.00015)-(.00065 if upper else .00055)*sin(pi*v)*h;vs.append((xx,y,z))
        for i in range(64):
            for j in range(8):k=i*9+j;fs.append((k,k+9,k+10,k+1) if upper else (k,k+1,k+10,k+9))
        mesh('Upper eyelid - continuous skin fold' if upper else 'Lower eyelid - soft skin rim',vs,fs,skin,parent=head)
        if upper:
            line('Fine upper lash line',[(x,y-.0005,z-.0001) for x,y,z in edge],browmat,.00052,head,[.1+.9*sin(pi*i/64)**.65 for i in range(65)])
            for k in range(14):
                ii=7+k*4;x,y,z=edge[ii];sideways=side*(.0005+.0007*k/13)
                line('Individual upper lashes',[(x,y-.0006,z),(x+sideways*.5,y-.0013,z+.0006),(x+sideways,y-.0018,z+.0011)],browmat,.00010,head,[1,.75,.10])
            cp=[]
            for i,(x,y,z) in enumerate(edge[5:-5]):
                zz=z+.0056*sin(pi*(i+5)/64)**.8;cp.append((x,face_y(x,zz)-.00022,zz))
            line('Subtle upper eyelid crease',cp,crease,.00017,head)
    cornerx=cx-side*w*.91;cornerz=cz-.0014
    uvball('Inner eye caruncle',(cornerx,eyey(cornerx,cornerz)-.0003,cornerz),(.0014,.00055,.0011),lips,head,20,12)
    bm=material('Brow soft pigment '+str(side),(.10,.057,.033),.83);vc=bm.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Col';bm.node_tree.links.new(vc.outputs['Color'],bm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    vs=[];fs=[];cc=[]
    for i,tt in enumerate(np.linspace(-1,1,65)):
        t=float(tt);x=cx+.025*t;midz=.039+.0042*(1-t*t)+.0017*side*t;thick=.0024*max(0,1-t*t)**.55
        for v in np.linspace(-1,1,9):
            v=float(v);z=midz+v*thick;vs.append((x,face_y(x,z)-.00023,z));opacity=(1-abs(v)**.6)*max(0,1-t*t)**.5*.76
            color=np.array([.10,.057,.033])*opacity+np.array([.62,.40,.315])*(1-opacity);cc.append((*color,1))
    for i in range(64):
        for j in range(8):k=i*9+j;fs.append((k,k+9,k+10,k+1))
    ob=mesh('Eyebrow soft pigment '+str(side),vs,fs,bm,parent=head);attr=ob.data.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.array(cc,dtype=np.float32).ravel())
    for k in range(56):
        t=-.96+1.92*k/55;x=cx+.025*t;z=.039+.0042*(1-t*t)+.0017*side*t;delta=random.uniform(-.001,.001);length=.0015*max(0,1-t*t)**.5
        ps=[(x,face_y(x,z+delta)-.0004,z+delta-length*.5),(x+side*.0006,face_y(x+side*.0006,z+delta+length)-.0005,z+delta+length)]
        line('Fine eyebrow hairs',ps,hairmats[k%4],.000085,head,[.8,.12])
    nostrilmat=material('Nasal shadow '+str(side),(.21,.093,.064),.76)
    nx=side*.011;nz=-.035
    uvball('Nasal opening '+str(side),(nx,face_y(nx,nz)-.00025,nz),(.0034,.00035,.00105),nostrilmat,head,28,12)

markmat=material('Subtle facial pigment',(.23,.115,.080),.86)
for mx,mz,mr in [(-.060,-.045,.00065),(-.011,.005,.00060),(.043,-.025,.00062)]:
    uvball('Small facial pigment detail',(mx,face_y(mx,mz)-.00013,mz),(mr,.00006,mr),markmat,head,20,10)
# Original smiling mouth: fitted lip surfaces, gum arch, and individual crowns.
MW=.034
verts=[];faces=[]
for i,uu in enumerate(np.linspace(-1,1,89)):
    u=float(uu);x=MW*u;top=-.047-.006*u*u;bottom=-.070+.017*u*u
    for tt in np.linspace(0,1,13):
        t=float(tt);z=bottom*(1-t)+top*t;verts.append((x,face_y(x,z)+.0055,z))
for i in range(88):
    for j in range(12):k=i*13+j;faces.append((k,k+13,k+14,k+1))
mesh('Smile - recessed oral cavity',verts,faces,oral,parent=head)
lipshade=lips.copy();lipshade.name='Lips - warm blended vermilion';vc=lipshade.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Col';lipshade.node_tree.links.new(vc.outputs['Color'],lipshade.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
lipshade.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.44
for upper in [True,False]:
    vs=[];fs=[];colors=[]
    for i,uu in enumerate(np.linspace(-1,1,97)):
        u=float(uu);x=MW*u;h=max(0,1-u*u)**.65;inner=(-.047-.006*u*u) if upper else (-.070+.017*u*u)
        thick=(.0043+.0010*(exp(-((u-.22)/.17)**2)+exp(-((u+.22)/.17)**2)))*h if upper else .0072*h
        for j,vv in enumerate(np.linspace(0,1,11)):
            v=float(vv);xx=x*(1+.045*v);z=inner+(1 if upper else -1)*thick*v;y=face_y(xx,z)-(.0014*(1-v)+.0003*v)-(.0026 if upper else .0032)*sin(pi*v)*h
            vs.append((xx,y,z));fade=v**2.4;inn=np.array([.50,.150,.165]);out=np.array([.62,.40,.315]);cc=inn*(1-fade)+out*fade;colors.append((*cc,1))
    for i in range(96):
        for j in range(10):k=i*11+j;fs.append((k,k+11,k+12,k+1) if upper else (k,k+1,k+12,k+11))
    ob=mesh('Upper lip - cupid bow' if upper else 'Lower lip - full vermilion',vs,fs,lipshade,parent=head);ca=ob.data.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT');ca.data.foreach_set('color',np.array(colors,dtype=np.float32).ravel())
gum=material('Gum - soft coral tissue',(.40,.135,.115),.53,sss=.12)
vs=[];fs=[]
for i,u in enumerate(np.linspace(-.88,.88,65)):
    x=MW*u;top=-.047-.006*u*u
    for dz in [-.0015,.0015]:vs.append((x,face_y(x,top)+.0032,top+dz))
for i in range(64):k=i*2;fs.append((k,k+2,k+3,k+1))
mesh('Gum arch behind upper lip',vs,fs,gum,parent=head)
def dental_crown(name,x,top,width,height):
    zc=top-.0005-height/2;yc=face_y(x,zc)+.0001;vs=[(x,yc-.0016,zc)];fs=[];nt=48;nr=12
    for rr in np.linspace(1/nr,1,nr):
        r=float(rr)
        for th in np.linspace(0,2*pi,nt,endpoint=False):
            c=float(cos(th));ss=float(sin(th));xx=.5*width*math.copysign(abs(c)**.625,c)*r;zz=.5*height*math.copysign(abs(ss)**.625,ss)*r
            xx*=1-.065*(zz/(height/2)+1)/2;yy=-.0016*sqrt(max(0,1-r*r));vs.append((x+xx,yc+yy,zc+zz))
    for j in range(nt):fs.append((0,1+j,1+(j+1)%nt))
    for i in range(nr-1):
        for j in range(nt):a=1+i*nt+j;b=1+i*nt+(j+1)%nt;fs.append((a,a+nt,b+nt,b))
    base=len(vs)
    for j in range(nt):p=vs[1+(nr-1)*nt+j];vs.append((p[0],p[1]+.0055,p[2]))
    for j in range(nt):a=1+(nr-1)*nt+j;b=1+(nr-1)*nt+(j+1)%nt;fs.append((a,b,base+(j+1)%nt,base+j))
    fs.append(tuple(base+j for j in range(nt-1,-1,-1)))
    return mesh(name,vs,fs,teeth,parent=head)
widths=[w*1.07 for w in [.0046,.0055,.0065,.0076,.0076,.0065,.0055,.0046]]
heights=[.008,.011,.015,.0185,.0185,.015,.011,.008];start=-(sum(widths)+.00015*7)/2
for i,(w,h) in enumerate(zip(widths,heights)):
    x=start+w/2;start+=w+.00015;u=x/MW;top=-.047-.006*u*u;dental_crown('Upper rounded crown '+str(i),x,top,w,h)
for side in [-1,1]:
    ps=[]
    for t in np.linspace(0,1,14):
        x=side*(.0335+.004*t);z=-.053+.003*t;ps.append((x,face_y(x,z)-.00020,z))
    line('Smile corner crease',ps,crease,.00017,head,[1-i/14 for i in range(14)])

# One fitted hair mass with a swept hairline; all fibres are authored geometry.
hairbase=material('Hair - natural dark underlying mass',(.007,.0046,.0038),.59)
hairbase.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.22
# Original directional surface detail: generated mathematical strands, no scan or photograph.
HH=512;WW=1024;yy,xx=np.mgrid[0:HH,0:WW];uu=xx/WW;vv=yy/HH
phase=2*pi*(uu*120+.15*np.sin(vv*pi*5)+.06*np.sin(vv*pi*17));ridge=np.sin(phase)+.35*np.sin(phase*2.7+1)+.15*np.sin(phase*6.3)
normal=np.dstack((.20*np.cos(phase)+.07*np.cos(phase*2.7+1),.012*np.sin(vv*pi*5),np.ones_like(uu)));normal/=np.linalg.norm(normal,axis=2,keepdims=True)
pixels=np.ones((HH,WW,4),np.float32);pixels[:,:,:3]=normal*.5+.5
im=bpy.data.images.new('Original directional hair normal',width=WW,height=HH,alpha=True);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(BUILD/'Original directional hair normal.png');im.file_format='PNG';im.save();im.pack()
nt=hairbase.node_tree;tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.48;nt.links.new(tx.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],nt.nodes.get('Principled BSDF').inputs['Normal'])
pixels[:,:,:3]=np.array([.078,.064,.057])[None,None,:]*(1+.16*ridge[:,:,None])
im=bpy.data.images.new('Original tonal hair strands',width=WW,height=HH,alpha=True);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(BUILD/'Original tonal hair strands.png');im.file_format='PNG';im.save();im.pack();tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nt.links.new(tx.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
nt.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.40;nt.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.36;nt.nodes.get('Principled BSDF').inputs['Anisotropic'].default_value=.45
del yy,xx,uu,vv,phase,ridge,normal,pixels

for hm0 in hairmats:hm0.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.26
HT=[-pi,-2,-1.6,-1.2,-.7,-.3,0,.35,.60,.90,1.2,1.6,2,pi]
HZ=[-.085,-.065,-.038,-.010,.021,.032,.036,.056,.091,.029,-.010,-.036,-.060,-.085]
def hairpoint(th,t,extra=0):
    th=(th+pi)%(2*pi)-pi;bot=smooth_profile(th,HT,HZ);end=math.acos(max(-.99,min(.99,(bot-.020)/.140)));pol=t*end;zs=.020+.140*cos(pol);w,d=shape(zs);back=(1-cos(th))/2;pad=(.007+.010*back)*max(.03,sin(pol))+extra
    cy=.010-.020*exp(-((zs+.108)/.022)**2);zz=zs+.006+.00055*sin(th*51+1.2)*t**18
    return Vector(((w+pad)*sin(th),cy-(d+pad)*cos(th),zz))
V=[];F=[];nr=58;ns=180
for t in np.linspace(.012,1,nr):
    for j in range(ns):V.append(hairpoint(2*pi*j/ns,float(t)))
for i in range(nr-1):
    for j in range(ns):k=i*ns+j;q=i*ns+(j+1)%ns;F.append((k,k+ns,q+ns,q))
V.append((0,.010,.166));tip=len(V)-1
for j in range(ns):F.append((tip,j,(j+1)%ns))
hair_ob=mesh('Hair - continuous swept scalp and fringe',V,F,hairbase,parent=head)
huv=[]
for vi in range(len(V)):
    if vi>=nr*ns:huv.append((.5,0));continue
    tt=.012+.988*(vi//ns)/(nr-1);th=(2*pi*(vi%ns)/ns+pi)%(2*pi)-pi;target=th
    for _ in range(8):target=th-.95*(1-tt)**.60*max(0,cos(target))
    huv.append(((target/(2*pi)+.5)%1,tt))
uvlay=hair_ob.data.uv_layers.new(name='HairUV')
for poly in hair_ob.data.polygons:
    us=[huv[hair_ob.data.loops[li].vertex_index][0] for li in poly.loop_indices];seam=max(us)-min(us)>.5
    for li,u in zip(poly.loop_indices,us):uvlay.data[li].uv=(u+1 if seam and u<.5 else u,huv[hair_ob.data.loops[li].vertex_index][1])
for k in range(850):
    target=2*pi*k/850-pi;pts=[]
    for tt in np.linspace(.020,1,42):
        t=float(tt);th=target+.95*(1-t)**.60*max(0,cos(target));p=hairpoint(th,t,.0003+.00012*sin(t*27+k));pts.append(p)
    line('Swept scalp fibres',pts,hairmats[k%6],.000115,head,[.20+.8*sin(pi*i/41)**.26 for i in range(42)])
# Short fine wisps break the mathematical hairline without exposing scalp gaps.
for k in range(85):
    target=-1.18+2.35*k/84;pts=[]
    for tt in np.linspace(.65,1.015,24):
        t=float(tt);pts.append(hairpoint(target+.30*(1-t),t,.0005))
    line('Hairline wisps',pts,hairmats[k%6],.000105,head,[max(.08,1-i/24)**.5 for i in range(24)])
# Wavy ponytails: a dark closed volume plus finer curled surface strands.
def pony_center(side,t):
    ps=[Vector((side*.084,.042,-.031)),Vector((side*.139,.045,-.108)),Vector((side*.108,-.020,-.192)),Vector((side*.102,-.052,-.267))]
    t=float(t);c=(1-t)**3*ps[0]+3*(1-t)**2*t*ps[1]+3*(1-t)*t*t*ps[2]+t**3*ps[3]
    c.x+=side*.008*sin(t*pi*3.4+.3)*sin(pi*min(t,1));c.y+=.008*sin(t*pi*4.1+side)*sin(pi*min(t,1));c.y-=.033*(t*t*(3-2*t));return c

def pony_point(side,t,angle,mult=1):
    t=float(t);r=float(np.interp(t,[0,.18,.40,.65,.85,1.03],[.017,.030,.033,.027,.020,.0008]))
    angle+=.70*t+.18*sin(t*14+side);r*=mult*(1+.05*cos(angle*11+t*10)+.045*cos(angle*7-t*15))
    c=pony_center(side,t);return c+Vector((r*cos(angle),r*.77*sin(angle),.0017*sin(angle*4)*t))
for side in [-1,1]:
    V=[];F=[];nt=112;nr=62
    for t in np.linspace(0,1.025,nr):
        for j in range(nt):V.append(pony_point(side,float(t),2*pi*j/nt))
    for i in range(nr-1):
        for j in range(nt):k=i*nt+j;q=i*nt+(j+1)%nt;F.append((k,k+nt,q+nt,q))
    F.append(tuple(range(nt)))
    F.append(tuple((nr-1)*nt+j for j in range(nt-1,-1,-1)))
    po=mesh('Ponytail - naturally waved underlying volume '+str(side),V,F,hairbase,parent=head)
    puv=po.data.uv_layers.new(name='HairUV')
    for poly in po.data.polygons:
        us=[(po.data.loops[li].vertex_index%nt)/nt for li in poly.loop_indices];seam=max(us)-min(us)>.5
        for li,u in zip(poly.loop_indices,us):
            vi=po.data.loops[li].vertex_index;puv.data[li].uv=(u+1 if seam and u<.5 else u,(vi//nt)/(nr-1))
    for k in range(780):
        th=2*pi*k/780;end=random.uniform(.90,1.025);mult=random.uniform(1.008,1.038);phase=random.random()*pi*2;pts=[]
        for t in np.linspace(0,end,42):
            tt=float(t);p=pony_point(side,tt,th+.025*sin(tt*19+phase),mult);p.x+=.00045*sin(tt*33+phase)*tt;pts.append(p)
        line('Wavy ponytail fibres',pts,hairmats[k%6],.000125,head,[.10+.9*(1-i/42)**.25 for i in range(42)])
    for k in range(32):
        th=random.uniform(0,2*pi);start=random.uniform(.05,.35);end=random.uniform(.80,1.06);pts=[]
        for t in np.linspace(start,end,34):
            tt=float(t);p=pony_point(side,tt,th,1.12+.09*sin(pi*(tt-start)/(end-start)));p.x+=.004*sin(tt*16+k)*sin(pi*(tt-start)/(end-start));pts.append(p)
        line('Ponytail loose wisps',pts,hairmats[k%6],.000105,head,[max(.07,sin(pi*i/33))**.4 for i in range(34)])
    uvball('Ponytail tie',(side*.084,.042,-.034),(.024,.019,.007),webbing,head,32,16)
    for k in range(13):
        off=(k-6)*.00018;pts=bez([(side*(.079+off),-.030,.005),(side*(.092+off),-.057,-.040),(side*(.057+off),-.069,-.100),(side*(.067+off),-.061,-.161-k*.001)],34)
        line('Soft face-framing strands',pts,hairmats[k%6],.00018,head,[.2+.8*(1-i/34)**.5 for i in range(34)])

# Tailored blouse with an explicit continuous V opening, not deleted grid faces.
TP=[(1.054,.118,.078),(1.073,.128,.083),(1.115,.123,.079),(1.170,.132,.085),(1.229,.145,.091),(1.285,.154,.085),(1.325,.158,.068),(1.348,.126,.055),(1.375,.051,.044)]
def blouse_profile(z):
    return smooth_profile(z,[p[0] for p in TP],[p[1] for p in TP]),smooth_profile(z,[p[0] for p in TP],[p[2] for p in TP])
V=[];F=[];UV=[];edges=[[],[]];rows=92;ns=144
for i,zz0 in enumerate(np.linspace(TP[0][0],TP[-1][0],rows)):
    z=float(zz0);w,d=blouse_profile(z);t=(z-1.054)/.321;opening=max(0,z-1.301)*.68;angle=math.asin(min(.90,opening/w))
    for j in range(ns+1):
        th=angle+(2*pi-2*angle)*j/ns;x=w*sin(th);front=cos(th);y=.005-d*front
        wrinkle=.0008*sin(th*11+t*24)+.0004*sin(th*19-t*33)+.0014*sin(th*9+t*51)*exp(-((t-.13)/.20)**2)
        tension=0
        for offset,amp in [(0,.0035),(.033,-.0023),(.066,.0025)]:tension+=amp*exp(-((z-(1.084+.80*abs(x)+offset))/.014)**2)*exp(-((abs(x)-.070)/.082)**2)
        y-=(wrinkle+tension)*max(front,0)+wrinkle*min(front,0);zz=z+.0016*sin(th*8)*exp(-((t-.07)/.12)**2);V.append((x,y,zz));UV.append((j/ns,t))
        if j==0:edges[0].append((x,y-.0004,zz))
        if j==ns:edges[1].append((x,y-.0004,zz))
for i in range(rows-1):
    for j in range(ns):k=i*(ns+1)+j;F.append((k,k+1,k+ns+2,k+ns+1))
shirt=mesh('Blouse - continuous tailored cotton',V,F,white,uv=UV);md=shirt.modifiers.new('Cotton thickness','SOLIDIFY');md.thickness=.0012
for side,edge in enumerate(edges):line('Fine neckline topstitch '+str(side),[p for p in edge if p[2]>1.302],seamwhite,.00024)

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
    palm=uvball('Hand palm • '+str(s),(s*.083,.133,.985),(.021,.010,.027),skin);palm.rotation_euler.y=s*-.28
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
# Pleated tartan skirt, with sharp folded radial profiles and rounded cloth edges.
V=[];F=[];UV=[];nr=40;nt=320
for i,t in enumerate(np.linspace(0,1,nr)):
    z=1.061-.320*t;wx=.118+.094*(t**.83);dy=.087+.063*(t**.86);amp=.0015+.011*t**.72
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
    pp=bez([(s*.123,.136,1.315),(s*.151,.023,1.396),(s*.133,-.074,1.343),(s*.131,-.084,1.251)],48)
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
# Fit garment proportions: longer blouse and lower waistband; skirt hem unchanged.
def fitted_body_z(z):
    return float(np.interp(z,[.50,.741,1.061,1.250,1.340,1.375,1.400,1.600],[.50,.720,1.035,1.262,1.376,1.397,1.409,1.600]))
bpy.context.view_layer.update()
for ob in list(CHAR.objects):
    if ob.parent is not None or ob.type not in {'MESH','CURVE'} or ob.name.startswith('Neck'):continue
    mat=ob.matrix_world.copy();inv=mat.inverted()
    if ob.type=='MESH':
        for v in ob.data.vertices:
            q=mat@v.co;q.z=fitted_body_z(q.z);v.co=inv@q
        ob.data.update()
    else:
        for sp in ob.data.splines:
            for pt in sp.points:
                q=mat@Vector(pt.co[:3]);q.z=fitted_body_z(q.z);q=inv@q;pt.co=(*q,1)
# Relaxed upper-body lean around the waist, preserving all child transforms.
bpy.context.view_layer.update()
upper=[o for o in CHAR.objects if o.parent is None and not o.name.startswith('Skirt')]
lean=bpy.data.objects.new('POSE - relaxed torso lean',None);CHAR.objects.link(lean);lean.location=(0,0,1.035);bpy.context.view_layer.update()
for ob in upper:
    ob.parent=lean;ob.matrix_parent_inverse=lean.matrix_world.inverted()
lean.rotation_euler.y=math.radians(3.5)
# Legs: identical femur and tibia lengths, solved geometrically for the pose.
def knee_ik(hip,ankle,pole,L1=.445,L2=.415):
    hip=Vector(hip);ankle=Vector(ankle);axis=(ankle-hip).normalized();D=(ankle-hip).length
    if not abs(L1-L2)<D<L1+L2:raise ValueError('Unreachable ankle target')
    a=(L1*L1-L2*L2+D*D)/(2*D);h=sqrt(max(0,L1*L1-a*a));perp=Vector(pole);perp=(perp-axis*perp.dot(axis)).normalized();return hip+axis*a+perp*h

LEGS=[{'side':'L','hip':(-.065,.032,.945),'knee':(-.015,-.073,.510),'ankle':(-.100,.055,.137)}, {'side':'R','hip':(.074,.047,.950),'knee':(.059,.035,.502),'ankle':(.020,.015,.095)}]
for leg in LEGS:leg['knee']=tuple(knee_ik(leg['hip'],leg['ankle'],(1,-1,0) if leg['side']=='L' else (-.2,1,0)))
measurements={}
for d in LEGS:
    hip,knee,ankle=map(Vector,[d['hip'],d['knee'],d['ankle']]);s=d['side'];mid=hip.lerp(knee,.42);below=knee.lerp(ankle,.35)
    tube('Leg • thigh and knee anatomy '+s,[hip,mid,knee,knee.lerp(ankle,.22)],[.063,.060,.038,.031],skin,n=72,sides=72,ratio=.92)
    measurements[s]={'femur':(hip-knee).length,'tibia':(knee-ankle).length,'hip':list(hip),'knee':list(knee),'ankle':list(ankle)}
    top=knee.lerp(ankle,.15);calf=knee.lerp(ankle,.36);low=knee.lerp(ankle,.84);end=ankle+Vector((0,-.007,-.027))
    tube('Sock • fine ribs '+s,[top,calf,low,ankle,end],[.0376,.0435,.029,.0265,.025],sock,n=70,sides=144,ratio=.92,ribs=.011)
    cuffend=top.lerp(calf,.20);tube('Sock • ribbed top band '+s,[top,cuffend],[.0385,.0405],sock,n=8,sides=144,ratio=.92,ribs=.012)
# Leather loafers: separate sole, stitched vamp, raised penny strap and open collar.
for side,cx,cy,base,yaw in [('L',-.100,.033,.055,-.13),('R',.020,-.013,.005,.10)]:
    shoe=bpy.data.objects.new('Loafer assembly '+side,None);CHAR.objects.link(shoe);shoe.location=(cx,cy,base);shoe.rotation_euler.z=yaw;shoe.rotation_euler.x=.15 if side=='L' else 0
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
    sv=[];sf=[]
    for i,x in enumerate(np.linspace(-.039,.039,29)):
        for yy in [-.050,-.037,-.024]:sv.append((x,yy,.069-.027*(abs(x)/.040)**2))
    for i in range(28):
        for j in range(2):k=i*3+j;sf.append((k,k+3,k+4,k+1))
    strap=mesh('Loafer - fitted penny saddle '+side,sv,sf,leather,parent=shoe);sm=strap.modifiers.new('Leather strap thickness','SOLIDIFY');sm.thickness=.0025
    # Curve the strap gently over the vamp by adding a central top layer.
    line('Penny strap raised seam',[(float(x),-.050,.070-.027*(abs(x)/.040)**2) for x in np.linspace(-.039,.039,30)],stitch,.0008,shoe)
    box('Penny strap slot '+side,(0,-.038,.071),(.020,.003,.0012),sole,.001,shoe)

def optimize_static_web_export():
    """Bake modifiers and merge equal-material pieces; keep all original source geometry."""
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();baked=[]
    for ob in list(CHAR.objects):
        if ob.type=='MESH':
            me=bpy.data.meshes.new_from_object(ob.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
            baked.append((ob,me,ob.matrix_world.copy()))
    for ob,me,matrix in baked:
        ob.modifiers.clear();ob.parent=None;ob.matrix_world=matrix;ob.data=me
    bpy.context.view_layer.update();groups={}
    for ob,me,matrix in baked:groups.setdefault(tuple(m.name if m else '' for m in me.materials),[]).append(ob)
    for key,obs in groups.items():
        if len(obs)>1:
            bpy.ops.object.select_all(action='DESELECT')
            for ob in obs:ob.select_set(True)
            bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();obs[0].name='WEB - '+(' / '.join(key) or 'unassigned')
    meshes=[o for o in CHAR.objects if o.type=='MESH']
    result={'meshes':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'triangles':sum(sum(max(0,len(p.vertices)-2) for p in o.data.polygons) for o in meshes)}
    print('WEB_GEOMETRY_METRICS',json.dumps(result),flush=True);return result

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
views={'front':((0,-5.3,2.02),(0,0,.844),1.78,(2,3)),'face':((.05,-4.2,1.65),(.05,-.015,1.525),.43,(1,1)),'threequarter':((3.4,-5.3,2.3),(0,0,.865),1.83,(2,3)),'back':((0,5.3,2.1),(0,0,.865),1.83,(2,3)),'side':((5.3,-.05,2.0),(0,0,.865),1.83,(2,3))}
def setview(name):
    pos,target,scale,aspect=views[name];cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale;scene.render.resolution_y=args.size;scene.render.resolution_x=round(args.size*aspect[0]/aspect[1])
setview('front')
base='gpt6_astra_pro_mcp_blender_rgirljk'
if not args.no_export:
    bpy.ops.wm.save_as_mainfile(filepath=str(BUILD/(base+f'_r{args.revision:02d}.blend')))
    # Convert curve duplicates for glTF while preserving editable curves in the .blend.
    bpy.ops.object.select_all(action='DESELECT')
    for o in CHAR.objects:
        if o.type=='CURVE':o.select_set(True)
    if bpy.context.selected_objects:bpy.context.view_layer.objects.active=bpy.context.selected_objects[0];bpy.ops.object.convert(target='MESH')
    metrics['web_export']=optimize_static_web_export()
    (BUILD/f'geometry_metrics_r{args.revision:02d}.json').write_text(json.dumps(metrics,indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in CHAR.objects:o.select_set(True)
    bpy.context.view_layer.objects.active=hm
    bpy.ops.export_scene.gltf(filepath=str(BUILD/(base+f'_r{args.revision:02d}.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
    print('EXPORT_COMPLETE',str(BUILD/(base+f'_r{args.revision:02d}.glb')),flush=True)
    bpy.ops.object.select_all(action='DESELECT')
    lite_meshes=[]
    for ob in CHAR.objects:
        if ob.type=='MESH' and not any('espresso' in m.name for m in ob.data.materials if m):ob.select_set(True);lite_meshes.append(ob)
    bpy.context.view_layer.objects.active=hm
    bpy.ops.export_scene.gltf(filepath=str(BUILD/(base+f'_lite_r{args.revision:02d}.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
    metrics['lite_export']={'meshes':len(lite_meshes),'triangles':sum(sum(max(0,len(p.vertices)-2) for p in ob.data.polygons) for ob in lite_meshes),'difference':'Fine fibre meshes omitted; original volume, directional surface maps, face, clothing and pose retained.'}
    (BUILD/f'geometry_metrics_r{args.revision:02d}.json').write_text(json.dumps(metrics,indent=2))
    print('LITE_EXPORT_COMPLETE',json.dumps(metrics['lite_export']),flush=True)

for name in args.views.split(','):
    if name not in views:continue
    setview(name);scene.render.filepath=str(OUT/f'{name}_r{args.revision:02d}.png');print('RENDER_BEGIN',name,flush=True);bpy.ops.render.render(write_still=True);print('RENDER_COMPLETE',name,flush=True)
print('BUILD_COMPLETE',args.revision,flush=True)
