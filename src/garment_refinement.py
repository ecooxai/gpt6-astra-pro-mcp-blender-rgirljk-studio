"""Original curved collar panels, neck stand and tailored seam details."""
# A real collar stand wraps around the neck; the front opening remains open.
V=[];F=[];nt=96
for j,theta in enumerate(np.linspace(.85,2*pi-.85,nt)):
    t=float(theta)
    for k,v in enumerate(np.linspace(0,1,7)):
        V.append((.005+.043*sin(t),.010-.043*cos(t),1.368+.020*float(v)+.001*cos(t)-.005*max(0,cos(t))**2))
for j in range(nt-1):
    for k in range(6):i=j*7+k;F.append((i,i+7,i+8,i+1))
stand=mesh("Collar - continuous curved neck stand",V,F,white)
m=stand.modifiers.new("Cotton stand thickness","SOLIDIFY");m.thickness=.0015
for s in [-1,1]:
    p0=Vector((s*.037,-.020,1.389));p1=Vector((s*.063,-.035,1.369))
    p2=Vector((s*.025,-.078,1.342));p3=Vector((s*.079,-.083,1.313))
    V=[];F=[];uv=[];nu=24;nv=32
    for i,v in enumerate(np.linspace(0,1,nv)):
        v=float(v)
        for j,u in enumerate(np.linspace(0,1,nu)):
            u=float(u);p=(1-v)*((1-u)*p0+u*p1)+v*((1-u)*p2+u*p3)
            p.y-=.0040*sin(pi*u)*sin(pi*v);p.z+=.0018*sin(pi*u)*(1-v);p.y+=.0015*u*u*v**4
            V.append(p);uv.append((u,v))
    for i in range(nv-1):
        for j in range(nu-1):k=i*nu+j;F.append((k,k+nu,k+nu+1,k+1))
    ob=mesh("Collar - softly curved lapel "+str(s),V,F,white,uv=uv)
    m=ob.modifiers.new("Cotton collar thickness","SOLIDIFY");m.thickness=.0016
    m=ob.modifiers.new("Soft turned collar edge","BEVEL");m.width=.00065;m.segments=2
    # Topstitch follows the actual curved surface instead of floating above a flat polygon.
    paths=[[V[j] for j in range(nu)],[V[i*nu+nu-1] for i in range(nv)],[V[(nv-1)*nu+j] for j in range(nu-1,-1,-1)]]
    for pp in paths:line("Collar fine topstitch",[v+Vector((0,-.0009,0)) for v in pp],seamwhite,.00022)
    pp=[(s*(.127+.033*t),-.043+.092*t,1.343-.017*sin(pi*t)) for t in np.linspace(0,1,32)]
    line("Shoulder seams",pp,seamwhite,.00035)
# Polished, not metallic, loafer finish.
p=leather.node_tree.nodes.get("Principled BSDF");p.inputs["Coat Weight"].default_value=.32;p.inputs["Coat Roughness"].default_value=.19;p.inputs["Roughness"].default_value=.25
print("CURVED_COLLAR_AND_CHEST_READY",flush=True)
