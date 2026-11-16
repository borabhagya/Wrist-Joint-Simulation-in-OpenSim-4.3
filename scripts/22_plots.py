"""Publication figures for the four movements (SO/ID/JR on prescribed synthetic kinematics; FD with explicit excitations) + comparisons + validation + sensitivity."""
from common import *
from render import MCOL
import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.size":8.5,"axes.grid":True,"grid.alpha":0.3,"figure.dpi":150,"savefig.bbox":"tight","axes.titlesize":9})
M6=WRIST_MUSCLES
MOV={"flexion":dict(kin="dyn_flexext",seg=(0,4),coord="flexion",sign=1,load="Lflex10N_dorsal",lab="10 N dorsally-directed force at 3rd MCP",axis="flexion"),
     "extension":dict(kin="dyn_flexext",seg=(4,8),coord="flexion",sign=1,load="Lflex10N_dorsal",lab="10 N dorsally-directed force at 3rd MCP",axis="flexion"),
     "radial":dict(kin="dyn_dev",seg=(0,4),coord="deviation",sign=1,load="Ldev10N_down",lab="10 N downward force at 3rd MCP",axis="deviation"),
     "ulnar":dict(kin="dyn_dev",seg=(4,8),coord="deviation",sign=1,load="Ldev10N_down",lab="10 N downward force at 3rd MCP",axis="deviation")}
def so(kin,ld): 
    t=f"SO_{kin}__{ld}"; return read_storage(f"{OSF}/results_SO/{t}_StaticOptimization_force.sto"),read_storage(f"{OSF}/results_SO/{t}_StaticOptimization_activation.sto")
