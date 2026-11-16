"""Phase III: create the working model by minimal TEXT edits of the original (keeps OpenSim 4.3 'Version 40000' format).
Modifications (all documented in results/tables/model_modifications.csv):
  M1  lock the 21 independent non-wrist coordinates at their default values (finger/thumb DOFs are not part of the wrist study; also
      required so that Inverse Dynamics / Static Optimization / Forward Dynamics have only the two wrist DOFs unlocked).
  M2  append CoordinateActuators flexion_reserve / deviation_reserve (optimal force 0.01 N m -> heavily penalised in Static Optimization).
Everything else (muscles, geometry, joints, constraints, passive elements, inertia) is byte-identical to the original."""
from common import *
import re, pandas as pd
txt = open(ORIG, encoding="utf8", newline="").read()
nl = "\r\n" if "\r\n" in txt else "\n"
KEEP_UNLOCKED = {"flexion","deviation","wrist_hand_r1","wrist_hand_r3","CMC5_r1"}   # wrist DOFs + coupler-dependent coordinates
mods = []; count = 0
def lock(mo):
    global count
    blk = mo.group(0); nm = re.search(r'<Coordinate name="([^"]+)"', blk).group(1)
    if nm in KEEP_UNLOCKED: return blk
    new = blk.replace("<locked>false</locked>", "<locked>true</locked>")
    if new != blk: count += 1; mods.append(dict(id="M1", item=f"Coordinate {nm}", parameter="locked", original="false", modified="true"))
    return new
txt2 = re.sub(r'<Coordinate name="[^"]+">.*?</Coordinate>', lock, txt, flags=re.S)
reserve = ""
for c in ("flexion","deviation"):
    reserve += (f'\t\t\t\t<CoordinateActuator name="{c}_reserve">{nl}\t\t\t\t\t<min_control>-10000</min_control>{nl}\t\t\t\t\t<max_control>10000</max_control>{nl}'
                f'\t\t\t\t\t<coordinate>{c}</coordinate>{nl}\t\t\t\t\t<optimal_force>0.01</optimal_force>{nl}\t\t\t\t</CoordinateActuator>{nl}')
    mods.append(dict(id="M2", item=f"ForceSet/{c}_reserve", parameter="added CoordinateActuator", original="(absent)", modified="optimal_force=0.01 N m, control in [-1e4, 1e4]"))
# insert before the </objects> that closes the top-level ForceSet
fs = txt2.find('<ForceSet name="forceset">'); end = txt2.find("</objects>", fs)
# the first </objects> after fs may belong to nested sets in muscles; locate the last </objects> before </ForceSet>
fe = txt2.find("</ForceSet>", fs); end = txt2.rfind("</objects>", fs, fe)
txt2 = txt2[:end].rstrip("\t") + reserve + "\t\t\t" + txt2[end:]
open(WORK, "w", encoding="utf8", newline="").write(txt2)
pd.DataFrame(mods).to_csv(f"{TAB}/model_modifications.csv", index=False)
print("locked coordinates:", count, " reserve actuators added: 2")
# ----- verification: loads, initialises, identical kinematics / muscle geometry / moment arms vs original
mo, so = load(ORIG); mw, sw = load(WORK)
print("working model: bodies", mw.getBodySet().getSize(), "forces", mw.getForceSet().getSize(), "muscles", mw.getMuscles().getSize(),
      "coords locked:", sum(c.getLocked(sw) for c in mw.getCoordinateSet()), "of", mw.getCoordinateSet().getSize())
maxd = 0; maxL = 0
for f, d in [(0,0),(0.5,0.1),(-0.7,0.3),(1.0,-0.1),(-1.0,0.4)]:
    set_pose(mo, so, f, d); set_pose(mw, sw, f, d)
    for mu in mo.getMuscles():
        n = mu.getName(); a = mu.getLength(so); b = mw.getMuscles().get(n).getLength(sw); maxL = max(maxL, abs(a-b))
        if n in WRIST_MUSCLES:
            for cn in ("flexion","deviation"):
                maxd = max(maxd, abs(mu.computeMomentArm(so, mo.getCoordinateSet().get(cn)) - mw.getMuscles().get(n).computeMomentArm(sw, mw.getCoordinateSet().get(cn))))
print(f"max |MTU length diff| original vs working: {maxL:.2e} m ; max |moment-arm diff|: {maxd:.2e} m")
print("mass original/working (kg):", sum(b.getMass() for b in mo.getBodySet()), sum(b.getMass() for b in mw.getBodySet()))
