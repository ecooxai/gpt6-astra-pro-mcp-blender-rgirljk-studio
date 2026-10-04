"""Original anatomical detail fitted to portrait_surface.py."""
profiles=[(1.275,.140,.073,.005),(1.312,.133,.067,.002),(1.338,.091,.052,-.003),(1.360,.052,.037,.005),(1.384,.0355,.031,.012),(1.476,.034,.030,.012)]
vs=[];fs=[];nz=82;na=80
for z in np.linspace(profiles[0][0],profiles[-1][0],nz):
    zz=float(z);rx=smooth_profile(zz,[q[0] for q in profiles],[q[1] for q in profiles]);ry=smooth_profile(zz,[q[0] for q in profiles],[q[2] for q in profiles]);cy=smooth_profile(zz,[q[0] for q in profiles],[q[3] for q in profiles])
    for j in range(na):
        a=2*pi*j/na;vs.append((.005+rx*sin(a),cy-ry*cos(a),zz))
for i in range(nz-1):
    for j in range(na):k=i*na+j;q=i*na+(j+1)%na;fs.append((k,q,q+na,k+na))
fs.append(tuple(range(na-1,-1,-1)));fs.append(tuple((nz-1)*na+j for j in range(na)))
neck=mesh("Neck and covered upper chest",vs,fs,skin)

earskin=material("Ears - warm translucent skin",(.56,.29,.23),.49,sss=.23)
for s in [-1,1]:
    uvball("Ear "+str(s),(s*.086,.010,-.014),(.014,.010,.029),earskin,head)
    uvball("Ear concha "+str(s),(s*.091,-.0005,-.014),(.006,.0025,.015),earinner,head,28,16)
    ep=[(s*(.088+.010*sin(t)),-.002-.002*sin(t),-.012+.024*cos(t)) for t in np.linspace(-.2,pi*1.7,56)]
    line("Ear helix",ep,earskin,.0022,head)
    cx=s*EC;vs=[(cx,eye_y(s,cx,EZ),EZ)];fs=[];nr=14
    for i in range(1,nr+1):
        r=i/nr
        for j in range(BN):
            x,z=eye_xz(s,2*pi*j/BN);x=cx+(x-cx)*r;z=EZ+(z-EZ)*r
            vs.append((x,eye_y(s,x,z),z))
    fs.extend((0,1+j,1+(j+1)%BN) for j in range(BN))
    for i in range(nr-1):
        for j in range(BN):
            k=1+i*BN+j;q=1+i*BN+(j+1)%BN;fs.append((k,k+BN,q+BN,q))
    eyemat=sclera.copy();eyemat.name="Eye whites - subtle lid occlusion "+str(s)
    nt=eyemat.node_tree;cn=nt.nodes.new("ShaderNodeVertexColor");cn.layer_name="Col"
    nt.links.new(cn.outputs["Color"],nt.nodes.get("Principled BSDF").inputs["Base Color"])
    ob=mesh("Curved almond eye white "+str(s),vs,fs,eyemat,parent=head);cc=[]
    for x,y,z in vs:
        u=(x-cx)/EW;mid=EZ+.0015*s*u;hh=max(.00015,(.0070 if z>=mid else .0042)*max(0,1-u*u)**.59)
        v=(z-mid)/hh;shade=(1-.28*abs(u)**3)*(1-.27*max(0,v)**2)
        col=np.array([.36,.348,.326])*shade;cc.append((*col,1))
    ca=ob.data.color_attributes.new(name="Col",type="FLOAT_COLOR",domain="POINT");ca.data.foreach_set("color",np.array(cc,dtype=np.float32).ravel())
    icz=EZ+.0018
    def clipped_iris_z(x,z):
        u=(x-cx)/EW;h=max(0,1-u*u)**.59;mid=EZ+.0015*s*u
        return max(mid-.0042*h+.0001,min(mid+.0070*h-.0001,z))
    for rad,mat,off in [(.0097,pupilmat,.00045),(.0092,irismat,.00065),(.0040,pupilmat,.00085)]:
        vs=[(cx,eye_y(s,cx,icz)-off,icz)];fs=[];nrad=16;na=96
        for i in range(1,nrad+1):
            r=i/nrad
            for j in range(na):
                a=2*pi*j/na;bx=cx+rad*cos(a);bz=clipped_iris_z(bx,icz+rad*sin(a))
                x=cx+(bx-cx)*r;z=icz+(bz-icz)*r;vs.append((x,eye_y(s,x,z)-off,z))
        fs.extend((0,1+j,1+(j+1)%na) for j in range(na))
        for i in range(nrad-1):
            for j in range(na):k=1+i*na+j;q=1+i*na+(j+1)%na;fs.append((k,k+na,q+na,q))
        mesh("Tessellated curved iris "+str(s),vs,fs,mat,parent=head)
    for k in range(48):
        a=2*pi*k/48;pp=[]
        for r in np.linspace(.004,.0075,5):
            x=cx+r*cos(a);z=clipped_iris_z(x,icz+r*sin(a));pp.append((x,eye_y(s,x,z)-.00076,z))
        line("Fine iris fibres",pp,irislight,.000045,head)
    for dx,dz,rr in [(-.0023,.0032,.0009),(.0016,-.0008,.00028)]:
        x=cx+dx;z=EZ+dz;uvball("Eye catchlight",(x,eye_y(s,x,z)-.0010,z),(rr,.00015,rr),highlight,head,20,12)
    edge=[]
    for a in np.linspace(0,pi,65):
        x,z=eye_xz(s,float(a));edge.append((x,eye_y(s,x,z)-.00035,z))
    line("Tapered upper lash margin",edge,browmat,.00056,head,[.13+.87*sin(pi*j/64)**.75 for j in range(65)])
    for k in range(12):
        j=8+k*4;x,y,z=edge[j]
        line("Fine upper lashes",[(x,y,z),(x+s*.0005,y-.0008,z+.0006),(x+s*.0008,y-.0011,z+.0010)],browmat,.000075,head,[.8,.5,.04])
    for k in range(58):
        t=-.95+1.9*k/57;x=cx+.024*t;z=.039+.005*(1-t*t)+.0012*s*t+random.uniform(-.001,.001)
        pp=[(x,face_y(x,z)-.00023,z),(x+s*.0007,face_y(x+s*.0007,z+.0012)-.00025,z+.0012)]
        line("Natural brow filaments",pp,hairmats[k%3],.00007,head,[.65,.06])
    nostrilmat=material("Nostril inner tissue "+str(s),(.085,.030,.021),.66)
    vs=[(s*.0115,face_y(s*.0115,-.033)+.0055,-.034)];fs=[];nr=8;na=BN
    for i in range(1,nr+1):
        r=i/nr
        for j in range(na):
            x,z=nostril_xz(s,2*pi*j/na);x=s*.0115+(x-s*.0115)*r;z=-.034+(z+.034)*r
            y=face_y(x,z)-.0006+.006*(1-r)**.8;vs.append((x,y,z))
    fs.extend((0,1+j,1+(j+1)%na) for j in range(na))
    for i in range(nr-1):
        for j in range(na):k=1+i*na+j;q=1+i*na+(j+1)%na;fs.append((k,k+na,q+na,q))
    mesh("Recessed anatomical nostril "+str(s),vs,fs,nostrilmat,parent=head)
    innerx=cx-s*EW*.96;innerz=EZ-.0013
    uvball("Tear duct "+str(s),(innerx,eye_y(s,innerx,innerz)-.0002,innerz),(.00075,.00028,.00055),lips,head,16,10)