Mom=pd.read_csv(f"{CSV}/momentarm_vs_flexion.csv"); Momd=pd.read_csv(f"{CSV}/momentarm_vs_deviation.csv")
def seg(df,t0,t1): return df[(df.time>=t0-1e-9)&(df.time<=t1+1e-9)]
for mv,c in MOV.items():
    t0,t1=c["seg"]; traj=pd.read_csv(f"{CSV}/{c['kin']}_trajectory.csv") if os.path.exists(f"{CSV}/{c['kin']}_trajectory.csv") else None
    K=read_storage(f"{OSF}/{c['kin']}.mot"); K=seg(K,t0,t1); q=np.degrees(K[c["coord"]]); tt=K.time-t0
    dt=K.time.iloc[1]-K.time.iloc[0]; w=np.gradient(np.radians(q),dt); al=np.gradient(w,dt)
    F,A=so(c["kin"],c["load"]); F0,A0=so(c["kin"],"L00_unloaded"); F=seg(F,t0,t1); A=seg(A,t0,t1); F0=seg(F0,t0,t1)
    ID=pd.read_csv(f"{CSV}/ID_{c['kin']}__{c['load']}.csv"); ID0=pd.read_csv(f"{CSV}/ID_{c['kin']}__L00_unloaded.csv"); ID=seg(ID.rename(columns={"time":"time"}),t0,t1); ID0=seg(ID0,t0,t1)
    JR=seg(pd.read_csv(f"{CSV}/JR_{c['kin']}__{c['load']}.csv"),t0,t1)
    fig,ax=plt.subplots(3,3,figsize=(13,9.5)); ax=ax.ravel()
    ax[0].plot(tt,q,"C0"); ax[0].set_ylabel(f"{c['coord']} (deg)"); ax[0].set_title(f"{mv}: joint angle (prescribed, synthetic)")
    ax[1].plot(tt,np.degrees(w),"C1"); ax[1].set_ylabel("angular velocity (deg/s)"); ax[1].set_title("angular velocity")
    ax[2].plot(tt,np.degrees(al),"C3"); ax[2].set_ylabel("angular acceleration (deg/s$^2$)"); ax[2].set_title("angular acceleration")
    for m_ in M6: ax[3].plot(F.time-t0,A[m_],color=MCOL[m_],label=m_)
    ax[3].set_ylabel("activation (-)"); ax[3].set_title(f"SO activation ({c['lab']})"); ax[3].legend(ncol=3,fontsize=7)
    for m_ in M6: ax[4].plot(F.time-t0,F[m_],color=MCOL[m_],label=m_)
    ax[4].set_ylabel("tendon force (N)"); ax[4].set_title("SO muscle force (loaded)")
    if c["axis"]=="flexion": D=Mom; col="flexion"
    else: D=Momd; col="deviation"
    for m_ in M6: ax[5].plot(D.q_deg,D[f"{m_}_r"]*1000,color=MCOL[m_],label=m_)
    ax[5].axvspan(min(q),max(q),color="k",alpha=0.08); ax[5].axhline(0,color="k",lw=.5); ax[5].set_xlabel(f"{col} angle (deg)"); ax[5].set_ylabel("moment arm (mm)"); ax[5].set_title("moment arms (shaded = range traversed)")
    ax[6].plot(ID0.time-t0,ID0[f"{c['axis']}_moment_Nm"],"k--",label="unloaded"); ax[6].plot(ID.time-t0,ID[f"{c['axis']}_moment_Nm"],"C0",label="loaded"); ax[6].set_ylabel("net muscle-required moment (N m)"); ax[6].set_title(f"inverse dynamics: {c['axis']} moment"); ax[6].legend()
    ax[7].plot(JR.time-t0,JR.radiocarpal_Fres_N,"C2",label="radiocarpal"); ax[7].plot(JR.time-t0,JR.wrist_hand_Fres_N,"C4",label="wrist_hand (midcarpal)"); ax[7].set_ylabel("resultant reaction force (N)"); ax[7].set_title("joint reaction force (loaded)"); ax[7].legend()
    ax[8].plot(JR.time-t0,JR.radiocarpal_Mres_Nm,"C2",label="radiocarpal"); ax[8].plot(JR.time-t0,JR.wrist_hand_Mres_Nm,"C4",label="wrist_hand"); ax[8].set_ylabel("resultant reaction moment (N m)"); ax[8].set_title("joint reaction moment (loaded)"); ax[8].legend()
    for a in ax: 
        if a is not ax[5]: a.set_xlabel("time (s)")
    fig.suptitle(f"Movement: {mv} (prescribed synthetic kinematics; SO/ID/reaction via Newton-Euler)",y=1.0,fontsize=10); fig.tight_layout(); fig.savefig(f"{FIG}/P_movement_{mv}.png"); plt.close(fig)
# ---------- comparative: kinematics of four movements
fig,ax=plt.subplots(1,3,figsize=(13,3.6)); cols={"flexion":"C3","extension":"C0","radial":"C2","ulnar":"C1"}
for mv,c in MOV.items():
    K=seg(read_storage(f"{OSF}/{c['kin']}.mot"),*c["seg"]); q=np.degrees(K[c["coord"]]); t=K.time-c["seg"][0]; dt=t.iloc[1]-t.iloc[0]; w=np.gradient(q,dt); a=np.gradient(w,dt)
    ax[0].plot(t,q,color=cols[mv],label=mv); ax[1].plot(t,w,color=cols[mv]); ax[2].plot(t,a,color=cols[mv])
ax[0].set_ylabel("angle (deg)"); ax[1].set_ylabel("angular velocity (deg/s)"); ax[2].set_ylabel("angular acceleration (deg/s$^2$)"); ax[0].legend()
for a in ax: a.set_xlabel("time (s)")
fig.suptitle("Four movements: prescribed trajectories (flexion/extension about `flexion`; radial/ulnar about `deviation`)"); fig.savefig(f"{FIG}/C_four_movement_kinematics.png"); plt.close(fig)
# ---------- comparative: peak SO activation & force per wrist muscle per movement (loaded and unloaded)
fig,ax=plt.subplots(1,2,figsize=(12,3.8)); x=np.arange(6); wdt=0.2
for k,(mv,c) in enumerate(MOV.items()):
    F,A=so(c["kin"],c["load"]); F=seg(F,*c["seg"]); A=seg(A,*c["seg"])
    ax[0].bar(x+(k-1.5)*wdt,[A[m_].max() for m_ in M6],wdt,color=cols[mv],label=mv); ax[1].bar(x+(k-1.5)*wdt,[F[m_].max() for m_ in M6],wdt,color=cols[mv])
