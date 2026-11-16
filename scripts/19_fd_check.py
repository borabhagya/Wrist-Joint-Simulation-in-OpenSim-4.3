"""Consistency check of forward dynamics: Inverse Dynamics of the simulated motion must return the muscle moments produced in the forward simulation."""
from idlib import *
import sys
c=sys.argv[1]; D=pd.read_csv(f"{CSV}/FD_{c}.csv")
cols=["time"]+[x[2:] for x in D.columns if x.startswith("q_")]; tab=np.column_stack([D.time]+[D[x] for x in D.columns if x.startswith("q_")])
mot=f"{OSF}/FD_{c}_coords.mot"; write_storage(mot,f"FD_{c}",cols,tab)
I=run_id_file(mot,f"FD_{c}",float(D.time.iloc[-1]),f"{OSF}/results_ID")
sel=(I.time>0.05)&(I.time<D.time.iloc[-1]-0.05)   # exclude spline end effects
ef=np.interp(I.time[sel],D.time,D.Mmuscle_flex_Nm)-I.flexion_moment_Nm[sel]; ed=np.interp(I.time[sel],D.time,D.Mmuscle_dev_Nm)-I.deviation_moment_Nm[sel]
out=dict(case=c,n=int(sel.sum()),flex_rms_err_Nm=float(np.sqrt((ef**2).mean())),flex_max_err_Nm=float(ef.abs().max()),dev_rms_err_Nm=float(np.sqrt((ed**2).mean())),dev_max_err_Nm=float(ed.abs().max()),
 flex_peak_moment_Nm=float(D.Mmuscle_flex_Nm.abs().max()),dev_peak_moment_Nm=float(D.Mmuscle_dev_Nm.abs().max()))
pd.DataFrame([out]).to_csv(f"{CSV}/FD_check_{c}.csv",index=False); print(out)
