rm evaluation/*.csv
brench brench_ic.toml > evaluation/ic.csv
brench brench_ps.toml > evaluation/ps.csv
cd evaluation
python3 plot.py ic
python3 plot.py ps
