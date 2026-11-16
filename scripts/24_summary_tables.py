"""Collect the numbers used in the report into results/tables/*.csv and results/report_data.json (every report number is traceable to a CSV)."""
from common import *
import pandas as pd, json
out={}
rows=[]
for c in ["baseline","flexion","extension","radial","ulnar"]:
    D=pd.read_csv(f"{CSV}/FD_{c}.csv"); J=pd.read_csv(f"{CSV}/JR_FD_{c}.csv"); K=pd.read_csv(f"{CSV}/FD_check_{c}.csv").iloc[0]; co="flexion" if c in ("flexion","extension","baseline") else "deviation"
    q=np.degrees(D[f"{co}_rad"]); i=q.abs().idxmax(); ax="flex" if co=="flexion" else "dev"
    rows.append(dict(case=c,primary_coordinate=co,peak_excursion_deg=q[i],t_peak_s=D.time[i],peak_vel_deg_s=np.degrees(D[f"{co}_vel"].abs().max()),peak_acc_deg_s2=np.degrees(D[f"{co}_acc"].abs().max()),
       peak_six_muscle_force_N=D[[f"F_{m}" for m in WRIST_MUSCLES]].sum(axis=1).max(),peak_muscle_moment_Nm=D[f"Mmuscle_{ax}_Nm"].abs().max(),peak_passive_limit_Nm=max(D.lig_flex_Nm.abs().max(),D.lig_dev_Nm.abs().max()),
       peak_other_axis_deg=np.degrees(D[("deviation_rad" if co=="flexion" else "flexion_rad")].abs().max()),peak_wrist_hand_F_N=J.wrist_hand_Fres_N.max(),peak_radiocarpal_F_N=J.radiocarpal_Fres_N.max(),peak_radiocarpal_M_Nm=J.radiocarpal_Mres_Nm.max(),
       FD_to_ID_rms_err_primary_Nm=K[f"{ax}_rms_err_Nm"],FD_to_ID_max_err_primary_Nm=K[f"{ax}_max_err_Nm"]))
pd.DataFrame(rows).to_csv(f"{TAB}/forward_dynamics_summary.csv",index=False); out["fd"]=rows
rows=[]
for kin,ld in [("dyn_flexext","L00_unloaded"),("dyn_flexext","Lflex5N_dorsal"),("dyn_flexext","Lflex10N_dorsal"),("dyn_flexext","Lflex20N_dorsal"),("dyn_dev","L00_unloaded"),("dyn_dev","Ldev10N_down")]:
    J=pd.read_csv(f"{CSV}/JR_{kin}__{ld}.csv"); ID=pd.read_csv(f"{CSV}/ID_{kin}__{ld}.csv")
    rows.append(dict(kinematics=kin,load=ld,peak_ID_flexion_Nm=ID.flexion_moment_Nm.abs().max(),peak_ID_deviation_Nm=ID.deviation_moment_Nm.abs().max(),peak_wrist_hand_F_N=J.wrist_hand_Fres_N.max(),min_wrist_hand_F_N=J.wrist_hand_Fres_N.min(),peak_radiocarpal_F_N=J.radiocarpal_Fres_N.max(),peak_radiocarpal_M_Nm=J.radiocarpal_Mres_Nm.max(),peak_axial_compressive_radiocarpal_N=J.radiocarpal_F_axial_compressive_N.max()))
pd.DataFrame(rows).to_csv(f"{TAB}/joint_reaction_summary.csv",index=False); out["jr"]=rows
# per-movement SO peaks (10 N loads)
rows=[]
for mv,kin,ld,seg in (("flexion","dyn_flexext","Lflex10N_dorsal",(0,4)),("extension","dyn_flexext","Lflex10N_dorsal",(4,8)),("radial","dyn_dev","Ldev10N_down",(0,4)),("ulnar","dyn_dev","Ldev10N_down",(4,8))):
    t=f"SO_{kin}__{ld}"; F=read_storage(f"{OSF}/results_SO/{t}_StaticOptimization_force.sto"); A=read_storage(f"{OSF}/results_SO/{t}_StaticOptimization_activation.sto")
    s=(F.time>=seg[0]-1e-9)&(F.time<=seg[1]+1e-9); r=dict(movement=mv,load=ld)
    for m in WRIST_MUSCLES: r[f"{m}_peak_act"]=A[m][s].max(); r[f"{m}_peak_F_N"]=F[m][s].max()
    rows.append(r)
pd.DataFrame(rows).to_csv(f"{TAB}/so_movement_peaks.csv",index=False)
out["so_mv"]=rows; json.dump(out,open(f"{ROOT}/results/report_data.json","w"),indent=1,default=float)
pd.set_option("display.width",250,"display.max_columns",30)
for n in ("forward_dynamics_summary","joint_reaction_summary","so_movement_peaks"): print(n); print(pd.read_csv(f"{TAB}/{n}.csv").round(2).T.to_string())