for a,yl in zip(ax,["peak activation (-)","peak tendon force (N)"]): a.set_xticks(x); a.set_xticklabels(M6); a.set_ylabel(yl)
ax[0].legend(); fig.suptitle("Static Optimization: peak wrist-muscle activation / force per movement (10 N loads)"); fig.savefig(f"{FIG}/C_peak_muscle_by_movement.png"); plt.close(fig)
# ---------- comparative: loading conditions (flexion/extension run)
fig,ax=plt.subplots(2,2,figsize=(11,7)); ax=ax.ravel(); LD=[("L00_unloaded","0 N"),("Lflex5N_dorsal","5 N"),("Lflex10N_dorsal","10 N"),("Lflex20N_dorsal","20 N")]
for ld,lab in LD:
    ID=pd.read_csv(f"{CSV}/ID_dyn_flexext__{ld}.csv"); F,A=so("dyn_flexext",ld); JR=pd.read_csv(f"{CSV}/JR_dyn_flexext__{ld}.csv")
    ax[0].plot(ID.time,ID.flexion_moment_Nm,label=lab); ax[1].plot(A.time,A["FCR"],label=lab); ax[2].plot(F.time,F[M6].sum(axis=1),label=lab); ax[3].plot(JR.time,JR.wrist_hand_Fres_N,label=lab)
for a,t,yl in zip(ax,["inverse-dynamics flexion moment","FCR activation (SO)","summed tendon force, six wrist muscles (SO)","wrist_hand reaction force (resultant)"],["N m","-","N","N"]): a.set_title(t); a.set_ylabel(yl); a.set_xlabel("time (s)  [0-4 s flexion, 4-8 s extension]")
ax[0].legend(title="external force"); fig.suptitle("Effect of external loading (flexion-extension motion)"); fig.tight_layout(); fig.savefig(f"{FIG}/C_loading_comparison.png"); plt.close(fig)
# ---------- forward dynamics figures
FDc={"flexion":"C3","extension":"C0","radial":"C2","ulnar":"C1","baseline":"gray"}
for c in ["flexion","extension","radial","ulnar","baseline"]:
    D=pd.read_csv(f"{CSV}/FD_{c}.csv"); JR=pd.read_csv(f"{CSV}/JR_FD_{c}.csv"); fig,ax=plt.subplots(3,3,figsize=(13,9.5)); ax=ax.ravel()
    ax[0].plot(D.time,np.degrees(D.flexion_rad),"C3",label="flexion"); ax[0].plot(D.time,np.degrees(D.deviation_rad),"C2",label="deviation"); ax[0].set_ylabel("angle (deg)"); ax[0].set_title("forward dynamics: joint angles"); ax[0].legend()
    ax[1].plot(D.time,np.degrees(D.flexion_vel),"C3"); ax[1].plot(D.time,np.degrees(D.deviation_vel),"C2"); ax[1].set_ylabel("angular velocity (deg/s)"); ax[1].set_title("angular velocity")
    ax[2].plot(D.time,np.degrees(D.flexion_acc),"C3"); ax[2].plot(D.time,np.degrees(D.deviation_acc),"C2"); ax[2].set_ylabel("angular acceleration (deg/s$^2$)"); ax[2].set_title("angular acceleration")
    for m_ in M6: ax[3].plot(D.time,D[f"ex_{m_}"],color=MCOL[m_],ls=":"); ax[3].plot(D.time,D[f"act_{m_}"],color=MCOL[m_],label=m_)
    ax[3].set_ylabel("excitation (dotted) / activation"); ax[3].set_title("muscle excitation & activation"); ax[3].legend(ncol=3,fontsize=7)
    for m_ in M6: ax[4].plot(D.time,D[f"F_{m_}"],color=MCOL[m_],label=m_)
    ax[4].set_ylabel("tendon force (N)"); ax[4].set_title("muscle force")
    ax[5].plot(D.time,D.Mmuscle_flex_Nm,"C3",label="muscle, flexion axis"); ax[5].plot(D.time,D.Mmuscle_dev_Nm,"C2",label="muscle, deviation axis"); ax[5].plot(D.time,D.lig_flex_Nm,"C3",ls="--",label="passive limit, flexion"); ax[5].plot(D.time,D.lig_dev_Nm,"C2",ls="--",label="passive limit, deviation")
    ax[5].set_ylabel("generalized force (N m)"); ax[5].set_title("joint moments"); ax[5].legend(fontsize=6.5)
    ax[6].plot(JR.time,JR.radiocarpal_Fres_N,"C2",label="radiocarpal"); ax[6].plot(JR.time,JR.wrist_hand_Fres_N,"C4",label="wrist_hand"); ax[6].set_ylabel("resultant reaction force (N)"); ax[6].set_title("joint reaction force"); ax[6].legend()
    ax[7].plot(JR.time,JR.radiocarpal_Mres_Nm,"C2",label="radiocarpal"); ax[7].plot(JR.time,JR.wrist_hand_Mres_Nm,"C4",label="wrist_hand"); ax[7].set_ylabel("reaction moment (N m)"); ax[7].set_title("joint reaction moment"); ax[7].legend()
    ax[8].plot(np.degrees(D.flexion_rad),np.degrees(D.deviation_rad),"k"); ax[8].plot(0,0,"go"); ax[8].set_xlabel("flexion (deg)"); ax[8].set_ylabel("deviation (deg)"); ax[8].set_title("trajectory in coordinate space")
    for a in ax[:8]: a.set_xlabel("time (s)")
    fig.suptitle(f"Forward dynamics: {c} (explicit excitation, hypothetical control)",y=1.0,fontsize=10); fig.tight_layout(); fig.savefig(f"{FIG}/FD_{c}.png"); plt.close(fig)
