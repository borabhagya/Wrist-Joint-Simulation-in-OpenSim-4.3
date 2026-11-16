from common import *
from render import *
import pandas as pd
plt.rcParams.update({"font.size":9,"axes.grid":True,"grid.alpha":0.3,"figure.dpi":150,"savefig.bbox":"tight"})
T = {n: pd.read_csv(f"{CSV}/{n}_trajectory.csv") for n in ["exp1_flexion_extension","exp2_radial_ulnar","exp3_combined"]}
# --- Fig K1: Exp1, Exp2: angle / velocity / acceleration
for n, cols, title, lab in [("exp1_flexion_extension",["flexion"],"Experiment 1: flexion-extension (flexion coordinate)", "Flexion (+) / Extension (-)"),
                            ("exp2_radial_ulnar",["deviation"],"Experiment 2: radial-ulnar deviation (deviation coordinate)", "Ulnar (+) / Radial (-)")]:
    d = T[n]; c = cols[0]; fig, ax = plt.subplots(3, 1, figsize=(7, 7), sharex=True)
    ax[0].plot(d.time_s, d[f"{c}_deg"], "C0"); ax[0].set_ylabel(f"{c} angle (deg)\n{lab}")
    ax[1].plot(d.time_s, np.degrees(d[f"{c}_vel_rad_s"]), "C1"); ax[1].set_ylabel("angular velocity (deg/s)")
    ax[2].plot(d.time_s, np.degrees(d[f"{c}_acc_rad_s2"]), "C3"); ax[2].set_ylabel("angular acceleration (deg/s$^2$)"); ax[2].set_xlabel("time (s)")
    for a in ax: a.axhline(0, color="k", lw=0.5)
    fig.suptitle(title + "\nprescribed piecewise minimum-jerk trajectory"); fig.savefig(f"{FIG}/K_{n}_kinematics.png"); plt.close(fig)
# --- Fig K2: Exp3 combined
d = T["exp3_combined"]; fig, ax = plt.subplots(3, 2, figsize=(10, 7), sharex=True)
for j, c in enumerate(["flexion", "deviation"]):
    ax[0,j].plot(d.time_s, d[f"{c}_deg"], "C0"); ax[0,j].set_ylabel(f"{c} (deg)")
    ax[1,j].plot(d.time_s, np.degrees(d[f"{c}_vel_rad_s"]), "C1"); ax[1,j].set_ylabel("velocity (deg/s)")
    ax[2,j].plot(d.time_s, np.degrees(d[f"{c}_acc_rad_s2"]), "C3"); ax[2,j].set_ylabel("acceleration (deg/s$^2$)"); ax[2,j].set_xlabel("time (s)")
    ax[0,j].set_title(c)
fig.suptitle("Experiment 3: combined movements (F+R, F+U, E+R, E+U)"); fig.savefig(f"{FIG}/K_exp3_combined_kinematics.png"); plt.close(fig)
# --- Fig K3: split between radiocarpal and midcarpal
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
q = np.linspace(-70, 70, 141); ax[0].plot(q, 0.5*q, label="radiocarpal (0.5 x flexion)"); ax[0].plot(q, 0.5*q, "--", label="midcarpal (wrist_hand_r3 = 0.5 x flexion)")
ax[0].set_xlabel("flexion coordinate (deg)"); ax[0].set_ylabel("joint rotation (deg)"); ax[0].set_title("Flexion-extension is split equally between joints"); ax[0].legend()
dv = pd.read_csv(f"{CSV}/deviation_split_radiocarpal_midcarpal.csv"); ax[1].plot(dv.deviation_deg, dv.deviation_deg, label="radiocarpal rot1 (1.0 x deviation)")
ax[1].plot(dv.deviation_deg, dv.wrist_hand_r1_deg, "o-", label="midcarpal wrist_hand_r1 (from constraint)")
ax[1].set_xlabel("deviation coordinate (deg)"); ax[1].set_ylabel("joint rotation (deg)"); ax[1].set_title("Deviation coupling (midcarpal gain 1.5 radial / 1.0 ulnar)"); ax[1].legend()
fig.savefig(f"{FIG}/K_carpal_joint_decomposition.png"); plt.close(fig)
# --- Fig K4: posture renders (radius frame)
m, s = load(); poses = {"neutral":(0,0),"flexion 60":(60,0),"extension 60":(-60,0),"radial 10":(0,-10),"ulnar 25":(0,25)}
cols = ["k","C3","C0","C2","C1"]
fig, ax = plt.subplots(1, 2, figsize=(11, 5))
for (nm,(f,dv_)), c in zip(poses.items(), cols):
    set_pose(m, s, np.radians(f), np.radians(dv_))
    draw(ax[0], m, s, ("y","z"), color=c, lw=1.4, muscles=False); draw(ax[1], m, s, ("x","y"), color=c, lw=1.4, muscles=False)
    ax[0].plot([], [], color=c, label=nm)
ax[0].set_xlabel("y (m): along forearm (distal = negative)"); ax[0].set_ylabel("z (m): +z = dorsal side in this view"); ax[0].set_title("Flexion plane (y-z), radius frame"); ax[0].legend(); ax[0].set_aspect("equal")
ax[1].set_xlabel("x (m)"); ax[1].set_ylabel("y (m)"); ax[1].set_title("Deviation plane (x-y), radius frame"); ax[1].set_aspect("equal")
fig.suptitle("Skeleton schematic (joint-centre segments; bone meshes not supplied)"); fig.savefig(f"{FIG}/K_posture_overlays.png"); plt.close(fig)
set_pose(m, s)
# --- Fig K5: 3D mosaic
combos = {"neutral":(0,0),"F40 + R10":(40,-10),"F40 + U20":(40,20),"E40 + R10":(-40,-10),"E40 + U20":(-40,20)}
fig = plt.figure(figsize=(14, 4.2))
for i, (nm,(f,dv_)) in enumerate(combos.items()):
    ax = fig.add_subplot(1, 5, i+1, projection="3d"); set_pose(m, s, np.radians(f), np.radians(dv_))
    segs, mus, _ = skeleton(m, s)
    for k,(p0,p1) in segs.items(): ax.plot([p0[0],p1[0]],[p0[1],p1[1]],[p0[2],p1[2]],"k",lw=1.3)
    for mu,arr in mus.items(): ax.plot(arr[-5:,0],arr[-5:,1],arr[-5:,2],color=MCOL[mu],lw=1.4)
    ax.set_title(nm, fontsize=9); ax.view_init(20, -60); ax.set_xlim(-0.08,0.08); ax.set_ylim(-0.45,-0.15); ax.set_zlim(-0.12,0.12); ax.set_box_aspect((0.16,0.3,0.24))
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
for mu,c in MCOL.items(): fig.axes[0].plot([],[],color=c,label=mu)
fig.legend(*[fig.axes[0].get_legend_handles_labels()[k] for k in (0,1)], loc="lower center", ncol=6)
fig.suptitle("Combined wrist postures (3D, radius frame, distal wrist-muscle paths)"); fig.savefig(f"{FIG}/K_combined_3d.png"); plt.close(fig)
set_pose(m, s); print("done")
