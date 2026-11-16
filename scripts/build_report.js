// Builds 08_Report/Final_Report.docx from results/report_data.json and results/figures/*.png.
// Usage: node build_report.js   (run from scripts/)
const fs = require("fs"), path = require("path");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel, AlignmentType, WidthType, ShadingType, BorderStyle,
  PageBreak, Footer, PageNumber, TableOfContents, LevelFormat } = D;
const ROOT = path.resolve(__dirname, "..");
const data = JSON.parse(fs.readFileSync(path.join(ROOT, "results/report_data.json")));
const figsz = JSON.parse(fs.readFileSync(path.join(ROOT, "results/figs.json")));
const T = data.tables, F = data.facts;
const FONT = "Calibri";
const W = 9026; // A4 content width (DXA) with 1" margins

function runs(text, base = {}) {            // **bold**  and  _italic_  markup
  const out = []; const re = /(\*\*[^*]+\*\*|\^\^[^^]+\^\^|`[^`]+`)/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...base }));
    const tok = m[0]; if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true, font: FONT, ...base })); else if (tok.startsWith("^^")) out.push(new TextRun({ text: tok.slice(2, -2), italics: true, font: FONT, ...base })); else out.push(new TextRun({ text: tok.slice(1, -1), font: "Consolas", ...base, size: (base.size || 22) - 2 }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...base }));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t, o.run || {}), spacing: { after: 120, line: 276 }, alignment: o.align || AlignmentType.JUSTIFIED, ...(o.p || {}) });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: FONT })] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT })] });
const B = t => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs(t), spacing: { after: 60, line: 264 } });
const EQ = t => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 120 }, children: [new TextRun({ text: t, italics: true, font: "Cambria Math", size: 23 })] });
const CAP = t => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: runs(t, { size: 19, italics: false }) });
const NOTE = t => new Paragraph({ spacing: { after: 140 }, shading: { type: ShadingType.CLEAR, fill: "FFF4CE" }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: "C28A00", space: 6 } }, children: runs(t, { size: 20 }) });
const brk = () => new Paragraph({ children: [new PageBreak()] });
let figN = 0, tabN = 0;
function fig(name, caption, widthPx = 600) {
  figN++; const sz = figsz[name]; const h = Math.round(widthPx * sz[1] / sz[0]);
  return [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true, children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(ROOT, "results/figures", name + ".png")), transformation: { width: widthPx, height: h }, altText: { title: name, description: caption, name } })] }),
    CAP(`**Figure ${figN}.** ${caption}  ^^Source: results/figures/${name}.png^^`)];
}
function table(rows, caption, widths) {
  tabN++; const n = rows[0].length; const cw = widths || Array(n).fill(Math.floor(W / n)); const tot = cw.reduce((a, b) => a + b, 0);
  const bd = { style: BorderStyle.SINGLE, size: 4, color: "B0B0B0" }; const borders = { top: bd, bottom: bd, left: bd, right: bd };
  const mk = (txt, j, hdr) => new TableCell({ width: { size: cw[j], type: WidthType.DXA }, borders, margins: { top: 40, bottom: 40, left: 70, right: 70 },
    shading: hdr ? { type: ShadingType.CLEAR, fill: "DCE6F1" } : undefined, children: [new Paragraph({ alignment: AlignmentType.LEFT, children: [new TextRun({ text: String(txt), font: FONT, size: 16, bold: hdr })] })] });
  return [new Paragraph({ keepNext: true, spacing: { before: 120, after: 60 }, children: runs(`**Table ${tabN}.** ${caption}`, { size: 19 }) }),
    new Table({ width: { size: tot, type: WidthType.DXA }, columnWidths: cw, rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, cantSplit: true, children: r.map((c, j) => mk(c, j, i === 0)) })) }),
    new Paragraph({ spacing: { after: 160 }, children: [] })];
}
const ctr = (t, size, bold = false, after = 120) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after }, children: [new TextRun({ text: t, font: FONT, size, bold })] });
const kids = [];
const add = (...x) => x.flat().forEach(e => kids.push(e));

// ---------------- title page
add(new Paragraph({ spacing: { before: 2400 }, children: [] }),
  ctr("Computational Biomechanical Analysis of Wrist Joint Kinematics, Muscle Mechanics and Joint Loading", 40, true, 240),
  ctr("Using the ARMS Wrist–Hand Musculoskeletal Model in OpenSim", 30, false, 480),
  ctr("Technical report — wrist flexion, extension, radial deviation and ulnar deviation", 24, false, 120),
  ctr("Model: Hand_Wrist_Model_for_development.osim (ARMS Lab; OpenSim 4.3 format)", 22, false, 120),
  ctr("Prepared by: bb, Department of Biomedical Engineering, IIT Madras", 22, false, 120),
  ctr("Date: 16 November 2026", 22, false, 600),
  NOTE("**Scope statement.** All motions and external loads in this report are synthetic (prescribed or hypothetical) inputs to a generic musculoskeletal model. No experimental motion, force, EMG or imaging data were used. Agreement with the literature is reported as plausibility, not as experimental validation. Analyses were run in OpenSim 4.6 (Python API); the model file is in OpenSim 4.3 format and was additionally loaded in OpenSim 4.4.1. It has not been run in OpenSim 4.3 itself."),
  brk());
add(new Paragraph({ children: [new TextRun({ text: "Contents", bold: true, size: 32, font: FONT })], spacing: { after: 200 } }),
  ...["1. Abstract","2. Introduction","3. Literature review","4. Anatomical background","5. Musculoskeletal model description","6. Model verification","7. Mathematical formulation","8. Simulation methodology","9. Kinematic analysis","10. Muscle–tendon analysis","11. Inverse dynamics and static optimization","12. Forward dynamics","13. External loading and joint reaction analysis","14. Validation","15. Sensitivity analysis","16. Results summary","17. Discussion","18. Clinical relevance","19. Limitations","20. Conclusion","21. References","22. Appendices (A–E)"].map(s=>new Paragraph({spacing:{after:80},children:[new TextRun({text:s,font:FONT,size:24})]})), brk());

// ---------------- 2 Abstract
add(H1("1. Abstract"),
  P("The ARMS Lab hand–wrist model (43 Millard2012 muscles, 30 bodies, 26 coordinates) was inspected programmatically, copied to a working model, and used to study wrist flexion, extension, radial deviation and ulnar deviation. The two wrist coordinates, `flexion` (±70°) and `deviation` (−10° to +25°), belong to a single coupled `radiocarpal` joint; coupler constraints distribute flexion equally between the radiocarpal and midcarpal (`wrist_hand`) joints and drive the midcarpal radial–ulnar rotation with a gain of 1.5 (radial) or 1.0 (ulnar). Sign conventions were verified geometrically: positive flexion is volar and positive deviation is ulnar."),
  P(`Muscle moment arms were computed over the full ranges (neutral flexion-axis values: FCR +14.9, FCU +14.9, PL +22.7, ECRL −9.7, ECRB −13.3, ECU −6.3 mm) and agreed with the finite-difference definition r = −dL/dθ (median difference ${F.ma_med.toFixed(2)} mm, maximum ${F.ma_max_abs_diff.toFixed(1)} mm). Inverse dynamics on prescribed synthetic motions with hypothetical hand loads (0–20 N) matched an independent virtual-work calculation to ${F.id_max.toExponential(1)} N·m over ${F.id_n} checks. Six Static Optimization runs converged with zero reserve use and a moment-balance error below ${F.so_bal_max.toExponential(0)} N·m; peak activations were 0.13 or less. Forward dynamics with explicit excitations (a posture-holding baseline plus a +0.10 agonist pulse) produced peak excursions of 38.1° (flexion), −25.2° (extension), −8.2° (radial) and 22.4° (ulnar) and reproduced, through inverse dynamics, the simulated muscle moments to an RMS error of 0.03 N·m or less.`),
  P(`Joint reaction forces at the radiocarpal and wrist_hand joints ranged from about 40 to 190 N in the cases studied. OpenSim's JointReaction analysis produced corrupted values in ${F.jra_bad} of ${F.jra_frames} sampled frames and disagreed with an independent Newton–Euler balance by about ${F.jra_late_med.toFixed(0)} N for t ≥ 3.4 s in the loaded case, so the reported reactions are the Newton–Euler results; the OpenSim analysis is documented as a failed validation. Six-muscle maximum isometric moments (10.2, 7.3, 9.5 and 12.2 N·m for flexion, extension, ulnar and radial deviation) lie within one standard deviation of the values reported by Delp et al. (1996). Sensitivity analyses show that tendon-slack length (±5 %) and the initial muscle state dominate the dynamic response, whereas integrator tolerance does not (peak flexion changes by 5×10⁻⁵°).`),
  P("**Keywords:** OpenSim, ARMS model, wrist biomechanics, moment arm, static optimization, forward dynamics, joint reaction."), brk());

