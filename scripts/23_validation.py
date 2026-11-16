"""Plausibility comparison with published values (NOT a validation against experimental data of the same subjects):
 (1) model maximum isometric wrist moments at neutral (all agonist muscles at full activation, tendon-compliant equilibrium) vs Delp et al. 1996;
 (2) passive limit torque at the range-of-motion ends vs Delp et al. 1996; (3) coordinate ranges vs Ryu et al. 1991."""
from common import *
import pandas as pd
m,s=load(WORK); cs=m.getCoordinateSet(); mus=list(m.getMuscles())
def moments(act):
    for mu in mus: osim.Millard2012EquilibriumMuscle.safeDownCast(mu).setActivation(s,act[mu.getName()])
    set_pose(m,s,0,0); m.equilibrateMuscles(s); m.realizePosition(s); m.realizeDynamics(s); out={}
    for c in ("flexion","deviation"): out[c]=sum(mu.getTendonForce(s)*mu.computeMomentArm(s,cs.get(c)) for mu in mus)
    return out
set_pose(m,s,0,0); ra={mu.getName():(mu.computeMomentArm(s,cs.get("flexion")),mu.computeMomentArm(s,cs.get("deviation"))) for mu in mus}
rest={mu.getName():0.01 for mu in mus}; M0=moments(rest); rows=[]
for nm,ax,sg in (("flexion","flexion",+1),("extension","flexion",-1),("ulnar deviation","deviation",+1),("radial deviation","deviation",-1)):
    idx=0 if ax=="flexion" else 1; act=dict(rest)
    for k,v in ra.items():
        if sg*v[idx]>1e-3 and (sg*v[idx]>abs(v[1-idx])*0.0): act[k]=1.0     # all muscles whose primary action about this axis is in the movement direction
    M=moments(act); rows.append(dict(movement=nm,model_max_isometric_moment_Nm=sg*(M[ax]-M0[ax]),n_muscles_activated=sum(1 for k in act if act[k]==1.0)))
# six primary wrist muscles only
rows6=[]
for nm,ax,sg in (("flexion","flexion",+1),("extension","flexion",-1),("ulnar deviation","deviation",+1),("radial deviation","deviation",-1)):
    idx=0 if ax=="flexion" else 1; act=dict(rest)
    for k in WRIST_MUSCLES:
        if sg*ra[k][idx]>1e-3: act[k]=1.0
    M=moments(act); rows6.append(sg*(M[ax]-M0[ax]))
R=pd.DataFrame(rows); R["model_six_wrist_muscles_only_Nm"]=rows6; ref={"flexion":(12.2,3.7),"extension":(7.1,2.1),"radial deviation":(11.0,2.0),"ulnar deviation":(9.5,2.2)}
R["Delp1996_mean_Nm"]=[ref[x][0] for x in R.movement]; R["Delp1996_SD_Nm"]=[ref[x][1] for x in R.movement]; R["model_over_mean"]=R.model_max_isometric_moment_Nm/R.Delp1996_mean_Nm
R.to_csv(f"{TAB}/validation_max_isometric_moments.csv",index=False); print(R.round(2).to_string())
F=pd.read_csv(f"{CSV}/passive_flexion_ligament_torque.csv"); D=pd.read_csv(f"{CSV}/passive_deviation_ligament_torque.csv")
P=pd.DataFrame([dict(item="flexion +70 deg",model_Nm=float(np.interp(70,F.q_deg,F.torque_Nm))),dict(item="extension -70 deg",model_Nm=float(np.interp(-70,F.q_deg,F.torque_Nm))),
  dict(item="radial -10 deg",model_Nm=float(np.interp(-10,D.q_deg,D.torque_Nm))),dict(item="ulnar +25 deg",model_Nm=float(np.interp(25,D.q_deg,D.torque_Nm))),dict(item="flexion +60 deg",model_Nm=float(np.interp(60,F.q_deg,F.torque_Nm))),dict(item="extension -60 deg",model_Nm=float(np.interp(-60,F.q_deg,F.torque_Nm)))])
P.to_csv(f"{TAB}/validation_passive_limit_torque.csv",index=False); print(P.round(2).to_string())
