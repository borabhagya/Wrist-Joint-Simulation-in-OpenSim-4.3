"""Independent force-balance check of the JRA at wrist_hand (muscle-loaded case, SO forces):
   F_jra(parent->capitate) + m_dist*g + F_ext + sum(muscle path forces acting on distal bodies) = m_dist*a ~ 0   (evaluated at zero-acceleration waypoints)."""
from common import *
import pandas as pd
import sys
TW=[float(x) for x in sys.argv[1].split(",")] if len(sys.argv)>1 else (0,2,4,6,8)
kin,ld="dyn_flexext","Lflex10N_dorsal"; tag=f"SO_{kin}__{ld}"
m,s=load(WORK); g=np.array(v3(m.getGravity()))
F=read_storage(f"{OSF}/results_SO/{tag}_StaticOptimization_force.sto"); J=read_storage(f"{OSF}/results_JRA/JRA_{kin}__{ld}_JRA_ReactionLoads.sto"); K=read_storage(f"{OSF}/{kin}.mot")
dist={"capitate","trapezium","trapezoid","hamate","firstmc1","firstmc","proximal_thumb","distal_thumb","secondmc","thirdmc","fourthmc","fifthmc"}|{f"{d}{p}" for d in "2345" for p in ("proxph","midph","distph")}
mass=sum(m.getBodySet().get(b).getMass() for b in dist); Fext=np.array([0,0,10.0]); rows=[]
for tw in TW:
    k=K.iloc[(K.time-tw).abs().argmin()]; set_pose(m,s,k["flexion"],k["deviation"]); m.realizeDynamics(s)
    f=F.iloc[(F.time-tw).abs().argmin()]; Fm=np.zeros(3)
    for mu in m.getMuscles():
        pts=mu.getGeometryPath().getCurrentPath(s); P=[]; B=[]
        for i in range(pts.getSize()):
            p=pts.get(i); fr=p.getParentFrame(); P.append(np.array(v3(fr.findStationLocationInGround(s,p.getLocation(s))))); B.append(fr.findBaseFrame().getName())
        T=f[mu.getName()]; u=lambda a,b:(b-a)/np.linalg.norm(b-a)
        for i in range(len(P)):
            if B[i] not in dist: continue
            fi=np.zeros(3)
            if i<len(P)-1: fi+=T*u(P[i],P[i+1])
            if i>0: fi-=T*u(P[i-1],P[i])
            Fm+=fi
    j=J.iloc[(J.time-tw).abs().argmin()]; rad=m.getBodySet().get("radius"); R=rad.getTransformInGround(s).R(); Rm=np.array([[R.get(a,b) for b in range(3)] for a in range(3)])
    Fj=Rm@np.array([j["wrist_hand_on_capitate_in_radius_f"+a] for a in "xyz"])
    bal=Fj+mass*g+Fext+Fm
    rows.append(dict(t=tw,JRA_force_ground_x=Fj[0],JRA_y=Fj[1],JRA_z=Fj[2],muscle_on_distal_x=Fm[0],muscle_y=Fm[1],muscle_z=Fm[2],weight_y=mass*g[1],ext_z=Fext[2],residual_N=np.linalg.norm(bal),JRA_magnitude_N=np.linalg.norm(Fj),residual_pct_of_JRA=100*np.linalg.norm(bal)/np.linalg.norm(Fj)))
R=pd.DataFrame(rows); R.to_csv(f"{TAB}/jra_force_balance_check.csv",index=False); print(R.round(3).T.to_string())