// ---------------- 3 Introduction
add(H1("2. Introduction"),
  P("The wrist links the forearm and hand, positions the hand in space and transmits the forces generated by the extrinsic digit muscles. Its functional ranges are large (Ryu et al., 1991) but its mechanics are complex: two rows of carpal bones, two articulating joints (radiocarpal and midcarpal) and a muscle group in which most tendons act about both the flexion–extension and the radial–ulnar axes. Computational musculoskeletal models make these relations quantifiable and provide a way to estimate quantities, such as muscle force and joint loading, that are hard to measure in vivo."),
  P("This report documents an end-to-end modelling study with the open-source ARMS Lab hand–wrist model (McFarland et al., 2023). The work inspects the model files directly, builds a minimally modified working copy, performs kinematic, muscle-mechanics, inverse-dynamics, static-optimization, forward-dynamics and joint-reaction analyses, and checks every stage against independent calculations. The emphasis is on reproducibility and on stating clearly what the model and the inputs can and cannot support."),
  H2("2.1 Objectives"),
  B("Verify the model's wrist kinematic implementation and coordinate sign conventions from the actual file."),
  B("Simulate flexion, extension, radial deviation and ulnar deviation, and combined movements, within model limits."),
  B("Quantify muscle–tendon lengths and moment arms of FCR, FCU, PL, ECRL, ECRB and ECU."),
  B("Estimate net joint moments (inverse dynamics), muscle activations and forces (static optimization), and joint reactions."),
  B("Simulate muscle-driven wrist motion by forward dynamics with explicitly defined excitations."),
  B("Verify numerical consistency, compare with published reference values, and assess sensitivity to key parameters."), brk());

// ---------------- 4 Literature
add(H1("3. Literature review"),
  H2("3.1 Wrist range of motion"),
  P("Ryu et al. (1991) measured wrist motion with a biaxial electrogoniometer during activities of daily living and found that the full battery of tasks could be achieved with 60° of extension, 54° of flexion, 40° of ulnar deviation and 17° of radial deviation; most tasks needed only 70 % of the maximal range, which converts to 40° each of flexion and extension and 40° of combined radial–ulnar deviation. These values are the reference used here for the functional ranges. The ARMS model coordinate ranges (±70° flexion; −10° to +25° deviation) are model limits and differ from these functional values, in particular on the ulnar side."),
  H2("3.2 Radiocarpal and midcarpal mechanics"),
  P("Flexion–extension and radial–ulnar deviation occur through both the radiocarpal and the midcarpal joints. Crisco et al. (2011) reported that the principal mechanical axes of the wrist are oriented obliquely to the anatomical axes, with the primary direction along the dart-thrower's path (radial extension to ulnar flexion). This is relevant because it indicates that the two wrist coordinates of a two-degree-of-freedom model are an anatomical convenience rather than separate physical hinges. The ARMS model reflects this by implementing both coordinates on one `radiocarpal` joint and distributing the rotation to the midcarpal joint through constraints (Section 6.1)."),
  H2("3.3 Muscles, moment arms and strength"),
  P("Gonzalez et al. (1997) showed with a 15-muscle model that peak wrist flexion moment exceeds peak extension moment mainly because of the 110 % larger summed physiological cross-sectional area of the flexors, and that flexion moment varies more with flexion angle because flexor moment arms vary more. Loren et al. (1996) described the biomechanical design of the human wrist motors and its implications for tendon transfers, and Lieber et al. (1990) reported the architecture of selected wrist flexor and extensor muscles. Ramsay et al. (2009) provided reference moment-arm data and a normalised potential-moment index for the 16 primary muscles of the elbow and wrist. Delp et al. (1996) measured maximum isometric moments in ten healthy men: peak flexion moments 12.2 ± 3.7 N·m, extension 7.1 ± 2.1 N·m, radial deviation 11.0 ± 2.0 N·m and ulnar deviation 9.5 ± 2.2 N·m, with passive flexion–extension moments near zero over the central 150° of motion, 0.5 N·m at 90° flexion and 1.2 N·m at 90° extension."),
  H2("3.4 The ARMS model and OpenSim"),
  P("McFarland et al. (2023) describe the ARMS Lab model, an OpenSim (v4.3) model of the hand and wrist with 23 independent degrees of freedom, 43 Hill-type muscle–tendon actuators and passive joint properties, developed by adapting earlier upper-limb work (Holzbaur et al., 2005). The model was evaluated in simulations of grip and pinch strength and of active and passive hand opening. Mirakhorlo et al. (2018) evaluated a different hand and wrist model against reference moment arms (average r = 0.88, RMSD about 23 %), illustrating the level of agreement typically reported. OpenSim (Delp et al., 2007; Seth et al., 2018) provides inverse dynamics, Static Optimization and forward dynamics; the muscle model is the Millard2012 equilibrium muscle (Millard et al., 2013). Static optimization minimises summed squared activation (Anderson and Pandy, 2001), a criterion in the tradition of Crowninshield and Brand (1981)."),
  NOTE("**Reference status.** Entries marked † in the reference list were cited from the author's knowledge and were not re-verified against the publishers' pages in this session; check them before submission. All other entries were confirmed from retrieved records during this work. Cadaveric wrist moment-arm datasets (Nichols et al., 2016, hosted on SimTK) could not be retrieved, so the model moment arms were not compared with them."),
  H2("3.5 Reference ranges and muscle functions"),
  ...table([["Quantity","Published reference","Source"],
    ["Functional extension / flexion","60° / 54° (full task battery); 40° each at 70 % of range","Ryu et al., 1991"],
    ["Functional ulnar / radial deviation","40° / 17° (full task battery)","Ryu et al., 1991"],
    ["Peak isometric flexion / extension moment","12.2 ± 3.7 / 7.1 ± 2.1 N·m","Delp et al., 1996"],
    ["Peak radial / ulnar deviation moment","11.0 ± 2.0 / 9.5 ± 2.2 N·m","Delp et al., 1996"],
    ["Passive flexion–extension moment","≈0 over central 150°; 0.5 N·m at 90° flexion; 1.2 N·m at 90° extension","Delp et al., 1996"],
    ["Passive deviation moment","≈0 radial/neutral; 0.9 N·m at full ulnar deviation","Delp et al., 1996"]], "Published reference values used in this report (not model outputs).", [2800, 4226, 2000]),
  ...table([["Muscle","Principal wrist action(s) (from model moment arms)"],
    ["FCR","Flexion; radial deviation"],["FCU","Flexion; ulnar deviation (largest deviation moment arm among flexors)"],["PL","Flexion (largest flexion moment arm in the model, 22.7 mm at neutral); negligible deviation"],
    ["ECRL","Extension; radial deviation (largest radial arm, −21.2 mm)"],["ECRB","Extension (largest extension arm, −13.3 mm); radial deviation"],["ECU","Ulnar deviation (largest ulnar arm, +25.1 mm); weak extension"]],
    "Functions of the six primary wrist muscles. Actions are taken from the signs of the model moment arms (Section 10), consistent with the roles described by Gonzalez et al. (1997) and Ramsay et al. (2009).", [1500, 7526]), brk());

