from common import *
import pandas as pd
def id_model():
    mm=osim.Model(WORK)
    for f in mm.updForceSet():
        if f.getConcreteClassName() in ("Millard2012EquilibriumMuscle","CoordinateActuator"): f.set_appliesForce(False)
    mm.initSystem(); return mm
def dep_slopes():
    mq,sq=load(WORK); dv=np.radians(np.linspace(-12,27,391)); r1=[]
    for d in dv: set_pose(mq,sq,0,d); r1.append(mq.getCoordinateSet().get("wrist_hand_r1").getValue(sq))
    return dv,np.gradient(np.array(r1),dv)
def run_id_file(mot,tag,tend,outdir):
    mm=id_model(); idt=osim.InverseDynamicsTool(); idt.setModel(mm); idt.setCoordinatesFileName(mot); idt.setLowpassCutoffFrequency(-1); idt.setStartTime(0); idt.setEndTime(tend)
    os.makedirs(outdir,exist_ok=True); idt.setOutputGenForceFileName(f"ID_{tag}.sto"); idt.setResultsDir(outdir); idt.run()
    I=read_storage(f"{outdir}/ID_{tag}.sto"); K=read_storage(mot); DV,SL=dep_slopes(); dev=np.interp(I.time,K.time,K["deviation"])
    I["flexion_moment_Nm"]=I["flexion_force"]+0.5*I["wrist_hand_r3_moment"]; I["deviation_moment_Nm"]=I["deviation_force"]+np.interp(dev,DV,SL)*I["wrist_hand_r1_moment"]; return I
