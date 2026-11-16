"""Phase VI: Inverse dynamics + Static Optimization on the WORKING model.
INPUT DATA ARE SYNTHETIC (prescribed minimum-jerk kinematics + hypothetical external forces). There is no experimental motion/force data,
so results demonstrate the workflow and the model's mechanics; they are not measurements of a person."""
from common import *
import pandas as pd, shutil, glob
D=np.radians; dt=0.02
m, s = load(WORK)
# ---------- kinematics inside the passive-limit-free band (flexion +-45, deviation -5..+15 deg)
CASES_KIN = {"dyn_flexext": ([0,2,4,6,8],[0,D(45),0,-D(45),0],[0]*5),
             "dyn_dev":     ([0,2,4,6,8],[0]*5,[0,-D(5),0,D(15),0])}
for name,(tw,fw,dw) in CASES_KIN.items():
    t=np.arange(0,tw[-1]+dt/2,dt); f,_,_=waypoints_traj(t,np.array(tw,float),np.array(fw)); d,_,_=waypoints_traj(t,np.array(tw,float),np.array(dw))
    cols,tab=full_pose_table(m,s,t,f,d); write_storage(f"{OSF}/{name}.mot",name,cols,tab)
# ---------- external loads: constant ground-frame force at the 3rd MCP head (point fixed in thirdmc frame)
pt = np.array([0.0002,-0.0263,0.0018])   # 3rd MCP joint centre expressed in thirdmc frame (from model, see 01/convention check)
# ground axes (radius frame analysis): gravity = -y ground ; volar direction = -z ground ; +z ground = dorsally directed
LOADS = {"L00_unloaded":(0,0,0), "Ldev5N_down":(0,-5,0), "Ldev10N_down":(0,-10,0), "Lflex5N_dorsal":(0,0,5), "Lflex10N_dorsal":(0,0,10), "Lflex20N_dorsal":(0,0,20)}
def write_extload(name, F, motfile, tlast):
    t=np.arange(0,tlast+dt/2,dt); data=np.zeros((len(t),7)); data[:,0]=t; data[:,1:4]=F; data[:,4:7]=pt
    write_storage(f"{OSF}/{name}_forces.mot", f"{name}_forces", ["time","hand_force_vx","hand_force_vy","hand_force_vz","hand_point_px","hand_point_py","hand_point_pz"], data)
    ef=osim.ExternalForce(); ef.setName("hand_load"); ef.set_applied_to_body("thirdmc"); ef.set_force_expressed_in_body("ground"); ef.set_point_expressed_in_body("thirdmc")
    ef.set_force_identifier("hand_force_v"); ef.set_point_identifier("hand_point_p")
    el=osim.ExternalLoads(); el.setDataFileName(f"{name}_forces.mot"); el.cloneAndAppend(ef); el.printToXML(f"{OSF}/{name}_ExternalLoads.xml")
for n,F in LOADS.items(): write_extload(n,F,None,8.0)
# ---------- run ID + SO for each (kinematics, load) pair
def id_model():
    """Working-model copy with ALL muscle and reserve forces switched off, so that Inverse Dynamics returns the generalized force the
    muscles (active + passive) must supply. (The tool's default 'Muscles' exclusion did not remove muscle passive force for this model.)"""
    mm=osim.Model(WORK)
    for f in mm.updForceSet():
        if f.getConcreteClassName() in ("Millard2012EquilibriumMuscle","CoordinateActuator"): f.set_appliesForce(False)
    mm.initSystem(); return mm
def dep_slopes():
    """d(wrist_hand_r1)/d(deviation) and d(wrist_hand_r3)/d(flexion) from the coupler constraints (for projecting ID onto independent coordinates)."""
    mq,sq=load(WORK); dv=np.radians(np.linspace(-10,25,351)); r1=[]
    for d in dv: set_pose(mq,sq,0,d); r1.append(mq.getCoordinateSet().get("wrist_hand_r1").getValue(sq))
    return dv, np.gradient(np.array(r1),dv)
DV,SL1=dep_slopes()
def run_id(kin, load, tag):
    idt=osim.InverseDynamicsTool(); mm=id_model(); idt.setModel(mm); idt.setCoordinatesFileName(f"{OSF}/{kin}.mot"); idt.setLowpassCutoffFrequency(-1)
    idt.setStartTime(0); idt.setEndTime(8.0)
    if load!="L00_unloaded": idt.setExternalLoadsFileName(f"{OSF}/{load}_ExternalLoads.xml")
    idt.setOutputGenForceFileName(f"ID_{tag}.sto"); idt.setResultsDir(f"{OSF}/results_ID"); os.makedirs(f"{OSF}/results_ID",exist_ok=True)
    idt.run(); I=read_storage(f"{OSF}/results_ID/ID_{tag}.sto"); K=read_storage(f"{OSF}/{kin}.mot")
    dev=np.interp(I.time,K.time,K["deviation"])
    # Net generalized force on the INDEPENDENT coordinates (virtual work through the coupler constraints):
    I["flexion_moment_Nm"]=I["flexion_force"]+0.5*I["wrist_hand_r3_moment"]
    I["deviation_moment_Nm"]=I["deviation_force"]+np.interp(dev,DV,SL1)*I["wrist_hand_r1_moment"]
    I["flexion_deg"]=np.degrees(np.interp(I.time,K.time,K["flexion"])); I["deviation_deg"]=np.degrees(dev)
    return I
def run_so(kin, load, tag, activation_exponent=2.0, model_path=None, suffix=""):
    so=osim.StaticOptimization(); so.setUseModelForceSet(True); so.setActivationExponent(activation_exponent); so.setUseMusclePhysiology(True)
    so.setConvergenceCriterion(1e-4); so.setMaxIterations(200)
    at=osim.AnalyzeTool(); at.setName(tag); at.setModelFilename(model_path or WORK); at.setCoordinatesFileName(f"{OSF}/{kin}.mot"); at.setLowpassCutoffFrequency(-1)
    at.setInitialTime(0); at.setFinalTime(8.0); at.setSolveForEquilibrium(True)
    at.getAnalysisSet().cloneAndAppend(so)
    if load!="L00_unloaded": at.setExternalLoadsFileName(f"{OSF}/{load}_ExternalLoads.xml")
    os.makedirs(f"{OSF}/results_SO",exist_ok=True); at.setResultsDir(f"{OSF}/results_SO")
    xml=f"{OSF}/results_SO/{tag}_setup.xml"; at.printToXML(xml)
    at2=osim.AnalyzeTool(xml); at2.run()
import sys
RUN = [(k,l) for k in CASES_KIN for l in LOADS]
for kin,load in RUN:
    tag=f"{kin}__{load}"; I=run_id(kin,load,tag)
    I.to_csv(f"{CSV}/ID_{tag}.csv",index=False)
    print(tag,"ID peak |flexion|, |deviation| projected net moment (N m):",I["flexion_moment_Nm"].abs().max().round(3),I["deviation_moment_Nm"].abs().max().round(3))