// ---------------- 5 Anatomy
add(H1("4. Anatomical background"),
  P("The distal radius and ulna articulate with the proximal carpal row (scaphoid, lunate, triquetrum) at the radiocarpal joint. The proximal row articulates with the distal row (trapezium, trapezoid, capitate, hamate) at the midcarpal joint, and the distal row is rigidly bound to the metacarpals. Wrist extensors (ECRL, ECRB, ECU) lie on the dorsal–radial to dorsal–ulnar aspect; the flexors (FCR, PL, FCU) lie on the volar side; the long finger muscles (FDS, FDP, EDC and others) also cross the wrist and contribute to its moments."),
  P("In the ARMS model the carpal bones are not individually articulated: the proximal row is a single body (`proximal_row`, mass 1×10⁻⁴ kg) between the radius and the capitate, and the trapezium, trapezoid and hamate are attached to the capitate by weld-like joints (`cap_trpzm`, `cap_trpzd`, `cap_ham`). The hand mass (0.327 kg) is lumped into the capitate. The labelled anatomical representation is therefore given as a joint-centre schematic (Figure 1); bone meshes (.vtp) were not available in the processing environment, so mesh-based renderings and OpenSim GUI screenshots are not included."),
  ...fig("K_posture_overlays", "Schematic skeleton (wrist and third ray) in the radius frame for neutral, 60° flexion, 60° extension, 10° radial and 25° ulnar deviation. Segments join model joint centres; this is not a bone-mesh rendering.", 560), brk());

// ---------------- 6 Model description
add(H1("5. Musculoskeletal model description"),
  P("The original file `Hand_Wrist_Model_for_development.osim` (OpenSim file version 40000, SHA-256 stored in `original_model/SHA256.txt`) was read directly with the OpenSim Python API and by XML inspection. It contains 30 bodies, 30 joints, 26 coordinates, 43 Millard2012 equilibrium muscles, 3 coupler constraints, 4 CoordinateLimitForce elements (wrist `flexion` and `deviation` ligament and damping elements) and 16 FunctionBasedBushing passive elements (digits and thumb). The total mass is 4.78 kg. The shoulder, elbow and radioulnar joints are weld joints, so the model has no pronation–supination degree of freedom, and the forearm is fixed horizontally with the ulnar side down; gravity (−y in the ground frame) therefore acts in the deviation plane."),
  P("The 26 coordinates comprise the 23 independent coordinates shown in the OpenSim GUI (two wrist, four thumb, 4cmc_flexion, and 16 finger coordinates) plus three dependent coordinates generated by constraints (`wrist_hand_r1`, `wrist_hand_r3`, `CMC5_r1`), which are not shown as free coordinates in the GUI. This reconciles the 23 coordinates visible in the GUI with the 26 found in the file."),
  ...table(T.muscles, "Parameters of the six primary wrist muscles, read from the model file (millimetres; Millard2012EquilibriumMuscle). MTU = muscle–tendon unit.", [800, 900, 900, 1000, 900, 1300, 1300, 1926]),
  P("All six wrist muscles originate on the humerus and insert on the capitate (PL on the third metacarpal), so each also spans the elbow and radioulnar joints, which are welded in this model and therefore do not contribute moment arms."), brk());

// ---------------- 7 Verification
add(H1("6. Model verification"),
  H2("6.1 Wrist kinematic implementation"),
  P("The `flexion` and `deviation` coordinates are both defined on the `radiocarpal` CustomJoint (motion type: coupled). Reading the joint and constraint definitions gives the following mechanical implementation."),
  B("**Radiocarpal joint:** rotation about an axis (0.956, −0.252, 0.147) is driven by 0.5 × `flexion`; rotation about (−0.819, −0.136, −0.557) is driven 1:1 by `deviation` (axes expressed in the parent frame; they are not orthogonal)."),
  B("**Midcarpal joint (`wrist_hand`):** `wrist_hand_r3 = 0.5 × flexion` (linear coupler, ±1.222 rad → ±0.611 rad), so total flexion is the sum of two equal halves; `wrist_hand_r1` follows `deviation` through a three-point spline (−10° → −15°, 0 → 0, +25° → +25°), i.e. a gain of 1.5 on the radial side and 1.0 on the ulnar side."),
  B("**Passive elements:** `flexion_ligaments` and `deviation_ligaments` (CoordinateLimitForce) and velocity damping elements; Section 14.2 describes their effective limits."),
  ...fig("K_carpal_joint_decomposition", "Distribution of the wrist coordinates over the radiocarpal and midcarpal joints (from the constraint definitions and computed state).", 580),
  H2("6.2 Sign conventions"),
  P("Conventions were verified geometrically rather than assumed. Applying +0.3 rad to `flexion` moved the third-metacarpal origin 13.7 mm towards the volar side (the side of the FCR/FCU/PL tendons), and −0.3 rad moved it dorsally; +0.3 rad of `deviation` moved the origin towards the side of the ECU/FCU tendons (ulnar), −0.1 rad towards the radial side. The signs of the moment arms agree: FCR, FCU and PL have positive flexion-axis arms; ECRL, ECRB and ECU negative. **Positive `flexion` = flexion; negative = extension. Positive `deviation` = ulnar; negative = radial.** This matches the ARMS tutorial table (flexed posture +0.175 rad, extended −0.820 rad, ulnar +0.297 rad, radial −0.017 rad). All coordinates are stored in radians in the model and motion files."),
  H2("6.3 Model validity checks"),
  B("The model initialises (`initSystem`) without errors; all 43 muscle–tendon lengths are finite at the default pose."),
  B("The model references 65 mesh files (.vtp/.obj) that were not present in the processing environment; this affects visualisation only, not the dynamics."),
  B("Finger and thumb coordinates have small non-zero defaults (up to 0.011 rad for `CMC5_r1`, and 0.2–0.5 % of range for several phalangeal angles). These were left unchanged."),
  B("Carpal bodies have very small masses and inertias (proximal row 1×10⁻⁴ kg; trapezium/trapezoid/hamate of order 10⁻⁵ kg). They are numerically stiff but caused no integration failures."),
  B("Extrinsic finger muscles have a default activation of 1.0 in the original file. Forward dynamics therefore requires explicit controls (Section 8.6)."), brk());

// ---------------- 8 Math
add(H1("7. Mathematical formulation"),
  P("Joint angle, velocity and acceleration are the coordinate and its time derivatives; with q in radians, ω = dq/dt in rad/s and α = d²q/dt² in rad/s². Moment arms follow from the virtual-work relation"),
  EQ("r_i(q) = − ∂L_i / ∂q       (L_i = muscle–tendon length, q in rad)"),
  P("and the muscle-generated generalised force on a coordinate is"),
  EQ("τ_muscle = Σ_i r_i F_i^T"),
  P("where F_i^T is the tendon force. The multibody equations of motion are"),
  EQ("M(q) q̈ + C(q, q̇) + G(q) = τ"),
  P("Inverse dynamics solves this equation for τ given q, q̇ and q̈. The required τ is taken on the independent coordinates by projecting the generalised forces of the constraint-dependent coordinates through the coupler gains: τ_flex = τ_flexion + 0.5 τ_wrist_hand_r3 and τ_dev = τ_deviation + (∂q_r1/∂deviation) τ_wrist_hand_r1. Static optimization solves, at each time step,"),
  EQ("min Σ_i a_i²      subject to      Σ_i r_i F_i(a_i, l_i) + Σ reserve = τ_required"),
  P("with F_i(a_i, l_i) from the muscle force–length–velocity relations (activation exponent 2; reserve actuators with optimal force 0.01 N·m). An external force F applied at a point at position r from the joint centre produces the torque"),
  EQ("τ_ext = r × F"),
  P("Joint reaction forces are obtained by Newton–Euler balance of the free body distal to a joint. For the group of bodies i distal to the joint, with muscle path forces f_k acting at points p_k on these bodies, external force F_ext at the point p_e, gravity g and joint centre c,"),
  EQ("F_R = −( Σ_k f_k + F_ext + Σ_i m_i g ) + Σ_i m_i a_i        M_R = −( Σ_k (p_k − c) × f_k + (p_e − c) × F_ext + Σ_i (x_i − c) × m_i g ) + Σ_i (x_i − c) × m_i a_i"),
  P("F_R is the force applied by the parent body on the distal group; both vectors are reported in the radius frame (x: radial–ulnar side axis, y: along the forearm, z: dorsal–volar) with magnitudes F_res = √(Fx²+Fy²+Fz²). Rotational inertia terms are neglected: for the slow prescribed motions (peak angular acceleration ≤ 1.9 rad/s²) they are below 0.01 N·m (an estimate using an effective inertia of about 1.6×10⁻³ kg·m²); for the abrupt radial forward-dynamics case (peak acceleration ≈ 300 rad/s²) they could reach about 0.5 N·m, so reaction moments there are approximate. These are joint reaction loads, not cartilage contact pressures; no contact model was implemented."), brk());

