# OpenSim version compatibility
* Results were produced with OpenSim 4.6 (Python API). The working model was created by **text edits** of the original 4.3-format (`Version="40000"`) file, so it carries no 4.6-only properties.
* **OpenSim 4.3 was not available** (the `opensim-org` conda channel starts at 4.4; pip provides 4.5/4.6). The original and working models were loaded in **4.4.1** and
  produced muscle-tendon lengths and wrist moment arms identical to 4.6 to <2e-17 at 72 values per model (`results/compat/`).
* To test in your 4.3 installation: (1) GUI: File > Open `working_model/ARMS_wrist_working.osim`; confirm 26 coordinates, flexion/deviation unlocked, other independent coordinates locked.
  (2) Python 4.3: `python scripts/compat_check.py out43.json` and compare with `results/compat/opensim_4.6.json` (muscle lengths/moment arms should agree to ~1e-12).
  (3) Load `opensim_files/exp1_flexion_extension.mot` in the GUI to play the motion.
* API differences: scripts use 4.6 Python names (e.g. `printToXML`, `AnalyzeTool.setModelFilename`, `Manager.initialize`). 4.3 versions of some calls may differ; the Static Optimization/ID/JRA XML setup files in `opensim_files/results_*` are standard `AnalyzeTool`/`InverseDynamicsTool` setups.
* Static Optimization output file names containing a dot (e.g. `fmax_0.8`) lose their `.sto` extension in OpenSim 4.6; sensitivity outputs were renamed accordingly.
