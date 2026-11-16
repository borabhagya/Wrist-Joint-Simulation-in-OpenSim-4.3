"""Schematic skeleton/muscle-path renderer (the bone .vtp meshes were not supplied, so bones are drawn as segments between joint centres)."""
from common import *
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
MCOL = {"ECRL":"#1b9e77","ECRB":"#66a61e","ECU":"#2c7fb8","FCR":"#d95f02","FCU":"#e7298a","PL":"#7570b3"}
def skeleton(m, s):
    """returns dict of segments (name -> (p0,p1)) and wrist muscle paths, in the RADIUS frame (metres)."""
    rad = m.getBodySet().get("radius")
    def P(frame): return np.array(v3(frame.findStationLocationInAnotherFrame(s, osim.Vec3(0), rad)))
    jc = {}; segs = {}
    prox = {}; dist = {}
    for j in m.getJointSet():
        cb = j.getChildFrame().findBaseFrame().getName(); pb = j.getParentFrame().findBaseFrame().getName()
        prox[cb] = P(j.getChildFrame()); dist.setdefault(pb, []).append((cb, P(j.getParentFrame())))
    for b, lst in dist.items():
        if b in ("ground","clavicle","scapula","humerus","ulna") : continue
        p0 = prox.get(b)
        for cb, p1 in lst:
            if any(x in f"{b}{cb}" for x in ("2proxph","2midph","2distph","4","5","secondmc","firstmc","thumb","trapez","hamate")): continue  # keep wrist + 3rd ray only
            if p0 is not None: segs[f"{b}->{cb}"] = (p0, p1)
    mus = {}
    for mu in WRIST_MUSCLES:
        pts = m.getMuscles().get(mu).getGeometryPath().getCurrentPath(s)
        arr = np.array([P(pts.get(i).getParentFrame()) + 0 for i in range(pts.getSize())])
        # use actual point locations in parent frame
        arr = np.array([v3(pts.get(i).getParentFrame().findStationLocationInAnotherFrame(s, pts.get(i).getLocation(s), rad)) for i in range(pts.getSize())])
        mus[mu] = arr
    return segs, mus, prox
def draw(ax, m, s, view=("y","z"), color="k", lw=1.6, muscles=True, alpha=1.0, wrist_only_muscles=True, lim=None):
    segs, mus, prox = skeleton(m, s); idx = {"x":0,"y":1,"z":2}; a, b = idx[view[0]], idx[view[1]]
    for k, (p0, p1) in segs.items(): ax.plot([p0[a],p1[a]],[p0[b],p1[b]], color=color, lw=lw, alpha=alpha, solid_capstyle="round")
    if muscles:
        for mu, arr in mus.items():
            sel = arr[-4:] if wrist_only_muscles else arr
            ax.plot(sel[:,a], sel[:,b], color=MCOL[mu], lw=1.1, alpha=alpha*0.9, label=mu)