// ---------------- 9 Methodology
add(H1("8. Simulation methodology"),
  H2("8.1 Working model and modifications"),
  P("A separate working model (`working_model/ARMS_wrist_working.osim`) was created by text edits of the original so that the OpenSim 4.3 file format is preserved. Two modifications were made (also in `results/tables/model_modifications.csv`); nothing else was changed, including the licence header."),
  ...table([["ID","Item","Original","Modified","Reason / expected effect"],
    ["M1","21 independent finger and thumb coordinates","locked = false","locked = true","Study focuses on the wrist; fixes digit posture so ID, SO and FD have two free coordinates. Wrist-coupled dependent coordinates left unlocked."],
    ["M2","ForceSet: flexion_reserve, deviation_reserve (CoordinateActuator)","absent","optimal force 0.01 N·m, control ±10⁴","Reserve actuators for Static Optimization; heavily penalised so they act only if muscles cannot balance the moment."]],
    "Model modifications.", [500, 2200, 1200, 1700, 3426]),
  P(`Verification: the working model loads and initialises, 21 of 26 coordinates are locked, muscle–tendon lengths differ from the original by at most 1.4×10⁻⁷ m and moment arms by at most 3.7×10⁻¹⁰ m at five test poses, and the total mass is unchanged. The model was also loaded in OpenSim 4.4.1 and reproduced the same lengths and moment arms as OpenSim 4.6 to within 2×10⁻¹⁷ (72 values per model; results/compat/).`),
  H2("8.2 Neutral configuration"),
  P("The neutral wrist is `flexion` = `deviation` = 0 (the model default; stored values 0.000 rad). At neutral, the hand tip lies in the plane of the forearm to within the model's initial finger offsets."),
  H2("8.3 Kinematic experiments"),
  P("Trajectories are piecewise minimum-jerk curves through waypoints, so velocity and acceleration are zero at each waypoint. For every frame the two wrist coordinates were set, the coupler constraints assembled, and all 26 coordinate values written to a `.mot` file (radians, 100 Hz for Experiments 1–3; 50 Hz for the dynamic inputs). Velocities and accelerations are analytic and agree with finite differences. **These are synthetic prescribed motions, not measurements.**"),
  ...table(T.kin, "Kinematic inputs. Experiments 1–3 are kinematic only; `dyn_flexext` and `dyn_dev` stay inside the passive-limit-free band and feed ID, SO and joint reactions.", [1900, 700, 700, 1100, 1100, 1800, 1726]),
  P("Experiment 3 (combined movements: flexion/extension with radial/ulnar deviation, ±40° flexion with −10° radial or +20° ulnar) was generated and plotted for kinematics and posture only; no dynamic analyses were run on it."),
  H2("8.4 External loads"),
  P("Hypothetical constant ground-frame forces were applied at the third-MCP joint centre (point fixed in the third metacarpal frame, (0.0002, −0.0263, 0.0018) m): 5, 10 or 20 N in the dorsal direction (+z ground) for the flexion–extension motion, and 5 or 10 N vertically downward for the deviation motion. In the model's posture, ground +z is dorsal and ground −y (gravity) is ulnar. The external torque about the flexion axis at neutral for 10 N is 0.71 N·m (virtual work), consistent with an effective lever arm of about 7 cm."),
  H2("8.5 Inverse dynamics, Static Optimization, reactions"),
  P("Inverse dynamics (OpenSim InverseDynamicsTool, no filtering of the synthetic trajectories) was run on a copy of the working model with every muscle and reserve force disabled. This step was necessary: with the tool's default exclusion, muscle passive force remained in the model and produced a spurious −1 N·m at 45° extension; disabling muscle force made the output equal to the virtual-work statics (Section 11.2). Static Optimization used OpenSim's StaticOptimization analysis (activation exponent 2, muscle physiology on, convergence 10⁻⁴) with the same kinematics and external loads. Joint reactions were computed by Newton–Euler balance (Section 7) from the Static Optimization tendon forces, and compared with OpenSim's JointReaction analysis (Section 13.1)."),
  H2("8.6 Forward dynamics"),
  P("Forward dynamics used the OpenSim Manager (Runge–Kutta–Merson, accuracy 10⁻⁵) with a PrescribedController that supplies an excitation to all 45 actuators. **Initial condition:** neutral posture, zero velocity, initial activation equal to the baseline excitation, fibre lengths equilibrated. **Baseline excitation:** the Static Optimization activations at t = 0 of the unloaded run, with ECRB and ECU re-tuned (0.085 and 0.045) so that the forward model's muscle moments equal the neutral posture-holding moments from inverse dynamics (flexion 0.012 N·m, deviation −0.173 N·m; residual <10⁻³ N·m); without this adjustment the neutral posture was not an equilibrium and the hand drifted (a first test reached 17° flexion in 1 s). With the tuned baseline the unperturbed model remains at 0.0° for 1.2 s. **Movement:** the agonists receive +0.10 excitation (ramps 0.05 s, plateau 0.1–0.4 s) for flexion (FCR, FCU, PL), extension (ECRL, ECRB, ECU), radial deviation (FCR, ECRL, ECRB) and ulnar deviation (FCU, ECU); duration 1.2 s. These excitations are hypothetical control inputs chosen to produce visible motion within range; they are not a physiologically validated recruitment pattern."), brk());

// ---------------- 10 Kinematic analysis
add(H1("9. Kinematic analysis"),
  P("Experiments 1 and 2 span the model ranges: ±60° flexion/extension and −10° to +25° deviation. Figure 3 shows the time histories of Experiment 1; the posture renders for combined movements are in Figure 4. In the extreme combined postures (flexion 40° with 20° ulnar deviation, etc.) the distal rays move towards −z (volar) for flexion and +z for extension, consistent with the sign conventions."),
  ...fig("K_exp1_flexion_extension_kinematics", "Experiment 1 (flexion–extension): angle, angular velocity and angular acceleration of the `flexion` coordinate (prescribed minimum-jerk trajectory).", 440),
  ...fig("K_combined_3d", "Combined postures (neutral, flexion 40° + radial 10°, flexion 40° + ulnar 20°, extension 40° + radial 10°, extension 40° + ulnar 20°) with distal wrist-muscle paths; radius frame; schematic.", 600),
  ...fig("C_four_movement_kinematics", "Comparison of the four movements used for the dynamic analyses (flexion and extension from `dyn_flexext`; radial and ulnar deviation from `dyn_dev`).", 600),
  NOTE("**Range caveat.** Experiment 2 reaches −10° radial and +25° ulnar deviation, which lie beyond the model's passive limit onset (−6° and +20°; Section 14.2). The kinematic experiment is unaffected because the coordinates are prescribed, but dynamic analyses were restricted to −5°…+15° (deviation) and ±45° (flexion)."), brk());