fig,ax=plt.subplots(2,3,figsize=(13,6.5)); ax=ax.ravel()
for c in ["flexion","extension","radial","ulnar"]:
    D=pd.read_csv(f"{CSV}/FD_{c}.csv"); JR=pd.read_csv(f"{CSV}/JR_FD_{c}.csv"); co="flexion" if c in("flexion","extension") else "deviation"
    ax[0].plot(D.time,np.degrees(D[f"{co}_rad"]),color=FDc[c],label=c); ax[1].plot(D.time,np.degrees(D[f"{co}_vel"]),color=FDc[c]); ax[2].plot(D.time,np.degrees(D[f"{co}_acc"]),color=FDc[c])
    ax[3].plot(D.time,D[[f"F_{m_}" for m_ in M6]].sum(axis=1),color=FDc[c]); ax[4].plot(D.time,D[f"Mmuscle_{'flex' if co=='flexion' else 'dev'}_Nm"],color=FDc[c]); ax[5].plot(JR.time,JR.wrist_hand_Fres_N,color=FDc[c])
for a,t,yl in zip(ax,["primary joint angle","angular velocity","angular acceleration","summed six wrist-muscle force","muscle moment about primary axis","wrist_hand reaction force"],["deg","deg/s","deg/s$^2$","N","N m","N"]): a.set_title(t); a.set_ylabel(yl); a.set_xlabel("time (s)")
ax[0].legend(); fig.suptitle("Forward dynamics comparison across movements (+0.10 excitation pulse, 0.1-0.4 s)"); fig.tight_layout(); fig.savefig(f"{FIG}/C_forward_dynamics_comparison.png"); plt.close(fig)
# ---------- sensitivity figures
S=pd.read_csv(f"{CSV}/sensitivity_static_optimization.csv"); fig,ax=plt.subplots(1,3,figsize=(13,3.8))
for v in S.variant.unique():
    d=S[S.variant==v]; ax[0].plot(d.flexion_deg,d.F_flexors_N,marker="o",ms=3,label=v); ax[1].plot(d.flexion_deg,d.act_max,marker="o",ms=3); ax[2].plot(d.flexion_deg,d.wrist_hand_reaction_N,marker="o",ms=3)
