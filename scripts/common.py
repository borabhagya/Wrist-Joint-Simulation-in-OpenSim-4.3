"""Shared helpers. All paths relative to the submission root."""
import os, sys, warnings
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ORIG = os.path.join(ROOT, "original_model", "Hand_Wrist_Model_for_development.osim")
WORK = os.path.join(ROOT, "working_model", "ARMS_wrist_working.osim")
CSV  = os.path.join(ROOT, "results", "csv")
FIG  = os.path.join(ROOT, "results", "figures")
TAB  = os.path.join(ROOT, "results", "tables")
OSF  = os.path.join(ROOT, "opensim_files")
for d in (CSV, FIG, TAB, OSF): os.makedirs(d, exist_ok=True)
import opensim as osim
osim.Logger.setLevelString("error")   # geometry (.vtp) files are not available; silence the warnings
WRIST_MUSCLES = ["ECRL","ECRB","ECU","FCR","FCU","PL"]
def load(path=None):
    m = osim.Model(path or ORIG); s = m.initSystem(); return m, s
def v3(v): return [v.get(i) for i in range(3)]

import numpy as np
def set_pose(m, s, flexion=0.0, deviation=0.0, extra=None):
    """Set wrist coordinates (radians), project constraints (couplers), realize position."""
    cs = m.updCoordinateSet()
    cs.get("flexion").setValue(s, flexion, False)
    cs.get("deviation").setValue(s, deviation, False)
    if extra:
        for k, v in extra.items(): cs.get(k).setValue(s, v, False)
    m.assemble(s)       # enforces coupler constraints (wrist_hand_r1/r3, CMC5_r1)
    m.realizePosition(s)
    return s
def pos_in(m, s, body_from, body_to_point, point=(0,0,0)):
    """Location of a point fixed on body_to_point, expressed in the frame of body_from."""
    pt = osim.Vec3(*point)
    return v3(m.getBodySet().get(body_to_point).findStationLocationInAnotherFrame(s, pt, m.getBodySet().get(body_from)))

def write_storage(path, name, cols, data, in_degrees=False):
    """Write an OpenSim Storage (.mot/.sto). data: (n, len(cols)) incl. time as first col."""
    with open(path, "w") as f:
        f.write(f"{name}\nversion=1\nnRows={len(data)}\nnColumns={len(cols)}\ninDegrees={'yes' if in_degrees else 'no'}\nendheader\n")
        f.write("\t".join(cols) + "\n")
        for r in data: f.write("\t".join(f"{v:.8f}" for v in r) + "\n")
def read_storage(path):
    import pandas as pd
    with open(path) as f:
        n = 0
        for line in f:
            n += 1
            if line.strip().lower() == "endheader": break
    return pd.read_csv(path, sep=r"\s+", skiprows=n)
def minjerk(tau):
    tau = np.clip(tau, 0, 1); s = 10*tau**3 - 15*tau**4 + 6*tau**5
    ds = (30*tau**2 - 60*tau**3 + 30*tau**4); dds = (60*tau - 180*tau**2 + 120*tau**3); return s, ds, dds
def waypoints_traj(t, tw, qw):
    """Piecewise minimum-jerk through waypoints qw at times tw. Returns q, qd, qdd arrays."""
    q = np.zeros_like(t); qd = np.zeros_like(t); qdd = np.zeros_like(t)
    for i in range(len(tw)-1):
        T = tw[i+1]-tw[i]; msk = (t >= tw[i]) & (t <= tw[i+1]) if i == len(tw)-2 else (t >= tw[i]) & (t < tw[i+1])
        tau = (t[msk]-tw[i])/T; s_, ds_, dds_ = minjerk(tau); d = qw[i+1]-qw[i]
        q[msk] = qw[i] + d*s_; qd[msk] = d*ds_/T; qdd[msk] = d*dds_/T**2
    return q, qd, qdd
def full_pose_table(m, s, t, flex, dev, lock_defaults=True):
    cs = m.getCoordinateSet(); names = [cs.get(i).getName() for i in range(cs.getSize())]
    rows = []
    for ti, f, d in zip(t, flex, dev):
        set_pose(m, s, flexion=f, deviation=d)
        rows.append([ti] + [cs.get(n).getValue(s) for n in names])
    return ["time"] + names, np.array(rows)
