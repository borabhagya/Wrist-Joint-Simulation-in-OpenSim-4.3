"""Tune the forward-dynamics baseline (ECRB, ECU activations) so the neutral posture is an equilibrium of the FORWARD model.
Targets = inverse-dynamics required muscle moments at t=0 (unloaded): results/csv/ID_dyn_flexext__L00_unloaded.csv. Writes results/csv/fd_baseline_activations.json."""
from fd_lib import *
import json
I=pd.read_csv(f"{CSV}/ID_dyn_flexext__L00_unloaded.csv"); i0=I.iloc[0]
if os.path.exists(f"{CSV}/fd_baseline_activations.json"): os.remove(f"{CSV}/fd_baseline_activations.json")   # start from raw SO activations
b=tune_baseline(target=(i0.flexion_moment_Nm,i0.deviation_moment_Nm)); json.dump(b,open(f"{CSV}/fd_baseline_activations.json","w"),indent=1)
print({k:round(b[k],4) for k in ("ECRB","ECU")})