for a,t,yl in zip(ax,["FCR+FCU+PL tendon force","peak muscle activation","wrist_hand reaction force"],["N","-","N"]): a.set_title(t); a.set_ylabel(yl); a.set_xlabel("wrist flexion (deg), quasi-static ramp")
ax[0].legend(fontsize=6.5,ncol=2); fig.suptitle("Static-optimization sensitivity (10 N load unless stated)"); fig.savefig(f"{FIG}/S_static_optimization_sensitivity.png"); plt.close(fig)
SF=pd.read_csv(f"{CSV}/sensitivity_forward_fd.csv"); fig,ax=plt.subplots(1,2,figsize=(11,3.8)); ax[0].barh(SF.variant,SF.peak_flexion_deg,color="C0"); ax[0].set_xlabel("peak flexion reached (deg)"); ax[0].set_title("forward dynamics: flexion pulse")
ax[1].barh(SF.variant,SF.peak_flexor_force_N,color="C3"); ax[1].set_xlabel("peak FCR/FCU tendon force (N)"); fig.savefig(f"{FIG}/S_forward_dynamics_sensitivity.png"); plt.close(fig)
# ---------- validation panel
V=pd.read_csv(f"{CSV}/momentarm_verification_fd_vs_api.csv"); I=pd.read_csv(f"{TAB}/id_verification_virtual_work.csv"); B=[pd.read_csv(f) for f in sorted(__import__("glob").glob(f"{CSV}/SO_balance_*.csv"))]
fig,ax=plt.subplots(1,4,figsize=(15,3.6)); ax[0].scatter(V.r_fd_mm,V.r_api_mm,s=8); lim=[V[["r_fd_mm","r_api_mm"]].min().min(),V[["r_fd_mm","r_api_mm"]].max().max()]; ax[0].plot(lim,lim,"k--",lw=.6); ax[0].set_xlabel("-dL/dq finite difference (mm)"); ax[0].set_ylabel("OpenSim computeMomentArm (mm)"); ax[0].set_title("moment-arm check")
ax[1].scatter(I.virtual_work_Nm,I.ID_Nm,s=8); l=[I.ID_Nm.min(),I.ID_Nm.max()]; ax[1].plot(l,l,"k--",lw=.6); ax[1].set_xlabel("virtual work statics (N m)"); ax[1].set_ylabel("Inverse Dynamics (N m)"); ax[1].set_title("ID check (120 pts)")
bal=pd.concat(B); ax[2].hist(np.r_[bal.err_flex.values,bal.err_dev.values],bins=40); ax[2].set_xlabel("sum(F r)+reserve - ID (N m)"); ax[2].set_title("Static Optimization moment balance")
fc=pd.concat([pd.read_csv(f"{CSV}/FD_check_{c}.csv") for c in ["baseline","flexion","extension","radial","ulnar"]]); xx=np.arange(len(fc)); ax[3].bar(xx-0.2,fc.flex_rms_err_Nm,0.4,label="flexion axis"); ax[3].bar(xx+0.2,fc.dev_rms_err_Nm,0.4,label="deviation axis"); ax[3].set_xticks(xx); ax[3].set_xticklabels(fc.case,rotation=30); ax[3].set_yscale("log"); ax[3].set_ylabel("RMS error (N m)"); ax[3].set_title("FD -> ID consistency"); ax[3].legend()
fig.tight_layout(); fig.savefig(f"{FIG}/V_validation_panel.png"); plt.close(fig); print("plots done")
