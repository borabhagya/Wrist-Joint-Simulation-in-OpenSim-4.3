"""Compare OpenSim JointReaction output with the Newton-Euler reaction (same SO forces, 10 N dorsal case, wrist_hand_on_capitate, radius frame)."""
from common import *
import pandas as pd
J=read_storage(f"{OSF}/results_JRA/JRA_dyn_flexext__Lflex10N_dorsal_JRA_ReactionLoads.sto"); N=pd.read_csv(f"{CSV}/JR_dyn_flexext__Lflex10N_dorsal.csv")
c=[f"wrist_hand_on_capitate_in_radius_f{a}" for a in "xyz"]; rows=[]
for _,r in N.iterrows():
    j=J.iloc[(J.time-r.time).abs().argmin()]; Fj=np.array([j[x] for x in c]); Fn=np.array([r[f"wrist_hand_F{a}_N"] for a in "xyz"])
    rows.append(dict(time=r.time,JRA_N=np.linalg.norm(Fj),NE_N=np.linalg.norm(Fn),diff_N=np.linalg.norm(Fj-Fn),JRA_corrupt=bool(np.abs(Fj).max()>1e3 or not np.isfinite(Fj).all())))
C=pd.DataFrame(rows); C.to_csv(f"{TAB}/jra_vs_newton_euler.csv",index=False)
ok=C[~C.JRA_corrupt]; print("frames:",len(C),"corrupted OpenSim-JRA frames:",int(C.JRA_corrupt.sum()))
for lo,hi in ((0,1.2),(1.2,3.4),(3.4,8.1)):
    q=ok[(ok.time>=lo)&(ok.time<hi)]; print(f"t in [{lo},{hi}) clean frames {len(q)}: median |JRA-NE| = {q.diff_N.median():.3f} N, max = {q.diff_N.max():.3f} N, median NE = {q.NE_N.median():.1f} N")
