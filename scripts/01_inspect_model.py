"""Phase II: read-only inspection of the ARMS model. Writes CSV tables to results/csv."""
from common import *
import pandas as pd, numpy as np, re
m, s = load()
print("OpenSim", osim.GetVersionAndDate())
# Bodies
rows=[]
for b in m.getBodySet():
    I=b.getInertia(); mo=I.getMoments(); pr=I.getProducts(); c=b.getMassCenter()
    rows.append(dict(body=b.getName(),mass_kg=b.getMass(),com_x=c.get(0),com_y=c.get(1),com_z=c.get(2),
        Ixx=mo.get(0),Iyy=mo.get(1),Izz=mo.get(2),Ixy=pr.get(0),Ixz=pr.get(1),Iyz=pr.get(2),
        n_geometry=b.getPropertyByName("attached_geometry").size()))
pd.DataFrame(rows).to_csv(f"{CSV}/bodies.csv",index=False)
# Joints
rows=[]
for j in m.getJointSet():
    rows.append(dict(joint=j.getName(),type=j.getConcreteClassName(),parent=j.getParentFrame().getName(),
        parent_body=j.getParentFrame().findBaseFrame().getName(),child=j.getChildFrame().getName(),
        child_body=j.getChildFrame().findBaseFrame().getName(),
        coordinates=";".join(j.get_coordinates(i).getName() for i in range(j.numCoordinates()))))
pd.DataFrame(rows).to_csv(f"{CSV}/joints.csv",index=False)
# Coordinates
rows=[]
cons_dep={c.getName() for c in m.getCoordinateSet() if c.isConstrained(s)}
for c in m.getCoordinateSet():
    mt=str(c.getMotionType())
    rows.append(dict(coord=c.getName(),joint=c.getJoint().getName(),
        motion={'1':'rotational','2':'translational','3':'coupled'}.get(mt,mt),
        units_internal='rad' if c.getJoint().getName() else '',
        default=c.getDefaultValue(),default_deg=np.degrees(c.getDefaultValue()),
        range_min_rad=c.getRangeMin(),range_max_rad=c.getRangeMax(),
        range_min_deg=np.degrees(c.getRangeMin()),range_max_deg=np.degrees(c.getRangeMax()),
        clamped=c.getDefaultClamped(),locked_default=c.getDefaultLocked(),
        prescribed=c.isPrescribed(s),dependent_via_constraint=c.isConstrained(s)))
pd.DataFrame(rows).to_csv(f"{CSV}/coordinates.csv",index=False)
# Constraints (parse from XML for functions)
txt=open(ORIG,encoding="utf8").read()
rows=[]
for cn in m.getConstraintSet():
    i=txt.find(f'<CoordinateCouplerConstraint name="{cn.getName()}"'); j=txt.find('</CoordinateCouplerConstraint>',i)
    seg=txt[i:j]
    xs=re.search(r'<x>([^<]*)</x>',seg).group(1).split(); ys=re.search(r'<y>([^<]*)</y>',seg).group(1).split()
    ind=re.search(r'<independent_coordinate_names>([^<]*)<',seg).group(1)
    dep=re.search(r'<dependent_coordinate_name>([^<]*)<',seg).group(1)
    rows.append(dict(constraint=cn.getName(),type=cn.getConcreteClassName(),independent=ind,dependent=dep,
        spline_x=" ".join(xs),spline_y=" ".join(ys)))
pd.DataFrame(rows).to_csv(f"{CSV}/constraints.csv",index=False)
# Forces
rows=[]
for f in m.getForceSet(): rows.append(dict(name=f.getName(),type=f.getConcreteClassName()))
pd.DataFrame(rows).to_csv(f"{CSV}/forces.csv",index=False)
# Muscles
rows=[]
for mu in m.getMuscles():
    mm=osim.Millard2012EquilibriumMuscle.safeDownCast(mu)
    gp=mu.getGeometryPath()
    pts=gp.getPathPointSet(); bodies=[osim.PathPoint.safeDownCast(pts.get(i)).getParentFrame().findBaseFrame().getName() if osim.PathPoint.safeDownCast(pts.get(i)) else "cond/moving" for i in range(pts.getSize())]
    rows.append(dict(muscle=mu.getName(),type=mu.getConcreteClassName(),Fmax_N=mu.getMaxIsometricForce(),
        lopt_m=mu.getOptimalFiberLength(),lslack_m=mu.getTendonSlackLength(),
        pennation_deg=np.degrees(mu.get_pennation_angle_at_optimal()),vmax_lopt_per_s=mu.getMaxContractionVelocity(),
        default_activation=mm.get_default_activation(),n_path_points=pts.getSize(),n_wrap=gp.getWrapSet().getSize(),
        origin_body=bodies[0],insertion_body=bodies[-1],mtu_len_neutral_m=mu.getLength(s)))
pd.DataFrame(rows).to_csv(f"{CSV}/muscles.csv",index=False)
# Ligament-like bushings and limit forces
rows=[]
for f in m.getForceSet():
    cl=f.getConcreteClassName()
    if cl=="FunctionBasedBushingForce":
        b=osim.FunctionBasedBushingForce.safeDownCast(f)
        rows.append(dict(name=f.getName(),type=cl,frame1=b.getFrame1().findBaseFrame().getName(),frame2=b.getFrame2().findBaseFrame().getName()))
    elif cl=="CoordinateLimitForce":
        c=osim.CoordinateLimitForce.safeDownCast(f)
        rows.append(dict(name=f.getName(),type=cl,coordinate=c.get_coordinate(),upper_limit_deg=c.get_upper_limit(),lower_limit_deg=c.get_lower_limit(),
           upper_stiffness=c.get_upper_stiffness(),lower_stiffness=c.get_lower_stiffness(),damping=c.get_damping(),transition_deg=c.get_transition()))
pd.DataFrame(rows).to_csv(f"{CSV}/passive_elements.csv",index=False)
# Geometry check
geo=sorted(set(re.findall(r'<mesh_file>\s*([^<\s]+)\s*</mesh_file>',txt)))
pd.DataFrame({"mesh_file":geo,"found_in_upload":[os.path.exists(os.path.join(os.path.dirname(ORIG),g)) for g in geo]}).to_csv(f"{CSV}/geometry_check.csv",index=False)
# Validity: model init + muscle length finite at default
bad=[mu.getName() for mu in m.getMuscles() if not np.isfinite(mu.getLength(s))]
print("bodies",m.getBodySet().getSize(),"joints",m.getJointSet().getSize(),"coords",m.getCoordinateSet().getSize(),
      "forces",m.getForceSet().getSize(),"muscles",m.getMuscles().getSize(),"constraints",m.getConstraintSet().getSize())
print("non-finite muscle lengths:",bad); print("mesh files referenced:",len(geo),"found:",sum(os.path.exists(os.path.join(os.path.dirname(ORIG),g)) for g in geo))
print("total model mass (kg):",sum(b.getMass() for b in m.getBodySet()), " gravity:",v3(m.getGravity()))