// ---------------- 11 Muscle-tendon
add(H1("10. Muscle–tendon analysis"),
  P(`Moment arms were obtained from OpenSim's computeMomentArm over flexion −70°…+70° (2.5° steps, deviation 0) and deviation −10°…+25° (1.25° steps, flexion 0), and verified against the finite-difference definition r = −dL/dθ at ${F.ma_n} points (median difference ${F.ma_med.toFixed(3)} mm; maximum ${F.ma_max_abs_diff.toFixed(2)} mm, ECU near −25° flexion; the ECU path has a wrapping surface in that region but the cause was not isolated).`),
  ...table(T.momentarm, "Moment arms of the six wrist muscles (mm; positive = flexor or ulnar, negative = extensor or radial).", [1000, 1300, 1900, 1900, 1300, 1626]),
  ...fig("M_momentarms_wrist_muscles", "Moment arms versus flexion angle (left, deviation = 0) and versus deviation angle (right, flexion = 0). Source: results/csv/momentarm_vs_flexion.csv and momentarm_vs_deviation.csv.", 600),
  P("**Interpretation.** The flexors have positive flexion-axis moment arms that rise with flexion for FCU (10.8 mm at −70° to 18.2 mm at +70°), whereas PL peaks near +25° (24 mm) and falls steeply beyond 60° flexion. The extensors ECRL and ECRB have larger extension arms in extension (ECRL −14.6 mm at −70°, −7.6 mm at +70°), so their leverage declines as the wrist flexes. ECU has a small extension arm that changes sign near −58° (+2.2 mm at −70°), i.e. at extreme extension it acts weakly as a flexor in this model. About the deviation axis, ECU (+25.1 mm) and FCU (+21.8 mm) are the main ulnar deviators and ECRL (−21.2 mm) and ECRB (−13.3 mm) the main radial deviators; FCR contributes about −7.5 mm throughout. The ulnar deviators lose leverage as the wrist deviates ulnarly (FCU 21.8 → 10.9 mm; ECU 25.1 → 18.5 mm), while ECRL and ECRB lose leverage towards ulnar deviation as well (ECRB −13.3 → −0.7 mm). Kinks near −22° flexion in ECRL, ECU and PL arise from changes in wrapping-surface contact."),
  P("Because nearly every muscle acts about both axes, the pure-flexion or pure-deviation actions require co-contraction: for example, flexion with FCR alone produces a radial deviation tendency that FCU (and in extension ECU) cancel. This is the mechanism by which antagonistic muscles also stabilise the wrist: co-contraction increases joint stiffness and compressive loading while keeping the net moment at the demanded value."),
  ...fig("M_neutral_two_axis", "Two-axis action of the six wrist muscles at the neutral posture.", 360),
  ...fig("M_mtu_length_change", "Change in muscle–tendon length from neutral versus flexion (left) and deviation (right).", 580),
  P("Muscle–tendon length changes are largest for the flexors and extensors during flexion–extension and account for the passive muscle tension that appears at extreme postures (Section 11.3)."), brk());

// ---------------- 12 ID & SO
add(H1("11. Inverse dynamics and static optimization"),
  H2("11.1 Inverse dynamics"),
  P("Net muscle-required moments (including all passive non-muscle elements) are shown for each movement in Figures 9–12. In the model's posture the flexion plane is horizontal, so the unloaded flexion moment is small (≤ 0.04 N·m) and the unloaded deviation moment is dominated by the weight of the hand (about 0.17–0.20 N·m, gravity pulling the hand into ulnar deviation, which muscles must oppose with radial deviators). A 10 N dorsal force at the third MCP requires 0.57–0.74 N·m of flexion moment; 5 N and 20 N give 0.39 and 1.45 N·m. A 10 N downward force requires −0.99 N·m about the deviation axis at 5° radial deviation. Coordinate conventions: positive flexion moment = flexor; positive deviation moment = ulnar."),
  H2("11.2 Verification of inverse dynamics"),
  P(`The projected inverse-dynamics moments were compared with a virtual-work statics calculation (τ = d/dq of gravitational and external-load potential, finite differences with constraints assembled) at the zero-velocity, zero-acceleration waypoints of every kinematics–load combination: ${F.id_n} checks, maximum difference ${F.id_max.toExponential(1)} N·m, median ${F.id_med.toExponential(1)} N·m (validation figure, Section 14). This is a numerical consistency check, not an experimental validation.`),
  H2("11.3 Static optimization: convergence and consistency"),
  P(`Six runs were completed (401 frames each): flexion–extension with 0, 5, 10 and 20 N and deviation with 0 and 10 N. In every run all outputs are finite, activations are bounded between 0.01 (the model minimum) and 0.13, reserve actuator forces are zero and the muscle moments plus reserve equal the required moment with a maximum error of ${F.so_bal_max.toExponential(1)} N·m. Peak tendon forces range from 10 N (unloaded deviation) to 49 N (20 N load). The low activations reflect the small demanded moments relative to the muscles' capacity (Section 14.1); passive muscle force provides a substantial part of the required moment at extreme postures.`),
  ...table(T.so, "Static optimization verification (all six runs). Reserve columns are flexion / deviation reserve peaks.", [1900, 800, 800, 1100, 800, 1000, 1000, 1626]),
  ...table(T.so_ext, "Wrist-muscle activation (tendon force in N) and net moments at the point of maximum excursion of each movement (10 N loads). Peak values over the whole segment occur at the neutral endpoints and are listed in results/tables/so_movement_peaks.csv.", [1500, 1000, 900, 900, 900, 900, 900, 900, 1126]),
  ...fig("P_movement_flexion", "Flexion (0–45°–0, 10 N dorsal load): joint kinematics, Static Optimization activation and force, moment arms, inverse-dynamics moment, and joint reaction force and moment. Synthetic prescribed motion.", 600),
  ...fig("P_movement_extension", "Extension (0 to −45° and back, 10 N dorsal load): same quantities as Figure 9.", 600),
  ...fig("P_movement_radial", "Radial deviation (0 to −5° and back, 10 N downward load).", 600),
  ...fig("P_movement_ulnar", "Ulnar deviation (0 to +15° and back, 10 N downward load).", 600),
  P("**Interpretation.** With the dorsal load the required flexion moment is met mostly by FCR, whose activation rises towards extension (0.011 at 45° flexion to 0.070 at 45° extension, force 2.5 → 28 N): as the wrist extends, flexor moment arms and passive tension change, and the optimiser recruits more flexor force. In flexion the extensor ECU (0.044) is recruited to balance passive flexor tension, an example of agonist–antagonist co-contraction forced by the passive muscle forces. For deviation, ECRL and ECRB provide the radial-deviation moment that opposes ulnar gravity and the downward load (ECRL activation 0.085–0.10, 27–31 N). The solutions are those of a quadratic-activation criterion; they are not recorded muscle activities and the optimiser's smooth-looking activations contain small discontinuities where the active set of muscles changes."),
  H2("11.4 Antagonist co-contraction and stability"),
  P("In every run several antagonists carry non-zero force simultaneously (for example ECU with FCR in the dorsal-load case). In the model this is partly passive: stretched muscles carry force even at the minimum activation of 0.01. Physiologically, co-contraction of antagonists stiffens the joint, which resists perturbations and joint-surface separation at the cost of increased compression. The model's reactions (Section 13) show this cost: unloaded postures already carry 40–65 N of compression because of muscle tension."),
  ...fig("C_peak_muscle_by_movement", "Peak activation (left) and tendon force (right) of the six wrist muscles for each movement (10 N loads). Peaks coincide with the neutral endpoints for deviation.", 560),
  ...fig("C_loading_comparison", "Effect of external loading on the flexion–extension run: inverse-dynamics moment, FCR activation, summed wrist-muscle force and wrist_hand reaction force for 0, 5, 10 and 20 N.", 520), brk());

