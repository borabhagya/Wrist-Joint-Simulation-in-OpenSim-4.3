"""Phase IX: sensitivity analysis.  usage: python 21_sensitivity.py so | fd | num
 so : Static Optimization (quasi-static flexion ramp -30..+30 deg) for load, Fmax (+-20 %, all muscles) and tendon-slack (+-5 %, six wrist muscles) variations, with joint reactions.
 fd : forward-dynamics flexion pulse: excitation amplitude, Fmax, tendon slack, initial activation.   num : integrator accuracy."""
from common import *
from jr import *
import pandas as pd, sys, importlib
mode=sys.argv[1]; SENS=f"{OSF}/sensitivity"; os.makedirs(SENS,exist_ok=True)
if mode=="so":
    SO=importlib.import_module("10_run_so"); D=np.radians
    t=np.arange(0,6.0001,0.1); s_,_,_=minjerk(t/6.0); f=D(-30)+D(60)*s_; m,s=load(WORK); cols,tab=full_pose_table(m,s,t,f,np.zeros_like(f)); write_storage(f"{OSF}/sens_ramp.mot","sens_ramp",cols,tab)
    VAR=[("base_10N",1,1,"Lflex10N_dorsal"),("load_0N",1,1,"L00_unloaded"),("load_5N",1,1,"Lflex5N_dorsal"),("load_20N",1,1,"Lflex20N_dorsal"),
         ("fmax_0.8",0.8,1,"Lflex10N_dorsal"),("fmax_1.2",1.2,1,"Lflex10N_dorsal"),("tsl_0.95",1,0.95,"Lflex10N_dorsal"),("tsl_1.05",1,1.05,"Lflex10N_dorsal")]
    LF={"Lflex10N_dorsal":(0,0,10),"L00_unloaded":(0,0,0),"Lflex5N_dorsal":(0,0,5),"Lflex20N_dorsal":(0,0,20)}
    sel=[x for x in VAR if len(sys.argv)<3 or x[0] in sys.argv[2].split(",")]
    for name,fs,ts,ld in sel:
        mv=osim.Model(WORK)
        for mu in mv.getMuscles():
            mu.setMaxIsometricForce(mu.getMaxIsometricForce()*fs)
            if mu.getName() in WRIST_MUSCLES: mu.setTendonSlackLength(mu.getTendonSlackLength()*ts)
        mp=f"{SENS}/{name}.osim"; mv.printToXML(mp); tag=f"SENS_{name}"
        # SO needs the ramp file + this variant's external load
        at_kin="sens_ramp"
        so=osim.StaticOptimization(); so.setUseModelForceSet(True); so.setActivationExponent(2.0); so.setUseMusclePhysiology(True); so.setConvergenceCriterion(1e-4); so.setMaxIterations(200)
        at=osim.AnalyzeTool(); at.setName(tag); at.setModelFilename(mp); at.setCoordinatesFileName(f"{OSF}/sens_ramp.mot"); at.setLowpassCutoffFrequency(-1); at.setInitialTime(0); at.setFinalTime(6.0); at.setSolveForEquilibrium(True); at.getAnalysisSet().cloneAndAppend(so)
        if ld!="L00_unloaded": at.setExternalLoadsFileName(f"{OSF}/{ld}_ExternalLoads.xml")
        at.setResultsDir(SENS); xml=f"{SENS}/{tag}_setup.xml"; at.printToXML(xml); osim.AnalyzeTool(xml).run(); print("done",name)
elif mode=="so_post":
    m,s=load(WORK); mus=[x.getName() for x in m.getMuscles()]; K=read_storage(f"{OSF}/sens_ramp.mot"); rows=[]
    LF={"base_10N":10,"load_0N":0,"load_5N":5,"load_20N":20,"fmax_0.8":10,"fmax_1.2":10,"tsl_0.95":10,"tsl_1.05":10}
    for name,Fz in LF.items():
        p=f"{SENS}/SENS_{name}_StaticOptimization_force.sto"; pa=f"{SENS}/SENS_{name}_StaticOptimization_activation.sto"
        if not os.path.exists(p): continue
        F=read_storage(p); A=read_storage(pa)
        for fd in (-30,-15,0,15,30):
            j=int(np.argmin(abs(np.degrees(np.interp(F.time,K.time,K.flexion))-fd))); k=K.iloc[(K.time-F.time[j]).abs().argmin()]
            set_pose(m,s,k["flexion"],0); m.realizeDynamics(s); T={n:F[n][j] for n in mus}; res,Rm=reactions(m,s,T,(0,0,Fz)); fr=np.linalg.norm(res["wrist_hand"][0])
            fl=sum(F[n][j] for n in ("FCR","FCU","PL")); ex=sum(F[n][j] for n in ("ECRL","ECRB","ECU"))
            rows.append(dict(variant=name,flexion_deg=fd,F_flexors_N=fl,F_extensors_N=ex,F_wristmuscles_N=sum(F[n][j] for n in WRIST_MUSCLES),F_all_muscles_N=sum(F[n][j] for n in mus),
                act_FCR=A["FCR"][j],act_FCU=A["FCU"][j],act_ECRB=A["ECRB"][j],act_max=A[mus].iloc[j].max(),reserve_Nm=abs(F["flexion_reserve"][j]),wrist_hand_reaction_N=fr))
    R=pd.DataFrame(rows); R.to_csv(f"{CSV}/sensitivity_static_optimization.csv",index=False); print(R[R.flexion_deg==0].round(2).to_string())
elif mode in ("fd","num"):
    from fd_lib import *
    VAR=[("base",{})] if mode=="fd" else []
    if mode=="fd": VAR+=[("amp_0.05",dict(d_ag=0.05)),("amp_0.20",dict(d_ag=0.20)),("fmax_0.8",dict(fmax_scale=0.8)),("fmax_1.2",dict(fmax_scale=1.2)),("tsl_0.95",dict(tsl_scale=0.95)),("tsl_1.05",dict(tsl_scale=1.05)),("a0_x0.5",dict(_a0=0.5)),("a0_x2",dict(_a0=2.0))]
    else: VAR=[("acc_1e-4",dict(_acc=1e-4)),("acc_1e-6",dict(_acc=1e-6))]
    rows=[]
    for name,kw in VAR:
        kb={k:v for k,v in kw.items() if not k.startswith("_")}; m,s=build(case="flexion",**kb); D=run(m,s,tmax=1.2,a0_scale=kw.get("_a0",1.0),acc=kw.get("_acc",1e-5))
        D.to_csv(f"{SENS}/FDSENS_{name}.csv",index=False); i=D.flexion_rad.idxmax()
        rows.append(dict(variant=name,status=D.attrs["status"],peak_flexion_deg=np.degrees(D.flexion_rad.max()),t_peak_s=D.time[i],peak_vel_deg_s=np.degrees(D.flexion_vel.abs().max()),peak_flexor_force_N=max(D.F_FCR.max(),D.F_FCU.max()),final_flexion_deg=np.degrees(D.flexion_rad.iloc[-1]),peak_dev_deg=np.degrees(D.deviation_rad.abs().max()),wall_s=D.attrs["wall_s"])); print(rows[-1])
    pd.DataFrame(rows).to_csv(f"{CSV}/sensitivity_forward_{mode}.csv",index=False)
