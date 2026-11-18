#!/bin/bash
# Re-run every experiment from the report. Output goes to results/.
# usage: tools/run_experiments.sh        (from the project folder)
set -e
cd "$(dirname "$0")/.."
X=xv6-riscv
(cd $X && rm -f fs.img && make -s kernel/kernel fs.img)
R="python3 -s tools/xv6run.py $X"

# smoke test + tracer demo
$R 1 results/smoke.txt "strace 32 cat README" "ps" "cpubound 20" "iobound 20"
$R 1 results/demo_tracer.txt "strace 32 cat README" "strace 2147483646 echo hello" \
  "strace 33554434 schedtest -c 1 -i 1 -w 2 -n 3" "cpubound 400 &" "iobound 300 &" \
  "ps" "ps" "cpubound 5" "ps" "cpubound 5" "ps"

# Exp 1: round-robin vs MLFQ (3 repetitions each)
W="-c 3 -i 3 -w 40 -n 60"
$R 1 results/exp1_rr_vs_mlfq.txt "schedtest -p rr $W" "schedtest -p mlfq $W" \
  "schedtest -p rr $W" "schedtest -p mlfq $W" "schedtest -p rr $W" "schedtest -p mlfq $W"

# Exp 2: queue level over time
$R 1 results/exp2_timeline.txt "schedtest -p mlfq -c 3 -i 2 -w 40 -n 60 -m"

# Exp 3: time-slice sweep (2 repetitions)
C=()
for rep in 1 2; do for s in 1,2,4 2,4,8 4,8,16 8,16,32 16,32,64; do
  C+=("schedtest -p mlfq $W -s $s"); done; done
$R 1 results/exp3_slices.txt "${C[@]}"

# Exp 4: priority boost vs starvation
B="-c 1 -i 4 -w 20 -e 3000 -n 40"
$R 1 results/exp4_boost.txt "schedtest -p mlfq $B -b 0" "schedtest -p mlfq $B -b 25" \
  "schedtest -p mlfq $B -b 50" "schedtest -p mlfq $B -b 100" "schedtest -p mlfq $B -b 200" \
  "schedtest -p rr $B"

# Exp 5: 3 CPUs
$R 3 results/exp5_multicpu.txt "schedtest -p rr $W" "schedtest -p mlfq $W" \
  "schedtest -p rr -c 6 -i 3 -w 40 -n 60" "schedtest -p mlfq -c 6 -i 3 -w 40 -n 60"
echo "all experiments done"
