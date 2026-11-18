# MLFQ Scheduler + Syscall Tracer (xv6-riscv) — CSL301 project

| Path | What |
| --- | --- |
| `xv6-riscv/` | modified xv6 (git repo; `git diff baseline` shows all changes) |
| `report/MLFQ_Syscall_Tracer_Report.pdf` | project report (submit this) |
| `report/MLFQ_Syscall_Tracer_Report.docx` | same report, editable |
| `report/figures/` | all figures used in the report |
| `results/` | raw xv6 console logs from every experiment |
| `tools/run_experiments.sh` | boots xv6 and re-runs every experiment |
| `tools/make_figures.py`, `tools/make_report.py` | regenerate figures / report |

Quick start:

    cd xv6-riscv && make qemu CPUS=1
    $ strace 32 cat README
    $ cpubound 400 &
    $ iobound 300 &
    $ ps
    $ schedtest -p rr -c 3 -i 3
    $ schedtest -p mlfq -c 3 -i 3

Regenerating figures/report needs matplotlib, reportlab and python-docx
(system matplotlib needs numpy<2; run python with `-s` if ~/.local has numpy 2).
