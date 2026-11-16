"""Forward-dynamics helpers (OpenSim API): explicit excitations via PrescribedController, Manager integration, state post-processing."""
from common import *
import pandas as pd, time as _t
BASE=0.02
CASES={  # agonist excitation sets (hypothetical, NOT physiologically validated recruitment)
 "baseline":   {},
 "flexion":    {"FCR":1,"FCU":1,"PL":1},
 "extension":  {"ECRL":1,"ECRB":1,"ECU":1},
 "radial":     {"FCR":1,"ECRL":1,"ECRB":1},
 "ulnar":      {"FCU":1,"ECU":1},
}
def so_baseline(path=None):
    """posture-holding activations at neutral = Static Optimization solution at t=0 (unloaded). Gives a valid dynamic-equilibrium initial condition."""
    import json
    jf=f"{CSV}/fd_baseline_activations.json"
    if path is None and os.path.exists(jf): return json.load(open(jf))      # SO activations with ECRB/ECU re-tuned for forward-model equilibrium (tune_baseline)
    A=read_storage(path or f"{OSF}/results_SO/SO_dyn_flexext__L00_unloaded_StaticOptimization_activation.sto"); r=A.iloc[0]
    return {c:float(r[c]) for c in A.columns if c not in ("time",) and not c.endswith("_reserve")}
def build(model_path=WORK, d_ag=0.10, case="flexion", t_on=0.10, t_off=0.40, ramp=0.05, tmax=1.2, base=None, fmax_scale=1.0, tsl_scale=1.0, a0_scale=1.0):
    base=base or so_baseline(); m=osim.Model(model_path)
    for mu in m.getMuscles():
        if fmax_scale!=1.0: mu.setMaxIsometricForce(mu.getMaxIsometricForce()*fmax_scale)
        if tsl_scale!=1.0 and mu.getName() in WRIST_MUSCLES: mu.setTendonSlackLength(mu.getTendonSlackLength()*tsl_scale)
    ctrl=osim.PrescribedController(); ctrl.setActuators(m.updActuators())
    for a in m.getActuators():
        n=a.getName(); f=osim.PiecewiseLinearFunction()
        if n.endswith("_reserve"): f.addPoint(0,0.0); f.addPoint(tmax+1,0.0)
        else:
            b=min(1.0,base[n])
            if n in CASES[case]:
                u=min(1.0,b+d_ag); f.addPoint(0,b); f.addPoint(t_on,b); f.addPoint(t_on+ramp,u); f.addPoint(t_off,u); f.addPoint(t_off+ramp,b); f.addPoint(tmax+1,b)
            else: f.addPoint(0,b); f.addPoint(tmax+1,b)
        ctrl.prescribeControlForActuator(n,f)
    m.addController(ctrl); s=m.initSystem(); m._base=base; m._a0scale=a0_scale; return m,s
