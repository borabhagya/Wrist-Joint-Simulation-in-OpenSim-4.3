"""Verify sign conventions; numerically verify r=-dL/dq vs OpenSim computeMomentArm; sweep moment arms."""
from common import *
import pandas as pd
m, s = load()
cs = m.getCoordinateSet()
# ---------- neutral and mapping through joints
set_pose(m, s)
print("neutral: ", {c: round(cs.get(c).getValue(s),6) for c in ["flexion","deviation","wrist_hand_r1","wrist_hand_r3"]})
# ---------- sign convention: where does the hand go for +flexion / +deviation, in the radius frame?
# radius-frame directions of anatomical sides from muscle paths (volar = FCR/FCU/PL path, dorsal = ECRL/ECRB/ECU path)
def path_pts(mu):
    gp = m.getMuscles().get(mu).getGeometryPath(); pts = gp.getCurrentPath(s); out = []
    for i in range(pts.getSize()):
        p = pts.get(i); loc = p.getLocation(s); fr = p.getParentFrame()
        out.append(v3(fr.findStationLocationInAnotherFrame(s, loc, m.getBodySet().get("radius"))))
    return np.array(out)
vol = np.mean([path_pts(x)[-2] for x in ["FCR","FCU","PL"]], axis=0)   # last-but-one point: distal forearm / wrist
dor = np.mean([path_pts(x)[-2] for x in ["ECRL","ECRB","ECU"]], axis=0)
ulna_dir = np.mean([path_pts(x)[-2] for x in ["ECU","FCU"]], axis=0) - np.mean([path_pts(x)[-2] for x in ["ECRL","ECRB","FCR"]], axis=0)  # ulnar-side minus radial-side tendons
tip0 = np.array(pos_in(m, s, "radius", "thirdmc", (0,0,0)))
conv = {}
for q, name in [(+0.3,"flexion"),(-0.3,"flexion")]:
    set_pose(m, s, flexion=q); tip = np.array(pos_in(m, s, "radius", "thirdmc")); d = tip - tip0
    conv[f"flexion={q:+.1f} rad"] = dict(dr=np.round(d*1000,2).tolist(), dot_volar=float(d@(vol-dor)/np.linalg.norm(vol-dor)))
for q in (+0.3,-0.1):
    set_pose(m, s, deviation=q); tip = np.array(pos_in(m, s, "radius", "thirdmc")); d = tip - tip0
    conv[f"deviation={q:+.1f} rad"] = dict(dr=np.round(d*1000,2).tolist(), dot_ulnar=float(d@ulna_dir/np.linalg.norm(ulna_dir)))
set_pose(m, s)
for k, v in conv.items(): print(k, v)
pd.DataFrame(conv).T.to_csv(f"{CSV}/sign_convention_check.csv")
# ---------- joint-level decomposition of motion through the two carpal joints
rows = []
for q in np.linspace(-1.2217, 1.2217, 11):
    set_pose(m, s, flexion=q)
    rows.append(dict(flexion_deg=np.degrees(q), wrist_hand_r3_deg=np.degrees(cs.get("wrist_hand_r3").getValue(s)),
                     radiocarpal_rot3_deg=np.degrees(0.5*q)))
pd.DataFrame(rows).to_csv(f"{CSV}/flexion_split_radiocarpal_midcarpal.csv", index=False)
rows = []
for q in np.linspace(-0.1745, 0.4363, 9):
    set_pose(m, s, deviation=q)
    rows.append(dict(deviation_deg=np.degrees(q), wrist_hand_r1_deg=np.degrees(cs.get("wrist_hand_r1").getValue(s))))
pd.DataFrame(rows).to_csv(f"{CSV}/deviation_split_radiocarpal_midcarpal.csv", index=False)
set_pose(m, s)
# ---------- moment-arm sweeps
muscles = [mu.getName() for mu in m.getMuscles()]
focus = WRIST_MUSCLES + ["EDCI","EDCM","EDCR","EDCL","EDM","FDSI","FDSM","FDSR","FDSL","FDPI","FDPM","FDPR","FDPL","APL","EPL","EPB","FPL","EIP"]
def sweep(coord, qs, other=0.0):
    out = []
    for q in qs:
        kw = {coord: q}; 
        if coord == "flexion": kw["deviation"] = other
        else: kw["flexion"] = other
        set_pose(m, s, **kw)
        row = dict(q_rad=q, q_deg=np.degrees(q))
        for mu in focus:
            M = m.getMuscles().get(mu); row[f"{mu}_L"] = M.getLength(s)
            row[f"{mu}_r"] = M.computeMomentArm(s, cs.get(coord))
        out.append(row)
    set_pose(m, s); return pd.DataFrame(out)
qf = np.radians(np.arange(-70, 70.1, 2.5)); qd = np.radians(np.arange(-10, 25.1, 1.25))
Df = sweep("flexion", qf); Df.to_csv(f"{CSV}/momentarm_vs_flexion.csv", index=False)
Dd = sweep("deviation", qd); Dd.to_csv(f"{CSV}/momentarm_vs_deviation.csv", index=False)
# cross-coupling: flexion-extension arm vs deviation arm for each wrist muscle (other coordinate at 0)
Dfd = sweep("deviation", qd); 
# ---------- independent verification: central finite difference  r = -dL/dq  vs computeMomentArm
chk = []
for coord, qs in (("flexion", np.radians([-50,-25,0,25,50])), ("deviation", np.radians([-5,0,10,20]))):
    for mu in WRIST_MUSCLES:
        for q in qs:
            h = 1e-4; Ls = []
            for dq in (-h, +h):
                kw = {coord: q+dq}; set_pose(m, s, **kw); Ls.append(m.getMuscles().get(mu).getLength(s))
            fd = -(Ls[1]-Ls[0])/(2*h)
            set_pose(m, s, **{coord: q}); api = m.getMuscles().get(mu).computeMomentArm(s, cs.get(coord))
            chk.append(dict(coord=coord, muscle=mu, q_deg=np.degrees(q), r_api_mm=api*1000, r_fd_mm=fd*1000, abs_diff_mm=abs(api-fd)*1000))
set_pose(m, s)
C = pd.DataFrame(chk); C.to_csv(f"{CSV}/momentarm_verification_fd_vs_api.csv", index=False)
print("max |API - FD| moment arm discrepancy (mm):", C.abs_diff_mm.max().round(4), " median:", C.abs_diff_mm.median().round(5))
# neutral-posture summary
r0 = pd.DataFrame({"muscle": WRIST_MUSCLES,
  "r_flexion_neutral_mm": [Df.loc[np.argmin(abs(Df.q_rad)), f"{x}_r"]*1000 for x in WRIST_MUSCLES],
  "r_deviation_neutral_mm": [Dd.loc[np.argmin(abs(Dd.q_rad-0)), f"{x}_r"]*1000 for x in WRIST_MUSCLES],
  "L_mtu_neutral_mm":[Df.loc[np.argmin(abs(Df.q_rad)), f"{x}_L"]*1000 for x in WRIST_MUSCLES]})
r0.to_csv(f"{TAB}/neutral_moment_arms.csv", index=False); print(r0.round(2).to_string())
