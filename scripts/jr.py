"""Joint reaction forces/moments by Newton-Euler balance of the distal free body (independent of OpenSim's JointReaction analysis).
Reaction applied by the PARENT on the distal group, resultant at the child-frame origin (joint centre), expressed in the radius frame:
    F_R = -( sum F_muscle,on distal + F_ext + m g )  +  sum m_i a_i
    M_R = -( sum (r_k - c) x F_k ) + sum (x_i - c) x m_i a_i          (rotational inertia terms neglected, bound reported separately)
"""
from common import *
G=np.array([0,-9.80665,0])
HAND={"capitate","trapezium","trapezoid","hamate","firstmc1","firstmc","proximal_thumb","distal_thumb","secondmc","thirdmc","fourthmc","fifthmc"}|{f"{d}{p}" for d in "2345" for p in ("proxph","midph","distph")}
DISTAL={"wrist_hand":HAND,"radiocarpal":HAND|{"proximal_row"}}
def _u(v):
    n=np.linalg.norm(v); return v/n if n>1e-12 else np.zeros(3)   # coincident path points (zero-length segments) carry no direction
def muscle_point_forces(m,s,T):
    """list of (ground_point, force_vector_ground, body_name) for all muscle path points; T: dict muscle->tendon force (N)."""
    out=[]
    for mu in m.getMuscles():
        t=T[mu.getName()]
        if t==0: continue
        pts=mu.getGeometryPath().getCurrentPath(s); P=[];B=[]
        for i in range(pts.getSize()):
            p=pts.get(i); fr=p.getParentFrame(); P.append(np.array(v3(fr.findStationLocationInGround(s,p.getLocation(s))))); B.append(fr.findBaseFrame().getName())
        for i in range(len(P)):
            f=np.zeros(3)
            if i<len(P)-1: f+=t*_u(P[i+1]-P[i])
            if i>0: f-=t*_u(P[i]-P[i-1])
            out.append((P[i],f,B[i]))
    return out
def reactions(m,s,T,Fext,ext_body="thirdmc",ext_pt=(0.0002,-0.0263,0.0018),acc=None):
    """acc: dict body-> (com_ground_pos, com_acc) optional. returns dict joint->(F_ground,M_ground,centre,Rm)"""
    mpf=muscle_point_forces(m,s,T); res={}
    ep=np.array(v3(m.getBodySet().get(ext_body).findStationLocationInGround(s,osim.Vec3(*ext_pt))))
    R=m.getBodySet().get("radius").getTransformInGround(s).R(); Rm=np.array([[R.get(a,b) for b in range(3)] for a in range(3)])
    for jn,bodies in DISTAL.items():
        j=m.getJointSet().get(jn); c=np.array(v3(j.getChildFrame().getPositionInGround(s)))
        F=np.zeros(3); M=np.zeros(3)
        for p,f,b in mpf:
            if b in bodies: F+=f; M+=np.cross(p-c,f)
        F+=np.array(Fext); M+=np.cross(ep-c,np.array(Fext))
        for b in bodies:
            B=m.getBodySet().get(b); mass=B.getMass(); x=np.array(v3(B.findStationLocationInGround(s,B.getMassCenter())))
            F+=mass*G; M+=np.cross(x-c,mass*G)
            if acc is not None and b in acc: F-=mass*acc[b]; M-=np.cross(x-c,mass*acc[b])
        res[jn]=(-F,-M,c)
    return res,Rm
def to_radius(v,Rm): return Rm.T@v
