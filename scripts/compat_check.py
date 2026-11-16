"""OpenSim version cross-check: load original + working model, compare muscle lengths and moment arms at fixed poses, print version.
Usage: <python with opensim> compat_check.py [out.csv]"""
import sys, os, json
import opensim as osim
osim.Logger.setLevelString("error")
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..")); out={}
out["opensim_version"]=osim.GetVersionAndDate()
for tag,p in (("original","original_model/Hand_Wrist_Model_for_development.osim"),("working","working_model/ARMS_wrist_working.osim")):
    try:
        m=osim.Model(os.path.join(ROOT,p)); s=m.initSystem(); out[tag]=dict(loads=True,bodies=m.getBodySet().getSize(),coords=m.getCoordinateSet().getSize(),muscles=m.getMuscles().getSize(),locked=sum(c.getLocked(s) for c in m.getCoordinateSet()))
        cs=m.updCoordinateSet(); vals={}
        for f,d in ((0,0),(0.5,0.1),(-0.7,0.3),(1.0,-0.1)):
            cs.get("flexion").setValue(s,f,False); cs.get("deviation").setValue(s,d,False); m.assemble(s); m.realizePosition(s)
            for n in ("FCR","FCU","ECRL","ECRB","ECU","PL"):
                mu=m.getMuscles().get(n); vals[f"{n}_f{f}_d{d}_L"]=mu.getLength(s); vals[f"{n}_f{f}_d{d}_rflex"]=mu.computeMomentArm(s,cs.get("flexion")); vals[f"{n}_f{f}_d{d}_rdev"]=mu.computeMomentArm(s,cs.get("deviation"))
        out[tag]["values"]=vals
    except Exception as e: out[tag]=dict(loads=False,error=str(e)[:300])
json.dump(out,open(sys.argv[1] if len(sys.argv)>1 else "compat.json","w"),indent=1); print(json.dumps({k:(v if k=="opensim_version" else {a:b for a,b in v.items() if a!="values"}) for k,v in out.items()},indent=1))
