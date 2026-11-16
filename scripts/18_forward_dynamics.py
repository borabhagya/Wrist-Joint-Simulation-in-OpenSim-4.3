"""Phase VII: forward dynamics with explicit excitations. Baseline = posture-holding activations at neutral (SO solution, ECRB/ECU re-tuned for forward-model equilibrium);
agonist pulse = +0.10 excitation for 0.30 s (ramps 0.05 s). The excitations are HYPOTHETICAL control inputs, not a validated recruitment pattern."""
from fd_lib import *
import sys
cases=sys.argv[1].split(",") if len(sys.argv)>1 else list(CASES)
for c in cases:
    m,s=build(case=c); D=run(m,s,tmax=1.2); D.to_csv(f"{CSV}/FD_{c}.csv",index=False)
    print(f"{c:10s} status={D.attrs['status']} wall={D.attrs['wall_s']:.0f}s | flexion range {np.degrees(D.flexion_rad.min()):.1f}..{np.degrees(D.flexion_rad.max()):.1f} deg, deviation {np.degrees(D.deviation_rad.min()):.1f}..{np.degrees(D.deviation_rad.max()):.1f} deg | peak ligament torque {max(D.lig_flex_Nm.abs().max(),D.lig_dev_Nm.abs().max()):.2f} Nm | t=0 acc {D.flexion_acc.iloc[0]:.2f},{D.deviation_acc.iloc[0]:.2f}")
