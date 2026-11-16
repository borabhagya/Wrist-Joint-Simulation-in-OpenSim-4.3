"""Phase IV: prescribed wrist kinematics (Experiments 1-3). Generates .mot files and trajectory CSVs.
Trajectories are piecewise minimum-jerk (zero velocity/acceleration at waypoints) -> synthetic, prescribed motion."""
from common import *
import pandas as pd
m, s = load(); dt = 0.01
D = np.radians
EXPS = {
 "exp1_flexion_extension": ([0,2,4,6,8],[0,D(60),0,-D(60),0],[0]*5),
 "exp2_radial_ulnar":      ([0,2,4,6,8],[0]*5,[0,-D(10),0,D(25),0]),
 "exp3_combined":          ([0,1.5,3,4.5,6,7.5,9,10.5,12],
                            [0,D(40),0,D(40),0,-D(40),0,-D(40),0],
                            [0,-D(10),0,D(20),0,-D(10),0,D(20),0]),
}
summ = []
for name, (tw, fw, dw) in EXPS.items():
    t = np.arange(0, tw[-1]+dt/2, dt)
    f, fd, fdd = waypoints_traj(t, np.array(tw,float), np.array(fw))
    d, dd, ddd = waypoints_traj(t, np.array(tw,float), np.array(dw))
    cols, tab = full_pose_table(m, s, t, f, d)
    write_storage(f"{OSF}/{name}.mot", name, cols, tab)
    df = pd.DataFrame(dict(time_s=t, flexion_rad=f, flexion_deg=np.degrees(f), flexion_vel_rad_s=fd, flexion_acc_rad_s2=fdd,
        deviation_rad=d, deviation_deg=np.degrees(d), deviation_vel_rad_s=dd, deviation_acc_rad_s2=ddd))
    # joint-level decomposition (from constraint-assembled state)
    df["wrist_hand_r1_deg"] = np.degrees(tab[:, cols.index("wrist_hand_r1")]); df["wrist_hand_r3_deg"] = np.degrees(tab[:, cols.index("wrist_hand_r3")])
    df.to_csv(f"{CSV}/{name}_trajectory.csv", index=False)
    # numerical consistency check: finite-difference of position vs analytic velocity
    fd_num = np.gradient(f, dt); dd_num = np.gradient(d, dt)
    summ.append(dict(experiment=name, duration_s=tw[-1], dt_s=dt, n_frames=len(t),
        flex_min_deg=np.degrees(f.min()), flex_max_deg=np.degrees(f.max()), dev_min_deg=np.degrees(d.min()), dev_max_deg=np.degrees(d.max()),
        peak_flex_vel_deg_s=np.degrees(abs(fd).max()), peak_flex_acc_deg_s2=np.degrees(abs(fdd).max()),
        peak_dev_vel_deg_s=np.degrees(abs(dd).max()), peak_dev_acc_deg_s2=np.degrees(abs(ddd).max()),
        max_FD_vs_analytic_vel_err_deg_s=np.degrees(max(abs(fd_num-fd).max(), abs(dd_num-dd).max()))))
S = pd.DataFrame(summ); S.to_csv(f"{TAB}/kinematic_experiments_summary.csv", index=False); print(S.round(2).T.to_string())
# range-of-motion limit check against model coordinate ranges
cs = m.getCoordinateSet()
print("model ranges (deg): flexion", np.degrees([cs.get("flexion").getRangeMin(), cs.get("flexion").getRangeMax()]).round(1),
      "deviation", np.degrees([cs.get("deviation").getRangeMin(), cs.get("deviation").getRangeMax()]).round(1))
