"""Independent check of Inverse Dynamics at zero-velocity/zero-acceleration waypoints: virtual-work statics
   tau_q = d/dq [ sum m_i g.x_com,i + F.x_p ] , required muscle generalized force = -tau_q   (finite differences, constraints assembled)."""
from common import *
import pandas as pd
m,s=load(WORK); g=np.array(v3(m.getGravity())); pt=osim.Vec3(0.0002,-0.0263,0.0018)
bodies=[(b.getName(),b.getMass(),b.getMassCenter()) for b in m.getBodySet() if b.getMass()>0]
def geom(f,d):
    set_pose(m,s,f,d)
    mc=sum(mass*np.array(v3(m.getBodySet().get(n).findStationLocationInGround(s,c))) for n,mass,c in bodies)
    p=np.array(v3(m.getBodySet().get("thirdmc").findStationLocationInGround(s,pt))); return mc,p
def tau(f,d,coord,Fv):
    h=1e-5; a,b=(geom(f+h,d),geom(f-h,d)) if coord=="flexion" else (geom(f,d+h),geom(f,d-h))
    return g@((a[0]-b[0])/(2*h)) + np.array(Fv)@((a[1]-b[1])/(2*h))
LOADS={"L00_unloaded":(0,0,0),"Ldev5N_down":(0,-5,0),"Ldev10N_down":(0,-10,0),"Lflex5N_dorsal":(0,0,5),"Lflex10N_dorsal":(0,0,10),"Lflex20N_dorsal":(0,0,20)}
rows=[]
for kin,col in (("dyn_flexext","flexion"),("dyn_dev","deviation")):
    K=read_storage(f"{OSF}/{kin}.mot")
    for ln,F in LOADS.items():
        I=pd.read_csv(f"{CSV}/ID_{kin}__{ln}.csv")
        for tw in (0,2,4,6,8):
            k=K.iloc[(K.time-tw).abs().argmin()]; i=I.iloc[(I.time-tw).abs().argmin()]
            for c in ("flexion","deviation"):
                ref=-tau(k["flexion"],k["deviation"],c,F); idv=i[f"{c}_moment_Nm"]
                rows.append(dict(kinematics=kin,load=ln,t_s=tw,flex_deg=np.degrees(k["flexion"]),dev_deg=np.degrees(k["deviation"]),coordinate=c,ID_Nm=idv,virtual_work_Nm=ref,abs_err_Nm=abs(idv-ref)))
V=pd.DataFrame(rows); V.to_csv(f"{TAB}/id_verification_virtual_work.csv",index=False)
print("max |ID - virtual work| over", len(V),"checks (N m):",V.abs_err_Nm.max().round(4)," median:",V.abs_err_Nm.median().round(5))
print(V.sort_values("abs_err_Nm",ascending=False).head(5).round(4).to_string())
# analytic external torque tau = r x F  vs  ID(loaded) - ID(unloaded) at neutral
set_pose(m,s,0,0); ax_flex=None
for c,coordname in (("flexion","flexion"),):
    f0=-tau(0,0,"flexion",(0,0,10))+tau(0,0,"flexion",(0,0,0)); print("external-load torque about flexion axis at neutral for 10 N dorsal force (virtual work, N m):",round(f0,4))
