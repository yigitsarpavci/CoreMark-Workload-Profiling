import os
import subprocess
import re
import json
import time
import statistics

CONFIGS = [
    {"name": "Default (no XCFLAGS)", "xcflags": None},
    {"name": "-O0", "xcflags": "-O0"},
    {"name": "-O1", "xcflags": "-O1"},
    {"name": "-O2", "xcflags": "-O2"},
    {"name": "-O3", "xcflags": "-O3"},
    {"name": "-Ofast", "xcflags": "-Ofast"},
    {"name": "-march=native", "xcflags": "-march=native"},
    {"name": "-O3 -march=native", "xcflags": "-O3 -march=native"},
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
COREMARK_DIR = os.environ.get("COREMARK_DIR", os.path.join(REPO_ROOT, "coremark"))
RUNS_PER_CONFIG = 5

def parse_output(output):
    iter_sec = None
    total_time = None
    total_iters = None
    for line in output.splitlines():
        if "Iterations/Sec" in line:
            m = re.search(r"Iterations/Sec\s*:\s*([\d\.]+)", line)
            if m:
                iter_sec = float(m.group(1))
        elif "Total time (secs)" in line:
            m = re.search(r"Total time \(secs\)\s*:\s*([\d\.]+)", line)
            if m:
                total_time = float(m.group(1))
        elif "Iterations" in line and "Iterations/Sec" not in line:
            m = re.search(r"Iterations\s*:\s*(\d+)", line)
            if m:
                total_iters = int(m.group(1))
    return iter_sec, total_time, total_iters

def run_benchmarks():
    results = {}
    print("Starting CoreMark Benchmark Suite...")
    
    for cfg in CONFIGS:
        cfg_name = cfg["name"]
        xcflags = cfg["xcflags"]
        print(f"\n==========================================")
        print(f"Testing configuration: {cfg_name}")
        print(f"XCFLAGS: {xcflags}")
        print(f"==========================================")
        
        # 1. Clean
        subprocess.run(["make", "clean"], cwd=COREMARK_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # 2. Build and run 1st time via make
        make_cmd = ["make"]
        if xcflags:
            make_cmd.append(f"XCFLAGS={xcflags}")
        
        print(f"Running Run 1 (build & initial run via make)...")
        res1 = subprocess.run(make_cmd, cwd=COREMARK_DIR, capture_output=True, text=True)
        if res1.returncode != 0:
            print(f"Error building {cfg_name}: {res1.stderr}")
            continue
            
        # Read run1.log
        with open(f"{COREMARK_DIR}/run1.log", "r") as f:
            run1_log = f.read()
        
        val, t_sec, iters = parse_output(run1_log)
        print(f"  Run 1: {val:.2f} iter/s (time: {t_sec}s, iters: {iters})")
        
        run_values = [val]
        run_times = [t_sec]
        run_iters = [iters]
        
        # Runs 2 to 5 directly with coremark.exe
        for r in range(2, RUNS_PER_CONFIG + 1):
            print(f"Running Run {r}...")
            res = subprocess.run(["./coremark.exe", "0x0", "0x0", "0x66", "0", "7", "1", "2000"],
                                 cwd=COREMARK_DIR, capture_output=True, text=True)
            v, t, it = parse_output(res.stdout)
            print(f"  Run {r}: {v:.2f} iter/s (time: {t}s, iters: {it})")
            run_values.append(v)
            run_times.append(t)
            run_iters.append(it)
            time.sleep(0.5)
            
        mean_val = statistics.mean(run_values)
        stdev_val = statistics.stdev(run_values) if len(run_values) > 1 else 0.0
        
        print(f"-> Summary for {cfg_name}: Mean = {mean_val:.2f} iter/s, StDev = {stdev_val:.2f}")
        
        results[cfg_name] = {
            "xcflags": xcflags,
            "runs": run_values,
            "times": run_times,
            "iterations": run_iters,
            "mean": mean_val,
            "stdev": stdev_val,
            "min": min(run_values),
            "max": max(run_values)
        }
        
        out_dir = os.path.join(REPO_ROOT, "results")
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, "benchmark_results.json")
        with open(out_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nBenchmark suite complete! Results saved to {out_file}")

if __name__ == "__main__":
    run_benchmarks()