// ---------------- 13 Forward dynamics
add(H1("12. Forward dynamics"),
  P("Section 8.6 describes the setup. Integration completed for all five cases without failure; 1.2 s of simulation took about 20–25 s of wall time. The unperturbed baseline remained at 0.0° (peak speed 0.03 °/s), confirming the equilibrium initial condition."),
  ...table(T.fd, "Forward-dynamics results. FD→ID RMS error: root-mean-square difference between the muscle moment about the primary axis in the simulation and the moment recovered by running inverse dynamics on the simulated motion.", [1100, 1300, 800, 900, 1000, 1000, 1000, 900, 1026]),
  ...fig("FD_flexion", "Forward dynamics, flexion pulse: joint angles, velocity, acceleration, excitation and activation, muscle force, joint moments, joint reaction force and moment, and trajectory in coordinate space.", 600),
  ...fig("FD_extension", "Forward dynamics, extension pulse. The passive deviation limit is engaged at about −7.5° radial deviation, where a coupled radial drift occurs.", 600),
  ...fig("FD_radial", "Forward dynamics, radial-deviation pulse. The hand reaches the passive radial limit (−6°) within 0.2 s; the 1.7 N·m limit torque stops it abruptly.", 600),
  ...fig("FD_ulnar", "Forward dynamics, ulnar-deviation pulse.", 600),
  ...fig("C_forward_dynamics_comparison", "Comparison of the four forward-dynamics movements (primary joint angle, velocity, acceleration, summed wrist-muscle force, muscle moment, reaction force).", 600),
  P("**Observations.** A +0.10 flexor pulse produced 38° of flexion at 0.47 s with a peak speed of 208 °/s (3.6 rad/s). After the pulse ended (0.45 s) passive moments and gravity returned the hand toward neutral: 9.5° of flexion remained at 1.2 s (extension −0.2°, radial −4.8°, ulnar 6.2° at 1.2 s). Extension reached −25° with radial drift to −7.5°, so the passive limit (0.38 N·m) was touched. The radial pulse drove the hand into the passive radial limit at −8.2°, giving a peak limit torque of 1.68 N·m and an impact-like acceleration; this case is therefore a limit-contact simulation and not a smooth movement. Ulnar deviation reached 22.4°, slightly beyond the passive onset (20°, 0.24 N·m). The coupling between axes is visible: flexion pulses induce up to 4.9° of radial deviation and the radial pulse 2.5° of flexion. Forward and inverse dynamics are consistent (RMS 0.003 N·m or less for flexion, extension and ulnar; 0.03 N·m, with a maximum of 0.26 N·m, for the radial case, where the stiff limit contact at 100 Hz sampling makes the spline-based accelerations in the inverse-dynamics check inaccurate)."), brk());

// ---------------- 14 Reaction
add(H1("13. External loading and joint reaction analysis"),
  P("Reactions were computed at two joints: **radiocarpal** (force and moment applied by the radius on the proximal carpal row and everything distal to it) and **wrist_hand** (applied by the proximal row on the capitate and everything distal to it). Both are expressed in the radius frame and referred to the joint centre. They are net loads transmitted through the whole joint, not cartilage contact forces or pressures."),
  ...table(T.jr, "Joint reaction summary for the Static-Optimization cases (Newton–Euler balance). Axial compression is the component along the forearm axis.", [1300, 1500, 1300, 1400, 1000, 1500, 1026]),
  P("In the unloaded cases the radiocarpal reaction is 56–66 N and falls to 38–44 N at the minimum, so most of the compression comes from muscle tension (including finger extrinsics), not from the 5.7 N weight of the distal segment. A 10 N dorsal load raises the peak reaction by about 12 N and a 20 N load by about 62 N relative to unloaded; the 5 N case is lower than unloaded (wrist_hand 54 vs 64 N) because the optimiser re-distributes muscle force (extensor force is reduced when the load already requires flexor activity). The reaction moments (≤ 0.4 N·m) are small because the muscles balance the net moment about the two free axes; the residual moment is carried by the carpal articulation. With explicit excitations (forward dynamics) the reactions reached 98–192 N, the largest values occurring for the limit-contact radial and the extension cases (Table 9)."),
  H2("13.1 Comparison with OpenSim's JointReaction analysis"),
  P(`OpenSim's JointReaction analysis (JointReaction on the radiocarpal and wrist_hand joints, child body, expressed in the radius frame, driven by the Static Optimization force file) was run for the 10 N dorsal flexion–extension case. Of ${F.jra_frames} frames compared, ${F.jra_bad} contained corrupted values (|F| > 10³ N; identical in repeated runs). For t < 1.2 s the clean frames agree with the Newton–Euler result (median difference 2×10⁻⁵ N, maximum ${F.jra_early_max.toFixed(2)} N) and an independent force balance on the distal group (muscle path forces on distal bodies + weight + external load + reaction = 0) closes to ${F.jr_fb_early.toExponential(1)} N at t = 0 and 2 s. For t ≥ 3.4 s the OpenSim output differs by a median of ${F.jra_late_med.toFixed(1)} N (maximum ${F.jra_late_max.toFixed(1)} N), about the magnitude of the 10 N external load, at identical postures and muscle forces that agree with t = 0; the cause was not isolated (a loss of the external load at later times is a plausible but unconfirmed explanation). **The OpenSim JointReaction output was therefore not used for the reported results.** A zero-muscle-force negative control (distal-segment weight only) also disagreed (4.0 N versus 5.7 N expected), because without muscle forces the model is not in equilibrium about its two free coordinates and the analysis is not meaningful there; this control is retained in results/tables/jra_zero_force_check.csv for transparency.`),
  brk());

// ---------------- 15 Validation + sensitivity
add(H1("14. Validation"),
  P("Validation is of two kinds. **Numerical consistency checks** (moment arms versus finite differences, inverse dynamics versus virtual work, Static Optimization moment balance, forward-to-inverse dynamics, integrator tolerance, cross-version loading) establish that the calculations are internally consistent. **Plausibility comparisons** with published values (below) indicate whether model outputs are of a realistic magnitude. Neither is validation against experimental data from the simulated scenarios, and none is subject-specific."),
  ...fig("V_validation_panel", "Numerical verification panel: moment arms (OpenSim versus finite difference), inverse dynamics versus virtual work, Static Optimization moment balance, and forward-to-inverse dynamics consistency (log scale).", 600),
  H2("14.1 Maximum isometric moments"),
  P("With the wrist at neutral and all muscles at minimum activation as the reference, the six primary wrist muscles were set to full activation in the direction of each movement (equilibrated tendon-compliant fibre states) and the resulting joint moment, relative to rest, was compared with Delp et al. (1996). The six-muscle moments lie within one standard deviation of the reference for all four movements. Activating all muscles that act in the movement direction (including the finger extrinsics, with the fingers locked in extension) over-predicts the reference by 1.6–2.6×, which shows that finger muscles contribute substantially to wrist moments in the model and that the comparison depends on which muscles are included."),
  ...table(T.val_moment, "Maximum isometric moments at neutral: model versus Delp et al. (1996) (10 healthy men; peak over wrist angles). Model value = moment change relative to the minimum-activation state.", [1500, 2000, 1800, 2000, 1726]),
  H2("14.2 Range of motion and passive moments"),
  P("The model flexion limit (±70° coordinate range; passive limit onset at ±60°) lies above the functional ranges of Ryu et al. (1991) (60° extension, 54° flexion); the ulnar limit (+25° coordinate range, onset +20°) is below the 40° functional ulnar deviation, and the radial limit (−10° range, onset −6°) is below the 17° functional radial deviation. The simulated motions in the dynamic analyses (±45° flexion; −5° to +15° deviation) are within both the model and the functional ranges except for the radial excursions of Experiment 2. The passive limit torques of the model are much larger than the in-vivo passive moments reported by Delp et al. (1996) at comparable ends of motion: the model's flexion limit torque is 21 N·m at +70° and 14 N·m at −70° (zero at ±60° and below), and the radial limit reaches 17.7 N·m at −10°, versus 0.5–1.2 N·m at 90° of flexion or extension in vivo. The limit elements are stiff end-stops rather than anatomical passive moments; the limit onset values are also those found numerically, because the file labels them in degrees while the stored values behave as radians. Limit-engaged simulations (radial FD; Experiment 2 beyond −6°) should therefore be interpreted as end-stop contact."),
  ...fig("M_passive_limit_torque", "Passive limit torque of the flexion_ligaments (left) and deviation_ligaments (right) elements versus angle. Source: results/csv/passive_flexion_ligament_torque.csv and passive_deviation_ligament_torque.csv.", 520),
  H2("14.3 Moment arms and joint reactions"),
  P("No numerical comparison of the model moment arms with cadaveric datasets was possible (the SimTK datasets were not retrievable), so the moment arms are verified for internal consistency only. Qualitatively, their pattern matches Gonzalez et al. (1997): flexor arms vary strongly with flexion angle and extensor arms less so. No published in-vivo wrist joint reaction values for these scenarios were retrieved, so the 40–190 N magnitudes are not validated; they are plausible in order of magnitude for muscle-dominated compressive loading but should be treated as model estimates."),
  H1("15. Sensitivity analysis"),
  P("Static Optimization sensitivity used a quasi-static flexion ramp from −30° to +30° (6 s, 10 N dorsal load unless stated) and compared loads, maximum isometric force (×0.8, ×1.2, all muscles) and tendon slack length (×0.95, ×1.05, six wrist muscles). Forward-dynamics sensitivity used the flexion pulse and varied pulse amplitude, F_max, tendon slack length and initial activation (×0.5, ×2), and the integrator accuracy (10⁻⁴, 10⁻⁶)."),
  ...table(T.sens_so, "Static Optimization sensitivity at 0° flexion (all variants: reserve actuator force = 0).", [1700, 1500, 1700, 1300, 1500, 1326]),
  ...table(T.sens_fd, "Forward-dynamics sensitivity (flexion pulse). The final rows are the integrator-accuracy tests.", [1700, 1300, 1200, 1200, 1700, 1926]),
  ...fig("S_static_optimization_sensitivity", "Static Optimization sensitivity to load, F_max and tendon slack length across the flexion ramp.", 600),
  ...fig("S_forward_dynamics_sensitivity", "Forward-dynamics sensitivity of peak flexion and peak flexor force to the parameter variations.", 560),
  P("**Findings.** (i) In Static Optimization, increasing the load from 0 to 20 N raised the flexor force from 8 to 61 N at neutral and the wrist_hand reaction from 48 to 117 N; ±20 % in F_max changed the reaction by −6 % and +9 % but left reserves at zero; a +5 % tendon slack length cut flexor force to 11 N (−66 %), because a longer tendon shifts the muscles to shorter fibre lengths and lower passive force, so the effect is large for a small change in a poorly known parameter. (ii) In forward dynamics, pulse amplitude is the most direct control (0.05, 0.10, 0.20 gives 26°, 38°, 48°); F_max ±20 % changes the peak by about ±1°; tendon slack ±5 % changes it by +6° and −25° (44° and 13°), mostly because the neutral posture is no longer an equilibrium (initial accelerations of −66 and −25 rad/s² versus 0.07 for the baseline); (iii) the initial activation (×0.5, ×2) leaves the peak unchanged (38.1°, 38.0°) but produces initial accelerations of +150 and −100 rad/s², so only the first 0.1 s differs; (iv) integrator tolerance has no practical effect (38.052° at 10⁻⁴, 10⁻⁵ and 10⁻⁶). The model's output is thus most sensitive to the passive/tendon properties that set the resting equilibrium and least to integration settings. Because the baseline activations were tuned for the nominal parameters, the parameter-variation rows combine a change in the dynamics with a loss of equilibrium; a re-tuned baseline per variant would isolate the pure parametric effect and was not done."),
  H2("15.1 Uncertainty and assumptions"),
  B("Synthetic kinematics and loads; no measured data."),
  B("Muscle properties, moment arms and passive elements are generic (not subject-specific); no parameter uncertainty distributions were propagated."),
  B("Fixed fingers and thumb, welded shoulder–elbow–forearm, fixed forearm orientation; gravity direction set by the model's posture."),
  B("Static Optimization ignores activation dynamics and assumes the quadratic-activation criterion; reserve actuators were unused."),
  B("Reaction moments neglect rotational inertia (Section 7)."), brk());

