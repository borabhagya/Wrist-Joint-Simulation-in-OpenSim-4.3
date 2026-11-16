#!/bin/bash
# Full pipeline (see README.md). ~40 min on one CPU. Run from scripts/.
set -e
for s in 01_inspect_model 02_conventions_and_momentarms 03_kinematics 04_plot_kinematics 05_passive_properties 06_plot_muscles 07_make_working_model 08_id_so 09_verify_id; do python3 $s.py; done
bash run_all_so.sh; python3 11_verify_so.py
python3 12_jra.py dyn_flexext Lflex10N_dorsal; python3 13_jra_check.py; python3 14_jra_force_balance.py; python3 15_reactions.py; python3 16_jra_compare.py
python3 17_tune_fd_baseline.py; python3 18_forward_dynamics.py
for c in baseline flexion extension radial ulnar; do python3 19_fd_check.py $c; done
python3 20_fd_reactions.py baseline,flexion,extension,radial,ulnar
python3 21_sensitivity.py so; python3 21_sensitivity.py so_post; python3 21_sensitivity.py fd; python3 21_sensitivity.py num
python3 22_plots.py; python3 23_validation.py; python3 24_summary_tables.py; python3 25_report_data.py; node build_report.js
