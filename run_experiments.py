"""Run a BehaviorSpace experiment of decoy_saturation.nlogox headlessly.

Usage:
    python run_experiments.py                                      # main sweep -> sweep_results.csv
    python run_experiments.py regime-timeseries timeseries.csv     # per-tick runs for the time series
    python run_experiments.py <experiment> <out.csv> --setup-file <experiments.xml>
"""
import argparse
import os
import subprocess
import time

JAVA_EXE = r"C:\Program Files\NetLogo 7.0.4\runtime\bin\java.exe"
NETLOGO_JAR = r"C:\Program Files\NetLogo 7.0.4\app\netlogo-7.0.4.jar"
MODEL_FILE = "decoy_saturation.nlogox"
THREADS = 12

def run(experiment, output_csv, setup_file=None):
    print(f"Running experiment '{experiment}' -> {output_csv} ({THREADS} threads)")
    start = time.time()
    cmd = [
        JAVA_EXE, "-XX:MaxRAMPercentage=50", "-Dfile.encoding=UTF-8",
        # without these NetLogo reports compile errors as a misleading SecurityException
        "-Duser.language=en", "-Duser.country=US",
        "-classpath", NETLOGO_JAR, "org.nlogo.headless.Main",
        "--model", MODEL_FILE,
        "--experiment", experiment,
        "--table", output_csv,
        "--threads", str(THREADS),
    ]
    if setup_file:
        cmd += ["--setup-file", setup_file]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Failed with code {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
        return proc.returncode
    size_kb = os.path.getsize(output_csv) / 1024
    print(f"Done in {time.time() - start:.0f} s, {output_csv} is {size_kb:.0f} KB")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("experiment", nargs="?", default="decoy-saturation-sweep")
    parser.add_argument("output_csv", nargs="?", default="sweep_results.csv")
    parser.add_argument("--setup-file")
    args = parser.parse_args()
    raise SystemExit(run(args.experiment, args.output_csv, args.setup_file))
