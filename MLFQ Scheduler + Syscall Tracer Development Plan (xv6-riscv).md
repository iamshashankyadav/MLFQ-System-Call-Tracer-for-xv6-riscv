# MLFQ Scheduler + Syscall Tracer: Development Plan (xv6-riscv)

CSL301 Operating Systems project. Combines a multilevel feedback queue scheduler with a system call tracer, so the tracer provides the data to evaluate the scheduler.

## Phase 0: Setup (Day 1)

- [ ] Clone xv6-riscv, run `make qemu`, confirm the `$` prompt appears
- [ ] `git init` your own repo and commit the clean baseline
- [ ] Read the xv6 book chapters on Scheduling (ch. 7) and System calls (ch. 4)

## Phase 1: Syscall Tracer (do this first, it is simpler)

Adding a syscall teaches you the plumbing you will reuse for the scheduler.

- [ ] **1.1 Add `trace(mask)` syscall**
  - `kernel/syscall.h`: add `#define SYS_trace 22`
  - `kernel/syscall.c`: add the `extern` declaration and a table entry
  - `kernel/sysproc.c`: write `sys_trace()` that stores the mask in `myproc()`
  - `user/usys.pl` and `user/user.h`: add the stub and prototype
- [ ] **1.2 Extend `struct proc`** (`kernel/proc.h`): add `int tracemask;` and `int syscount[32];`
- [ ] **1.3 Hook into `syscall()`** (`kernel/syscall.c`): increment `syscount[num]`, and if the mask bit is set, print `pid: syscall name -> return value`
- [ ] **1.4 Inherit in `fork()`** (`kernel/proc.c`): copy `tracemask` to the child
- [ ] **1.5 Write `user/strace.c`**: usage `strace <mask> <cmd>`; add it to `UPROGS` in the Makefile
- [ ] **Test:** `strace 32 cat README` should log `read` calls. Commit.

## Phase 2: `getpinfo()` Syscall

- [ ] Create `kernel/pstat.h` with `struct pstat { int pid[NPROC]; int inuse[NPROC]; int queue[NPROC]; int ticks[NPROC]; int syscalls[NPROC]; }`
- [ ] Add `getpinfo(struct pstat*)` using the same 4 steps as 1.1, and use `copyout()` to return the data
- [ ] Write `user/ps.c` to print the table
- [ ] **Test:** `ps` lists running processes. Commit.

## Phase 3: MLFQ Scheduler

- [ ] **3.1 Add fields to `struct proc`:** `int queue;` (0-2), `int ticks_used;`, `int wait_ticks;`
- [ ] **3.2 Initialize** them in `allocproc()`: new processes start at queue 0 (highest priority)
- [ ] **3.3 Define the policy** (put these as constants in `param.h`):

| Queue | Priority | Time slice |
| --- | --- | --- |
| 0 | Highest | 2 ticks |
| 1 | Medium | 4 ticks |
| 2 | Lowest | 8 ticks (round-robin) |

- [ ] **3.4 Rewrite `scheduler()`** (`kernel/proc.c`): scan for the highest-priority RUNNABLE process, run it, round-robin within a queue
- [ ] **3.5 Track ticks:** in `kernel/trap.c` (timer interrupt), increment `ticks_used`. When the slice is used up, demote the process one queue level and `yield()`
- [ ] **3.6 I/O-friendly rule:** if a process gives up the CPU (sleeps) before its slice ends, keep it at the same level
- [ ] **3.7 Aging / priority boost:** every N ticks (e.g. 100), move all processes back to queue 0 to prevent starvation
- [ ] **Test with `CPUS=1`** first (`make qemu CPUS=1`). Commit.

## Phase 4: Test Programs (`user/`)

- [ ] `cpubound.c`: long loop, no sleep
- [ ] `iobound.c`: loop with frequent `sleep()` or `read`/`write`
- [ ] `mixed.c`: forks several of each and runs them together
- [ ] Use `ps` (from `getpinfo`) to show queue levels over time

## Phase 5: Evaluation (use the tracer to collect data)

- [ ] Compare round-robin (original) vs MLFQ: turnaround time, response time for I/O-bound jobs
- [ ] Use `syscount` to show I/O-bound processes make more syscalls and stay in higher queues
- [ ] Vary parameters (time slices, boost interval) and record results
- [ ] Make charts (queue level vs time, ticks per process)

## Phase 6: Wrap-up

- [ ] Write the report: design, changed files, challenges, results
- [ ] Prepare a demo script (3 to 5 minutes): `strace` demo, then `ps` + mixed workload
- [ ] Final commit and tag (`git tag v1.0`)

## Files You Will Touch

| File | Purpose |
| --- | --- |
| `kernel/proc.h`, `proc.c` | PCB fields, `fork`, `scheduler` |
| `kernel/syscall.h`, `syscall.c`, `sysproc.c` | new syscalls and tracing hook |
| `kernel/trap.c` | timer tick accounting and demotion |
| `kernel/pstat.h` | process info struct |
| `user/usys.pl`, `user.h` | user-side stubs |
| `user/strace.c`, `ps.c`, test programs | tools and benchmarks |
| `Makefile` | register new user programs |

## Tips

- Commit after every checkbox. A broken scheduler just hangs the boot, and Git is your undo button.
- Use `printf` in the kernel for debugging, and `make clean` if things act strangely.
- Get Phase 3 working with one CPU before testing with multiple CPUs.