def run(m,s,tmax=1.2,q0=(0.0,0.0),acc=1e-5,dt=0.01,a0_scale=1.0):
    """integrate to tmax, sampling the live integrator state every dt (states rebuilt from a table do not realize reliably for this model)."""
    cs=m.updCoordinateSet(); cs.get("flexion").setValue(s,q0[0]); cs.get("deviation").setValue(s,q0[1]); cs.get("flexion").setSpeedValue(s,0); cs.get("deviation").setSpeedValue(s,0)
    for mu in m.getMuscles(): osim.Millard2012EquilibriumMuscle.safeDownCast(mu).setActivation(s,max(0.01,min(1.0,m._base[mu.getName()]*a0_scale)))
    m.assemble(s); m.equilibrateMuscles(s); s.setTime(0)
    mg=osim.Manager(m); mg.setIntegratorMethod(osim.Manager.IntegratorMethod_RungeKuttaMerson); mg.setIntegratorAccuracy(acc); mg.initialize(s)
    lig_f=osim.CoordinateLimitForce.safeDownCast(m.getForceSet().get("flexion_ligaments")); lig_d=osim.CoordinateLimitForce.safeDownCast(m.getForceSet().get("deviation_ligaments"))
    mus=list(m.getMuscles()); rows=[]; t0=_t.time(); status="completed"; sv_names=None
    def record(st):
        m.realizeAcceleration(st); r=dict(time=st.getTime(),flexion_rad=cs.get("flexion").getValue(st),deviation_rad=cs.get("deviation").getValue(st),
            flexion_vel=cs.get("flexion").getSpeedValue(st),deviation_vel=cs.get("deviation").getSpeedValue(st),flexion_acc=cs.get("flexion").getAccelerationValue(st),deviation_acc=cs.get("deviation").getAccelerationValue(st),
            lig_flex_Nm=lig_f.calcLimitForce(st),lig_dev_Nm=lig_d.calcLimitForce(st)); Mf=Md=0.0
        for mu in mus:
            F=mu.getTendonForce(st); n_=mu.getName(); r[f"F_{n_}"]=F; r[f"act_{n_}"]=mu.getActivation(st); r[f"ex_{n_}"]=mu.getExcitation(st)
            Mf+=F*mu.computeMomentArm(st,cs.get("flexion")); Md+=F*mu.computeMomentArm(st,cs.get("deviation"))
        r["Mmuscle_flex_Nm"]=Mf; r["Mmuscle_dev_Nm"]=Md
        # coordinate values (all 26) for the later ID consistency check
        for k in range(cs.getSize()): r["q_"+cs.get(k).getName()]=cs.get(k).getValue(st)
        return r
    rows.append(record(s))
    try:
        for tt in np.arange(dt,tmax+1e-9,dt):
            st=mg.integrate(float(tt)); rows.append(record(st))
    except Exception as e: status="FAILED at t=%.3f: %s"%(rows[-1]["time"],str(e)[:120].replace("\n"," "))
    D=pd.DataFrame(rows); D.attrs["status"]=status; D.attrs["wall_s"]=_t.time()-t0; return D

def static_muscle_moments(m,s,base):
    for mu in m.getMuscles(): osim.Millard2012EquilibriumMuscle.safeDownCast(mu).setActivation(s,min(1.0,base[mu.getName()]))
    cs=m.updCoordinateSet(); cs.get("flexion").setValue(s,0.0); cs.get("deviation").setValue(s,0.0); m.assemble(s); m.equilibrateMuscles(s); m.realizePosition(s); m.realizeDynamics(s)
    cs=m.getCoordinateSet(); Mf=Md=0.0
    for mu in m.getMuscles():
        F=mu.getTendonForce(s); Mf+=F*mu.computeMomentArm(s,cs.get("flexion")); Md+=F*mu.computeMomentArm(s,cs.get("deviation"))
    return np.array([Mf,Md])
def tune_baseline(target=(0.0124,-0.1732),tune=("ECRB","ECU"),verbose=True):
    """adjust two extensor baseline activations so that the FORWARD model's muscle moments equal the neutral posture-holding moments from inverse dynamics (unloaded)."""
    m=osim.Model(WORK); s=m.initSystem(); base=so_baseline(); x=np.array([base[n] for n in tune]); tgt=np.array(target)
    for it in range(12):
        b=dict(base); b.update({n:float(v) for n,v in zip(tune,x)}); f0=static_muscle_moments(m,s,b)-tgt
        if verbose: print("iter",it,"act",np.round(x,4),"moment error (Nm)",np.round(f0,4))
        if np.abs(f0).max()<2e-4: break
        J=np.zeros((2,2))
        for k in range(2):
            xp=x.copy(); xp[k]+=1e-3; bp=dict(base); bp.update({n:float(v) for n,v in zip(tune,xp)}); J[:,k]=(static_muscle_moments(m,s,bp)-tgt-f0)/1e-3
        x=np.clip(x-np.linalg.solve(J,f0),0.01,0.6)
    b=dict(base); b.update({n:float(v) for n,v in zip(tune,x)}); return b
