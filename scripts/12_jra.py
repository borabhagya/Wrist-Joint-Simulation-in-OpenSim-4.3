"""Phase VIII: OpenSim JointReaction analysis at radiocarpal and wrist_hand, driven by Static-Optimization muscle forces (forces file).
Reactions = force/moment applied by the PARENT on the CHILD body, expressed in the RADIUS frame (x radial->ulnar-ish side axis, y along forearm, z dorsal-volar)."""
from common import *
import sys, pandas as pd
def run_jra(kin, load, tag, forces_file, out_tag, model_path=None, final=8.0):
    jra=osim.JointReaction(); jra.setName("JRA")
    names=osim.ArrayStr(); [names.append(n) for n in ("radiocarpal","wrist_hand")]
    onb=osim.ArrayStr(); [onb.append("child") for _ in range(2)]
    inf=osim.ArrayStr(); [inf.append("radius") for _ in range(2)]
    jra.setJointNames(names); jra.setOnBody(onb); jra.setInFrame(inf); jra.setForcesFileName(forces_file)
    at=osim.AnalyzeTool(); at.setName(out_tag); at.setModelFilename(model_path or WORK); at.setCoordinatesFileName(f"{OSF}/{kin}.mot"); at.setLowpassCutoffFrequency(-1)
    at.setInitialTime(0); at.setFinalTime(final); at.setSolveForEquilibrium(True); at.getAnalysisSet().cloneAndAppend(jra)
    if load!="L00_unloaded": at.setExternalLoadsFileName(f"{OSF}/{load}_ExternalLoads.xml")
    d=f"{OSF}/results_JRA"; os.makedirs(d,exist_ok=True); at.setResultsDir(d); xml=f"{d}/{out_tag}_setup.xml"; at.printToXML(xml); osim.AnalyzeTool(xml).run()
if __name__=="__main__":
    kin,load=sys.argv[1],sys.argv[2]; tag=f"SO_{kin}__{load}"
    run_jra(kin,load,tag,f"{OSF}/results_SO/{tag}_StaticOptimization_force.sto",f"JRA_{kin}__{load}")
