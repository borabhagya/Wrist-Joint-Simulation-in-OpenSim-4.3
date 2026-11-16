"""Passive wrist torques from the model's CoordinateLimitForce elements (flexion_ligaments, deviation_ligaments, damping)."""
from common import *
import pandas as pd
m, s = load()
lig = {n: osim.CoordinateLimitForce.safeDownCast(m.getForceSet().get(n)) for n in ["flexion_ligaments","deviation_ligaments"]}
rows=[]
for q in np.radians(np.arange(-70,70.1,2)):
    set_pose(m, s, flexion=q); rows.append(dict(q_deg=np.degrees(q), torque_Nm=lig["flexion_ligaments"].calcLimitForce(s)))
F=pd.DataFrame(rows); F.to_csv(f"{CSV}/passive_flexion_ligament_torque.csv",index=False)
rows=[]
for q in np.radians(np.arange(-10,25.1,1)):
    set_pose(m, s, deviation=q); rows.append(dict(q_deg=np.degrees(q), torque_Nm=lig["deviation_ligaments"].calcLimitForce(s)))
Dv=pd.DataFrame(rows); Dv.to_csv(f"{CSV}/passive_deviation_ligament_torque.csv",index=False)
print("flexion ligament torque, selected (deg: Nm):", {int(r.q_deg):round(r.torque_Nm,3) for r in F.itertuples() if int(r.q_deg) in (-70,-60,-50,-40,0,40,50,60,70)})
print("deviation ligament torque, selected:", {int(r.q_deg):round(r.torque_Nm,3) for r in Dv.itertuples() if int(r.q_deg) in (-10,-6,0,10,20,25)})
for n in ["flexion_ligaments","deviation_ligaments"]:
    l=lig[n]; print(n,"lower/upper limit(raw prop):",l.get_lower_limit(),l.get_upper_limit(),"transition:",l.get_transition(),"stiff:",l.get_lower_stiffness(),l.get_upper_stiffness())
