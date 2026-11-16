from common import *
import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from render import MCOL
plt.rcParams.update({"font.size":9,"axes.grid":True,"grid.alpha":0.3,"figure.dpi":150,"savefig.bbox":"tight"})
Df=pd.read_csv(f"{CSV}/momentarm_vs_flexion.csv"); Dd=pd.read_csv(f"{CSV}/momentarm_vs_deviation.csv")
fig,ax=plt.subplots(1,2,figsize=(11,4.2))
for mu in WRIST_MUSCLES:
    ax[0].plot(Df.q_deg,Df[f"{mu}_r"]*1000,color=MCOL[mu],label=mu); ax[1].plot(Dd.q_deg,Dd[f"{mu}_r"]*1000,color=MCOL[mu],label=mu)
ax[0].set_xlabel("flexion angle (deg)  [+ flexion, - extension]"); ax[0].set_ylabel("moment arm about flexion axis (mm)\n[+ flexor, - extensor]")
ax[0].set_title("Moment arms vs flexion (deviation = 0)"); ax[0].axhline(0,color="k",lw=.6); ax[0].axvline(0,color="k",lw=.6); ax[0].legend(ncol=2,fontsize=8)
ax[1].set_xlabel("deviation angle (deg)  [+ ulnar, - radial]"); ax[1].set_ylabel("moment arm about deviation axis (mm)\n[+ ulnar, - radial]")
ax[1].set_title("Moment arms vs deviation (flexion = 0)"); ax[1].axhline(0,color="k",lw=.6); ax[1].axvline(0,color="k",lw=.6)
fig.savefig(f"{FIG}/M_momentarms_wrist_muscles.png"); plt.close(fig)
# individual requested plots
for mu_group,fn,t in [(["FCR"],"FCR","FCR"),(["FCU"],"FCU","FCU"),(["ECRL","ECRB"],"ECR","ECRL / ECRB"),(["ECU"],"ECU","ECU")]:
    fig,ax=plt.subplots(figsize=(5,3.6))
    for mu in mu_group: ax.plot(Df.q_deg,Df[f"{mu}_r"]*1000,color=MCOL[mu],label=mu)
    ax.set_xlabel("flexion angle (deg)"); ax.set_ylabel("moment arm (mm)"); ax.set_title(f"{t}: flexion-axis moment arm"); ax.axhline(0,color="k",lw=.6); ax.legend(); fig.savefig(f"{FIG}/M_momentarm_{fn}_vs_flexion.png"); plt.close(fig)
# MTU lengths
fig,ax=plt.subplots(1,2,figsize=(11,3.8))
for mu in WRIST_MUSCLES:
    ax[0].plot(Df.q_deg,(Df[f"{mu}_L"]-Df[f"{mu}_L"].iloc[np.argmin(abs(Df.q_deg))])*1000,color=MCOL[mu],label=mu)
    ax[1].plot(Dd.q_deg,(Dd[f"{mu}_L"]-Dd[f"{mu}_L"].iloc[np.argmin(abs(Dd.q_deg))])*1000,color=MCOL[mu],label=mu)
ax[0].set_xlabel("flexion (deg)"); ax[0].set_ylabel("change in MTU length from neutral (mm)"); ax[0].set_title("MTU length change vs flexion"); ax[0].legend(ncol=2,fontsize=8)
ax[1].set_xlabel("deviation (deg)"); ax[1].set_ylabel("change in MTU length from neutral (mm)"); ax[1].set_title("MTU length change vs deviation")
fig.savefig(f"{FIG}/M_mtu_length_change.png"); plt.close(fig)
# neutral 2-axis moment-arm bar
r0=pd.read_csv(f"{TAB}/neutral_moment_arms.csv"); x=np.arange(len(r0)); fig,ax=plt.subplots(figsize=(6,3.6))
ax.bar(x-0.2,r0.r_flexion_neutral_mm,0.4,label="flexion axis"); ax.bar(x+0.2,r0.r_deviation_neutral_mm,0.4,label="deviation axis")
ax.set_xticks(x); ax.set_xticklabels(r0.muscle); ax.axhline(0,color="k",lw=.6); ax.set_ylabel("moment arm at neutral (mm)"); ax.set_title("Two-axis action of wrist muscles (neutral)"); ax.legend(); fig.savefig(f"{FIG}/M_neutral_two_axis.png"); plt.close(fig)
# passive torque
F=pd.read_csv(f"{CSV}/passive_flexion_ligament_torque.csv"); Dv=pd.read_csv(f"{CSV}/passive_deviation_ligament_torque.csv")
fig,ax=plt.subplots(1,2,figsize=(10,3.6)); ax[0].plot(F.q_deg,F.torque_Nm); ax[0].set_xlabel("flexion (deg)"); ax[0].set_ylabel("passive limit torque (N m)"); ax[0].set_title("flexion_ligaments")
ax[1].plot(Dv.q_deg,Dv.torque_Nm); ax[1].set_xlabel("deviation (deg)"); ax[1].set_title("deviation_ligaments"); fig.savefig(f"{FIG}/M_passive_limit_torque.png"); plt.close(fig)
# summary table: moment arms at neutral, extremes
rows=[]
for mu in WRIST_MUSCLES:
    r=Df[f"{mu}_r"]*1000; d=Dd[f"{mu}_r"]*1000
    rows.append(dict(muscle=mu,r_flex_neutral=r[np.argmin(abs(Df.q_deg))],r_flex_min=r.min(),r_flex_max=r.max(),r_flex_at_m60=np.interp(-60,Df.q_deg,r),r_flex_at_p60=np.interp(60,Df.q_deg,r),
       r_dev_neutral=d[np.argmin(abs(Dd.q_deg))],r_dev_min=d.min(),r_dev_max=d.max()))
T=pd.DataFrame(rows); T.to_csv(f"{TAB}/momentarm_summary.csv",index=False); print(T.round(1).to_string())
