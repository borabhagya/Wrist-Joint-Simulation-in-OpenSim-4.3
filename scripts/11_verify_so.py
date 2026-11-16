"""Verify the six Static Optimization runs: finiteness, activation bounds, reserve use, and moment balance
   sum_i F_i r_i(q) + reserve  ==  ID net moment (projected on independent coordinates)."""
from common import *
import pandas as pd
RUNS=[("dyn_flexext","L00_unloaded"),("dyn_flexext","Lflex5N_dorsal"),("dyn_flexext","Lflex10N_dorsal"),("dyn_flexext","Lflex20N_dorsal"),("dyn_dev","L00_unloaded"),("dyn_dev","Ldev10N_down")]
m,s=load(WORK); mus=[x.getName() for x in m.getMuscles()]; cs=m.getCoordinateSet(); summ=[]
for kin,ld in RUNS:
    tag=f"SO_{kin}__{ld}"; F=read_storage(f"{OSF}/results_SO/{tag}_StaticOptimization_force.sto"); A=read_storage(f"{OSF}/results_SO/{tag}_StaticOptimization_activation.sto")
    I=pd.read_csv(f"{CSV}/ID_{kin}__{ld}.csv"); K=read_storage(f"{OSF}/{kin}.mot"); rows=[]
    for j in range(0,len(F),4):
        t=F.time.iloc[j]; k=K.iloc[(K.time-t).abs().argmin()]; set_pose(m,s,k["flexion"],k["deviation"]); i=I.iloc[(I.time-t).abs().argmin()]
        Mf=sum(F[n].iloc[j]*m.getMuscles().get(n).computeMomentArm(s,cs.get("flexion")) for n in mus)
        Md=sum(F[n].iloc[j]*m.getMuscles().get(n).computeMomentArm(s,cs.get("deviation")) for n in mus)
        rows.append(dict(t=t,Mmus_flex=Mf,Mmus_dev=Md,res_flex=F["flexion_reserve"].iloc[j],res_dev=F["deviation_reserve"].iloc[j],ID_flex=i.flexion_moment_Nm,ID_dev=i.deviation_moment_Nm))
    R=pd.DataFrame(rows); R["err_flex"]=R.Mmus_flex+R.res_flex-R.ID_flex; R["err_dev"]=R.Mmus_dev+R.res_dev-R.ID_dev
    R.to_csv(f"{CSV}/SO_balance_{kin}__{ld}.csv",index=False)
    am=A[mus]; fm=F[mus]
    summ.append(dict(run=tag,n_frames=len(F),all_finite=bool(np.isfinite(F.drop(columns='time').values).all()),act_min=am.values.min(),act_max=am.values.max(),
        force_min_N=fm.values.min(),force_peak_N=fm.values.max(),peak_reserve_flex_Nm=F["flexion_reserve"].abs().max(),peak_reserve_dev_Nm=F["deviation_reserve"].abs().max(),
        peak_ID_flex_Nm=R.ID_flex.abs().max(),peak_ID_dev_Nm=R.ID_dev.abs().max(),max_balance_err_flex_Nm=R.err_flex.abs().max(),max_balance_err_dev_Nm=R.err_dev.abs().max(),
        top_muscle_by_peak_activation=am.max().idxmax(),top_peak_activation=am.max().max()))
S=pd.DataFrame(summ); S.to_csv(f"{TAB}/so_verification.csv",index=False); pd.set_option("display.width",250,"display.max_columns",30); print(S.round(4).T.to_string())
