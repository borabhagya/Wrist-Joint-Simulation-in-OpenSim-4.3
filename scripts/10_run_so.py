"""Run Static Optimization for one (kinematics, load) case. Usage: python 10_run_so.py dyn_flexext Lflex10N_dorsal [activation_exponent]"""
import sys
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"08_id_so.py")).read() if False else None
from common import *
def run_so(kin, load, tag, activation_exponent=2.0, model_path=None):
    so=osim.StaticOptimization(); so.setUseModelForceSet(True); so.setActivationExponent(activation_exponent); so.setUseMusclePhysiology(True)
    so.setConvergenceCriterion(1e-4); so.setMaxIterations(200)
    at=osim.AnalyzeTool(); at.setName(tag); at.setModelFilename(model_path or WORK); at.setCoordinatesFileName(f"{OSF}/{kin}.mot"); at.setLowpassCutoffFrequency(-1)
    at.setInitialTime(0); at.setFinalTime(8.0); at.setSolveForEquilibrium(True); at.getAnalysisSet().cloneAndAppend(so)
    if load!="L00_unloaded": at.setExternalLoadsFileName(f"{OSF}/{load}_ExternalLoads.xml")
    os.makedirs(f"{OSF}/results_SO",exist_ok=True); at.setResultsDir(f"{OSF}/results_SO")
    xml=f"{OSF}/results_SO/{tag}_setup.xml"; at.printToXML(xml); at2=osim.AnalyzeTool(xml); at2.run()
if __name__=="__main__":
    kin,load=sys.argv[1],sys.argv[2]; ex=float(sys.argv[3]) if len(sys.argv)>3 else 2.0
    run_so(kin,load,f"SO_{kin}__{load}"+("" if ex==2.0 else f"__exp{ex:g}"),ex)