markmat=material("Subtle natural skin pigment",(.19,.088,.059),.85)
for x,z,r in [(-.057,-.040,.00060),(-.011,.003,.00047),(.046,-.025,.00052)]:
    uvball("Facial pigment detail",(x,face_y(x,z)-.00012,z),(r,.00007,r),markmat,head,16,10)
# Recessed oral volume connected to the inner lip, not a dark plane floating on skin.
vs=[(0,face_y(0,-.060)+.015,-.060)];fs=[];nr=12
for i in range(1,nr+1):
    r=i/nr
    for j in range(BN):
        x,z=mouth_xz(2*pi*j/BN);x*=r;z=-.060+(z+.060)*r
        y=face_y(x,z)-.0008+.016*(1-r)**.8;vs.append((x,y,z))
fs.extend((0,1+j,1+(j+1)%BN) for j in range(BN))
for i in range(nr-1):
    for j in range(BN):k=1+i*BN+j;q=1+i*BN+(j+1)%BN;fs.append((k,k+BN,q+BN,q))
mesh("Smile - fitted oral cavity",vs,fs,oral,parent=head)
teeth.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.31
teeth.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(.70,.68,.60,1)
widths=[.0047,.0058,.0067,.0076,.0076,.0067,.0058,.0047]
heights=[.0074,.0090,.0103,.0117,.0117,.0103,.0090,.0074]
left=-(sum(widths)+.00012*7)/2
for idx,(w,h) in enumerate(zip(widths,heights)):
    x=left+w/2;left+=w+.00012;top=-.050-.004*(x/MW)**2
    zc=top-.00025-h/2;yc=face_y(x,zc)+.00015
    vs=[(x,yc-.0014,zc)];fs=[];nt=40;nr=9
    for rr in np.linspace(1/nr,1,nr):
        r=float(rr)
        for a in np.linspace(0,2*pi,nt,endpoint=False):
            xx=.5*w*math.copysign(abs(cos(a))**.55,cos(a))*r
            zz=.5*h*math.copysign(abs(sin(a))**.55,sin(a))*r
            yy=yc-.0014*sqrt(max(0,1-r*r));vs.append((x+xx,yy,zc+zz))
    fs.extend((0,1+j,1+(j+1)%nt) for j in range(nt))
    for i in range(nr-1):
        for j in range(nt):k=1+i*nt+j;q=1+i*nt+(j+1)%nt;fs.append((k,k+nt,q+nt,q))
    mesh("Individually shaped upper tooth "+str(idx),vs,fs,teeth,parent=head)
print("PORTRAIT_DETAILS_COMPLETE",flush=True)