// ---------------- Results synthesis, discussion, clinical, limitations, conclusion
add(H1("16. Results summary"),
  B("Wrist flexion and extension are generated by two radiocarpal rotations driven by `flexion` (half each in radiocarpal and midcarpal joints); deviation is a radiocarpal rotation plus a midcarpal rotation with a 1.5 radial gain."),
  B("Neutral moment arms: flexion axis FCR 14.9, FCU 14.9, PL 22.7, ECRL −9.7, ECRB −13.3, ECU −6.3 mm; deviation axis FCR −7.5, FCU +21.8, PL −2.7, ECRL −21.2, ECRB −13.3, ECU +25.1 mm."),
  B("Inverse dynamics: 0.71–0.74 N·m flexion moment for a 10 N dorsal force at the third MCP, 0.2 N·m deviation moment from hand weight, −0.99 N·m for a 10 N downward force; all checked to 0.0002 N·m by virtual work."),
  B("Static Optimization (six runs): activations ≤ 0.13, reserves zero, balance error < 4×10⁻⁵ N·m."),
  B("Forward dynamics: peak excursions 38.1° flexion, −25.2° extension, −8.2° radial, 22.4° ulnar for a +0.10 excitation pulse from a posture-holding baseline; forward-to-inverse consistency 0.003 N·m RMS (0.03 N·m radial)."),
  B("Joint reactions (Newton–Euler): 38–66 N unloaded, up to 128 N (20 N load) in the prescribed-motion cases and up to 192 N in the forward-dynamics cases."),
  B("Six-muscle maximum moments: 10.2 / 7.3 / 9.5 / 12.2 N·m versus 12.2 / 7.1 / 9.5 / 11.0 N·m (Delp et al., 1996)."), 
  H1("17. Discussion"),
  P("**How flexion–extension is generated.** In the model, wrist flexion is produced by the volar muscles (FCR, FCU, PL; positive flexion-axis moment arms 11–24 mm) and extension by ECRL, ECRB and ECU (negative arms). Because the rotation is shared equally by the radiocarpal and midcarpal joints, a given tendon excursion drives both. **Radial versus ulnar deviation.** Ulnar deviation is generated by ECU and FCU (arms 22–25 mm), radial deviation by ECRL, ECRB and FCR. The ulnar deviators (FCU, ECU) lose leverage as the wrist deviates ulnarly (FCU 21.8 → 10.9 mm), and the radial deviators ECRL and ECRB are weakest in ulnar deviation but gain leverage radially (ECRL −27.3 mm at −10°); the midcarpal rotation on the radial side is 1.5 times the commanded deviation in the model."),
  P("**Role of external loading and co-contraction.** External loading raised muscle demand roughly in proportion to the load moment (flexor force 8 → 61 N from 0 to 20 N) and increased joint compression (reaction 48 → 117 N). Co-contraction appears even without load because passive tension of stretched extrinsic muscles must be balanced; this is a property of the model with fingers locked in extension, which is an assumption of this study. The finding that finger extrinsic muscles raise the maximum isometric moment by 60–160 % when fully activated (Section 14.1) shows how strongly the finger and wrist systems are coupled."),
  P("**What the model represents and does not.** The model represents the wrist as two coupled rotations with literature-based muscle paths and Hill-type muscles. It does not represent individual carpal motion, ligament anatomy, cartilage contact, forearm rotation, wrist–elbow–shoulder coupling, or subject-specific strength. The joint-reaction results are net loads on idealised joints. The passive limit elements are numerically stiff end-stops."),
  H1("18. Clinical relevance"),
  P("The workflow shows how a musculoskeletal model can be used to explore rehabilitation and surgical questions in principle: moment arms indicate which muscles contribute to which direction (relevant to understanding weakness patterns and tendon-transfer planning; Loren et al., 1996), net moment and muscle-demand estimates indicate how external load changes muscle effort (relevant to exercise load and orthotic design), and reaction estimates give a first indication of joint loading. Applications to wrist rehabilitation, muscle weakness, functional assessment, surgical planning and device development would require subject-specific anatomy, validated strength and moment arms, and experimental motion and force data. **No patient-specific or clinical claim is made from this generic model.**"),
  H1("19. Limitations"),
  B("All inputs are synthetic; no experimental motion, force, EMG, imaging or in-vivo loading data were used; predicted activations cannot be compared with EMG."),
  B("**Not completed or not possible here:** OpenSim 4.3 execution (only 4.4.1 and 4.6 were available; the 4.3-format file loads in 4.4.1 with identical results); OpenSim GUI screenshots and mesh-based renderings (Geometry folder not available to the processing environment); moment-arm comparison with cadaveric data; dynamic analyses for combined movements (Experiment 3 is kinematic only); a valid OpenSim JointReaction result (see Section 13.1)."),
  B("Static Optimization neglects activation dynamics; forward dynamics excitations are hypothetical and the baseline was tuned numerically to obtain equilibrium."),
  B("Reaction moments neglect rotational inertia; the radial forward-dynamics case is dominated by end-stop contact."),
  B("Wrist limit-force properties are stiff end-stops with limit onsets that differ from functional ranges; the file's stated units for these limits are inconsistent with the numerically observed behaviour."),
  B("Reserve actuators were not used, so no conclusion about reserve sizing can be drawn."),
  B("Some bibliographic entries (†) were not re-verified."),
  H1("20. Conclusion"),
  P("The ARMS wrist–hand model supports a coherent, reproducible set of wrist analyses when its coupled-coordinate implementation, sign conventions and passive elements are respected. Moment arms, inverse dynamics, Static Optimization and forward dynamics were mutually consistent to 10⁻⁴ to 10⁻² N·m in the cases tested, and six-muscle maximum moments matched published values within one standard deviation. Two problems were identified and handled explicitly: muscle passive force leaking into the default inverse-dynamics result, and unreliable OpenSim JointReaction output for this model, for which an independent Newton–Euler calculation was substituted. The main uncertainties are the synthetic inputs, the stiff passive end-stops and the sensitivity of dynamics to tendon slack length and the resting equilibrium. All results are traceable to scripts and CSV files in the accompanying repository."), brk());

