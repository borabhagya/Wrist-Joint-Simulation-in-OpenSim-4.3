"""Joint reaction forces/moments (radiocarpal, wrist_hand) for the six SO runs, plus agreement test against OpenSim's JointReaction analysis."""
from common import *
from jr import *
import pandas as pd, sys
RUNS=[("dyn_flexext","L00_unloaded",(0,0,0)),("dyn_flexext","Lflex5N_dorsal",(0,0,5)),("dyn_flexext","Lflex10N_dorsal",(0,0,10)),("dyn_flexext","Lflex20N_dorsal",(0,0,20)),("dyn_dev","L00_unloaded",(0,0,0)),("dyn_dev","Ldev10N_down",(0,-10,0))]
m,s=load(WORK); stride=2
for kin,ld,Fe in RUNS:
    tag=f"SO_{kin}__{ld}"; F=read_storage(f"{OSF}/results_SO/{tag}_StaticOptimization_force.sto"); K=read_storage(f"{OSF}/{kin}.mot")
    idx=list(range(0,len(F),stride)); mus=[x.getName() for x in m.getMuscles()]
    # COM accelerations (finite difference of kinematics) for linear inertial terms
    names=sorted(HAND|{"proximal_row"}); com=np.zeros((len(K),len(names),3))
    for n,(_,k) in enumerate(K.iterrows()):
        set_pose(m,s,k["flexion"],k["deviation"])
        for b,nm in enumerate(names): B=m.getBodySet().get(nm); com[n,b]=v3(B.findStationLocationInGround(s,B.getMassCenter()))
    dt=K.time.iloc[1]-K.time.iloc[0]; acc=np.gradient(np.gradient(com,dt,axis=0),dt,axis=0)
    rows=[]
    for j in idx:
        k=K.iloc[j]; set_pose(m,s,k["flexion"],k["deviation"]); m.realizeDynamics(s)
        T={n:F[n].iloc[j] for n in mus}; a={nm:acc[j,b] for b,nm in enumerate(names)}
        res,Rm=reactions(m,s,T,Fe,acc=a); row=dict(time=F.time.iloc[j],flexion_deg=np.degrees(k["flexion"]),deviation_deg=np.degrees(k["deviation"]))
        for jn,(Fg,Mg,c) in res.items():
            fr=to_radius(Fg,Rm); mr=to_radius(Mg,Rm)
            for ax,v in zip("xyz",fr): row[f"{jn}_F{ax}_N"]=v
            for ax,v in zip("xyz",mr): row[f"{jn}_M{ax}_Nm"]=v
            row[f"{jn}_Fres_N"]=np.linalg.norm(fr); row[f"{jn}_Mres_Nm"]=np.linalg.norm(mr)
            row[f"{jn}_F_axial_compressive_N"]=-fr[1]   # along the forearm long axis (radius -y points distally): force of radius/carpus on distal bone pushing distally = compression
        rows.append(row)
    R=pd.DataFrame(rows); R.to_csv(f"{CSV}/JR_{kin}__{ld}.csv",index=False); print(tag,"peak wrist_hand F (N):",R.wrist_hand_Fres_N.max().round(1),"peak radiocarpal F:",R.radiocarpal_Fres_N.max().round(1),"peak M (N m):",R.radiocarpal_Mres_Nm.max().round(3))
