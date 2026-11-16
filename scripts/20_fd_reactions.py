"""Joint reactions (radiocarpal, wrist_hand) for the forward-dynamics runs: Newton-Euler balance with the ACTUAL simulated accelerations (finite difference of COM motion)."""
from common import *
from jr import *
import pandas as pd, sys
m,s=load(WORK); mus=[x.getName() for x in m.getMuscles()]; names=sorted(HAND|{"proximal_row"})
for c in sys.argv[1].split(","):
    D=pd.read_csv(f"{CSV}/FD_{c}.csv"); com=np.zeros((len(D),len(names),3))
    qcols=[x for x in D.columns if x.startswith("q_")]
    for n in range(len(D)):
        set_pose(m,s,D.flexion_rad[n],D.deviation_rad[n])
        for b,nm in enumerate(names): B=m.getBodySet().get(nm); com[n,b]=v3(B.findStationLocationInGround(s,B.getMassCenter()))
    dt=D.time[1]-D.time[0]; acc=np.gradient(np.gradient(com,dt,axis=0),dt,axis=0); rows=[]
    for n in range(len(D)):
        set_pose(m,s,D.flexion_rad[n],D.deviation_rad[n]); m.realizeDynamics(s); T={x:D[f"F_{x}"][n] for x in mus}
        res,Rm=reactions(m,s,T,(0,0,0),acc={nm:acc[n,b] for b,nm in enumerate(names)}); row=dict(time=D.time[n],flexion_deg=np.degrees(D.flexion_rad[n]),deviation_deg=np.degrees(D.deviation_rad[n]))
        for jn,(Fg,Mg,cc) in res.items():
            fr=to_radius(Fg,Rm); mr=to_radius(Mg,Rm)
            for ax,v in zip("xyz",fr): row[f"{jn}_F{ax}_N"]=v
            for ax,v in zip("xyz",mr): row[f"{jn}_M{ax}_Nm"]=v
            row[f"{jn}_Fres_N"]=np.linalg.norm(fr); row[f"{jn}_Mres_Nm"]=np.linalg.norm(mr); row[f"{jn}_F_axial_compressive_N"]=-fr[1]
        rows.append(row)
    R=pd.DataFrame(rows); R.to_csv(f"{CSV}/JR_FD_{c}.csv",index=False); print(c,"peak wrist_hand F %.1f N, radiocarpal F %.1f N, peak M %.3f N m"%(R.wrist_hand_Fres_N.max(),R.radiocarpal_Fres_N.max(),R.radiocarpal_Mres_Nm.max()))
