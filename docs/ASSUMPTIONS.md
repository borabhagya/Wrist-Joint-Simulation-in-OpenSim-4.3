# Key assumptions
Synthetic minimum-jerk kinematics; hypothetical constant ground-frame hand loads (5/10/20 N dorsal; 5/10 N downward) at the 3rd-MCP centre; fingers/thumb locked; welded shoulder/elbow/radioulnar; forearm fixed horizontal, ulnar side down.
ID computed on a model copy with muscle forces disabled; independent-coordinate moments obtained by constraint projection (flexion: +0.5×wrist_hand_r3 moment; deviation: +d(wrist_hand_r1)/d(deviation)×wrist_hand_r1 moment).
Static Optimization: sum a^2, reserve optimal force 0.01 N m. Forward dynamics: baseline = SO activations at neutral with ECRB/ECU re-tuned for equilibrium; +0.10 agonist pulse; hypothetical, not validated recruitment.
Reactions: Newton–Euler balance of the distal free body; rotational inertia neglected; not cartilage contact stress.
Passive limit elements: effective onset ±60° flexion, −6° radial, +20° ulnar (observed numerically; file labels limits in degrees but values behave as radians).