// ---------------- References
const refs = [
  "Anderson FC, Pandy MG. Static and dynamic optimization solutions for gait are practically equivalent. J Biomech 2001;34(2):153–161. †",
  "Crisco JJ, et al. The mechanical axes of the wrist are oriented obliquely to the anatomical axes. J Bone Joint Surg Am 2011;93(2):169–177. doi:10.2106/JBJS.I.01222. (author list †)",
  "Crowninshield RD, Brand RA. A physiologically based criterion of muscle force prediction in locomotion. J Biomech 1981;14(11):793–801. †",
  "Delp SL, Anderson FC, Arnold AS, et al. OpenSim: open-source software to create and analyze dynamic simulations of movement. IEEE Trans Biomed Eng 2007;54(11):1940–1950.",
  "Delp SL, Grierson AE, Buchanan TS. Maximum isometric moments generated by the wrist muscles in flexion–extension and radial–ulnar deviation. J Biomech 1996;29(10):1371–1375.",
  "Gonzalez RV, Buchanan TS, Delp SL. How muscle architecture and moment arms affect wrist flexion–extension moments. J Biomech 1997;30(7):705–712. doi:10.1016/S0021-9290(97)00015-8.",
  "Holzbaur KRS, Murray WM, Delp SL. A model of the upper extremity for simulating musculoskeletal surgery and analyzing neuromuscular control. Ann Biomed Eng 2005. doi:10.1007/s10439-005-3320-7. (volume/pages †)",
  "Lieber RL, Fazeli BM, Botte MJ. Architecture of selected wrist flexor and extensor muscles. J Hand Surg Am 1990;15(2):244–250.",
  "Loren GJ, Shoemaker SD, Burkholder TJ, Jacobson MD, Fridén J, Lieber RL. Human wrist motors: biomechanical design and application to tendon transfers. J Biomech 1996;29(3):331–342.",
  "McFarland DC, Binder-Markey BI, Nichols JA, Wohlman SJ, de Bruin M, Murray WM. A musculoskeletal model of the hand and wrist capable of simulating functional tasks. IEEE Trans Biomed Eng 2023;70(5). Preprint: bioRxiv 2021.12.28.474357, doi:10.1101/2021.12.28.474357.",
  "Millard M, Uchida T, Seth A, Delp SL. Flexing computational muscle: modeling and simulation of musculotendon dynamics. J Biomech Eng 2013;135(2):021005. †",
  "Mirakhorlo M, Van Beek N, Wesseling M, Maas H, Veeger HEJ. A musculoskeletal model of the hand and wrist: model definition and evaluation. Comput Methods Biomech Biomed Engin 2018;21(9):548–557. doi:10.1080/10255842.2018.1490952.",
  "Nichols JA, Bednar MS, Murray WM. Cadaveric wrist moment-arm data (Clin Biomech 2016; PLoS One 2016), SimTK project 'wristsalvage'. Cited as referenced by the University of Florida lab resources page; not retrieved or used. †",
  "Ramsay JW, Hunter BV, Gonzalez RV. Muscle moment arm and normalized moment contributions as reference data for musculoskeletal elbow and wrist joint models. J Biomech 2009;42(4):463–473.",
  "Ryu J, Cooney WP, Askew LJ, An KN, Chao EYS. Functional ranges of motion of the wrist joint. J Hand Surg Am 1991;16(3):409–419. doi:10.1016/0363-5023(91)90006-W.",
  "Seth A, Hicks JL, Uchida TK, et al. OpenSim: simulating musculoskeletal dynamics and neuromuscular control to study human and animal movement. PLoS Comput Biol 2018;14(7):e1006223. †",
];
add(H1("21. References"), ...refs.map(r => new Paragraph({ spacing: { after: 80, line: 264 }, indent: { left: 360, hanging: 360 }, children: runs(r, { size: 20 }) })), brk());

// ---------------- Appendices
add(H1("22. Appendices"),
  H2("Appendix A. Software, versions and licence"),
  B("OpenSim 4.6 (Python API, analyses); OpenSim 4.4.1 (compatibility cross-check); OpenSim 4.3 not run. Python 3.12, NumPy, pandas, Matplotlib, SciPy, Node.js `docx` for this report."),
  B("**Model licence:** the ARMS hand and wrist model header states that it is open-sourced solely for non-commercial purposes under the BSD 3-Clause licence and requires citation of McFarland et al. in any work using it. Redistribution of the source with modification is permitted provided the copyright notice, conditions and disclaimer are retained; the working model retains the header. The accompanying repository therefore includes the original and the working `.osim` with the notice, for non-commercial use; mesh geometry was not available and is not included."),
  H2("Appendix B. Reproducibility"),
  P("Run the scripts in `scripts/` in numerical order (see README.md); each reads `original_model/` and writes to `working_model/`, `opensim_files/` and `results/`. `results/csv` and `results/tables` hold every number used in this report."),
  H2("Appendix C. Failed or limited analyses"),
  B("OpenSim JointReaction: corrupted frames and a ≈10 N discrepancy at later times (Section 13.1); not used."),
  B("Forward dynamics without tuned baseline: neutral not an equilibrium (drift to 17° flexion within 1 s); superseded by the tuned baseline."),
  B("AnalyzeTool with `solve_for_equilibrium_for_auxiliary_states = false`: failed (states storage required); used equilibrium solve."),
  B("StatesTrajectory rebuilt from a states table failed to realise (fibre-velocity Newton iteration); live integrator states were sampled instead."),
  B("Zero-muscle-force JointReaction control: non-meaningful because the model is not in equilibrium; retained for transparency."),
  H2("Appendix D. Constraint definitions"),
  ...table([["Constraint","Independent","Dependent","Function (x → y, rad)"],["wrist_hand_r1_con","deviation","wrist_hand_r1","−0.1745, 0, 0.4363 → −0.2618, 0, 0.4363 (spline)"],["wrist_hand_r3_con","flexion","wrist_hand_r3","−1.2217, 1.2217 → −0.6109, 0.6109 (linear, slope 0.5)"],["CMC5_r1_con","4cmc_flexion","CMC5_r1","0, 0.2032 → 0, 0.5528 (linear)"]], "Coupler constraints (results/csv/constraints.csv).", [2000, 1800, 1800, 3426]),
  H2("Appendix E. Deliverable index"),
  P("Figures: results/figures (30 PNG). Tables and data: results/tables, results/csv. OpenSim input and output files: opensim_files (motion `.mot`, external-load XML, Static Optimization `.sto`, ID outputs). Scripts: scripts/."));

const doc = new Document({
  creator: "bb", title: "Computational Biomechanical Analysis of the Wrist (ARMS model, OpenSim)",
  styles: { default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 32, bold: true, color: "1F3864" }, paragraph: { spacing: { before: 280, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 26, bold: true, color: "2F5496" }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { margin: { top: 1440, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "ARMS wrist model — OpenSim biomechanics report — page ", font: FONT, size: 16 }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16 })] })] }) },
    children: kids }],
});
Packer.toBuffer(doc).then(b => { const out = path.join(ROOT, "08_Report"); fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(path.join(out, "Final_Report.docx"), b); console.log("docx written", b.length, "bytes; figures:", figN, "tables:", tabN); });
