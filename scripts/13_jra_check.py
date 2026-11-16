"""Validity check of the JointReaction analysis: with ALL muscle forces set to zero and no external load, the force transmitted by the wrist_hand joint
   to the capitate (carrying every distal body) must balance the weight of the distal segment: F = -m_dist * g (static)."""
from common import *
import pandas as pd; from importlib import import_module
J=import_module("12_jra")
F=read_storage(f"{OSF}/results_SO/SO_dyn_flexext__L00_unloaded_StaticOptimization_force.sto")
for c in F.columns[1:]: F[c]=0.0
F=F[F.time<=0.5]; zf=f"{OSF}/results_SO/zero_forces.sto"; write_storage(zf,"zero",list(F.columns),F.values)
J.run_jra("dyn_flexext","L00_unloaded","zero","%s"%zf,"JRA_zeroforce_check",final=0.5)
D=read_storage(f"{OSF}/results_JRA/JRA_zeroforce_check_JRA_ReactionLoads.sto"); r=D.iloc[0]
m,s=load(WORK); set_pose(m,s)
dist=["capitate","trapezium","trapezoid","hamate","firstmc1","firstmc","proximal_thumb","distal_thumb","secondmc","thirdmc","fourthmc","fifthmc"]+[f"{d}{p}" for d in "2345" for p in ("proxph","midph","distph")]
mass=sum(m.getBodySet().get(b).getMass() for b in dist); W=mass*9.80665
R=np.array([r["wrist_hand_on_capitate_in_radius_f"+a] for a in "xyz"]); 
# gravity direction expressed in radius frame
rad=m.getBodySet().get("radius"); Rm=rad.getTransformInGround(s).R(); Rm=np.array([[Rm.get(i,j) for j in range(3)] for i in range(3)]); gdir=Rm.T@np.array([0,-1,0])
res=pd.DataFrame([dict(distal_mass_kg=mass,weight_N=W,JRA_force_N=np.linalg.norm(R),JRA_fx=R[0],JRA_fy=R[1],JRA_fz=R[2],expected_fx=-W*gdir[0],expected_fy=-W*gdir[1],expected_fz=-W*gdir[2],rel_err=np.linalg.norm(R-(-W*gdir))/W)])
res.to_csv(f"{TAB}/jra_zero_force_check.csv",index=False); print(res.round(4).T.to_string())
