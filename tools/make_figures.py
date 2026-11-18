#!/usr/bin/env python3
"""Parse the xv6 experiment logs in results/ and draw the report figures."""
import os, re, sys, statistics as stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "report", "figures")
os.makedirs(OUT, exist_ok=True)

# reference palette (light mode)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SEQ = ["#9ec5f0", "#4f93e0", "#1d5aa8"]          # Q0 -> Q2, one hue light->dark
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"
POL = {"rr": ORANGE, "mlfq": BLUE}
KIND = {"cpu": BLUE, "io": ORANGE}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "legend.frameon": False, "savefig.dpi": 170,
})

RES_FIELDS = ["kind", "pid", "ctime", "first_run", "etime", "rtime", "wtime",
              "stime", "queue", "q0", "q1", "q2", "nsys", "ndemote", "nsched",
              "tat", "resp", "cpu_us", "wait_us", "maxwait_us"]


def parse(fname):
    """Return list of runs: {cfg:{...}, res:[...], mon:[...]}"""
    runs = []
    for line in open(os.path.join(RES, fname), errors="replace"):
        line = line.strip()
        m = re.search(r"(CFG|RES|MON),[^\s]*", line)
        if not m:
            continue
        parts = m.group(0).split(",")
        tag = parts[0]
        if tag == "CFG":
            pol, boost, s0, s1, s2 = parts[1:6]
            runs.append({"cfg": {"policy": pol, "boost": int(boost),
                                 "slice": (int(s0), int(s1), int(s2))},
                         "res": [], "mon": []})
        elif tag == "RES" and len(parts) == len(RES_FIELDS) + 1:
            d = dict(zip(RES_FIELDS, parts[1:]))
            for k in RES_FIELDS[1:]:
                d[k] = int(d[k])
            runs[-1]["res"].append(d)
        elif tag == "MON" and len(parts) == 7:
            t, pid, kind, q, st, tk = parts[1:]
            runs[-1]["mon"].append((int(t), int(pid), kind, int(q), int(st), int(tk)))
    return runs


def avg(runs_res, kind, key):
    v = [r[key] for r in runs_res if r["kind"] == kind]
    return sum(v) / len(v) if v else 0


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- fig 1: design
def fig_design():
    fig, ax = plt.subplots(figsize=(9.4, 4.2))
    ax.set_xlim(-1.4, 11.8); ax.set_ylim(0, 5.2); ax.axis("off"); ax.grid(False)
    rows = [("Queue 0  (highest priority)", "time slice = 2 ticks", 4.1),
            ("Queue 1  (medium)", "time slice = 4 ticks", 2.7),
            ("Queue 2  (lowest, RR)", "time slice = 8 ticks", 1.3)]
    for i, (lab, sl, y) in enumerate(rows):
        ax.add_patch(FancyBboxPatch((1.2, y - 0.38), 6.0, 0.76,
                     boxstyle="round,pad=0.02,rounding_size=0.12",
                     fc=SEQ[i], ec="white", lw=2))
        ax.text(1.4, y + 0.08, lab, color="white" if i else INK, fontsize=10.5,
                weight="bold", va="center")
        ax.text(1.4, y - 0.2, sl, color="white" if i else INK, fontsize=9, va="center")
        # process tokens
        for j in range(3 - i):
            ax.add_patch(FancyBboxPatch((5.95 + j * 0.42, y - 0.17), 0.32, 0.34,
                         boxstyle="round,pad=0.01,rounding_size=0.06",
                         fc="white", ec=INK2, lw=0.8))
            ax.text(6.11 + j * 0.42, y, "P", fontsize=8, ha="center", va="center", color=INK2)
    # demotion arrows
    for y0, y1 in [(4.1, 2.7), (2.7, 1.3)]:
        ax.add_patch(FancyArrowPatch((7.35, y0 - 0.1), (7.35, y1 + 0.1),
                     arrowstyle="-|>", mutation_scale=14, color=ORANGE, lw=1.8,
                     connectionstyle="arc3,rad=-0.45"))
    ax.text(7.85, 3.4, "uses whole slice\n→ demote one level", fontsize=9, color=INK2, va="center")
    ax.text(7.85, 2.0, "uses whole slice\n→ demote one level", fontsize=9, color=INK2, va="center")
    # boost arrow
    ax.add_patch(FancyArrowPatch((0.95, 1.3), (0.95, 4.1), arrowstyle="-|>",
                 mutation_scale=14, color=AQUA, lw=1.8, connectionstyle="arc3,rad=-0.5"))
    ax.text(-1.35, 2.7, "priority\nboost\nevery\n100 ticks", fontsize=8.5,
            color=INK2, va="center", ha="left")
    # sleep loop
    ax.text(7.85, 4.55, "blocks (I/O, sleep) before slice ends\n→ stays at same level",
            fontsize=9, color=INK2, va="center")
    ax.text(1.2, 0.35, "New process → Queue 0.   scheduler() always runs the highest non-empty "
            "queue;\nround-robin inside a queue; a newly-runnable higher-priority job preempts.",
            fontsize=9, color=INK2)
    ax.set_title("Figure 1 – MLFQ policy implemented in xv6", pad=4)
    save(fig, "fig1_mlfq_design.png")


# -------------------------------------------------------------- fig 2: timeline
def fig_timeline():
    runs = parse("exp2_timeline.txt")
    run = [r for r in runs if r["cfg"]["policy"] == "mlfq"][0]
    mon = run["mon"]
    t0 = min(m[0] for m in mon)
    pids = sorted({m[1] for m in mon})
    kinds = {m[1]: m[2] for m in mon}
    order = sorted(pids, key=lambda p: (kinds[p] != "io", p))
    fig, axes = plt.subplots(len(order), 1, figsize=(8.6, 1.05 * len(order) + 0.8),
                             sharex=True)
    cpu_i = io_i = 0
    for ax, pid in zip(axes, order):
        pts = [(m[0] - t0, m[3]) for m in mon if m[1] == pid]
        xs, ys = zip(*pts)
        c = KIND[kinds[pid]]
        ax.step(xs, ys, where="post", color=c, lw=2)
        ax.set_ylim(2.4, -0.4); ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["Q0", "Q1", "Q2"])
        ax.tick_params(axis="y", labelsize=8)
        if kinds[pid] == "cpu":
            cpu_i += 1; lab = f"CPU-bound job {cpu_i} (pid {pid}, {cpu_i}× work)"
        else:
            io_i += 1; lab = f"I/O-bound job {io_i} (pid {pid})"
        ax.text(0.33, 0.66, lab, transform=ax.transAxes, ha="left", va="center",
                fontsize=8.5, color=INK2, bbox=dict(fc="white", ec="none", alpha=0.85))
        ax.grid(axis="y", visible=False)
    # boost markers (every 100 ticks since schedctl reset)
    cfg0 = min(r["ctime"] for r in run["res"])
    for ax in axes:
        b = 100 - (t0 - cfg0) % 100
        while b < max(m[0] for m in mon) - t0:
            ax.axvline(b, color=AQUA, lw=1, ls="--")
            b += 100
    axes[-1].set_xlabel("time since start (ticks, 1 tick = 10 ms)")
    axes[0].set_title("Figure 5 – Queue level over time under MLFQ (sampled every tick "
                      "with getpinfo; dashed = priority boost)", pad=8, fontsize=10.5)
    fig.tight_layout(h_pad=0.4)
    save(fig, "fig5_queue_timeline.png")


def bars(ax, groups, series, values, colors, fmt="{:.0f}", errs=None):
    n = len(series); w = 0.8 / n
    for i, s in enumerate(series):
        xs = [g + (i - (n - 1) / 2) * w for g in range(len(groups))]
        ax.bar(xs, values[i], width=w * 0.92, color=colors[i], label=s,
               edgecolor="white", linewidth=1)
        tops = values[i]
        if errs:
            lo, hi = errs[i]
            ax.vlines(xs, lo, hi, color=INK2, lw=1)
            tops = [max(a, b) for a, b in zip(values[i], hi)]
        for x, v, t in zip(xs, values[i], tops):
            ax.annotate(fmt.format(v), (x, t), xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(groups))); ax.set_xticklabels(groups)
    ax.grid(axis="x", visible=False)
    ax.margins(y=0.15)


# ----------------------------------------------------------- fig 3: RR vs MLFQ
def exp1_summary():
    runs = parse("exp1_rr_vs_mlfq.txt")
    out = {}
    for pol in ("rr", "mlfq"):
        rs = [r for r in runs if r["cfg"]["policy"] == pol]
        out[pol] = {}
        for kind in ("cpu", "io"):
            def per_run(f):
                return [f([x for x in r["res"] if x["kind"] == kind]) for r in rs]
            out[pol][kind] = {
                "tat": per_run(lambda xs: stats.mean(x["tat"] for x in xs)),
                "wait_ms": per_run(lambda xs: stats.mean(x["wait_us"] for x in xs) / 1000),
                "lat_ms": per_run(lambda xs: stats.mean(x["wait_us"] / max(x["nsched"], 1)
                                                         for x in xs) / 1000),
                "max_ms": per_run(lambda xs: max(x["maxwait_us"] for x in xs) / 1000),
                "resp": per_run(lambda xs: stats.mean(x["resp"] for x in xs)),
                "nsys": per_run(lambda xs: stats.mean(x["nsys"] for x in xs)),
            }
    return runs, out


def fig_rr_vs_mlfq():
    runs, s = exp1_summary()
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6))
    metrics = [("tat", "Avg turnaround (ticks)", "{:.0f}"),
               ("wait_ms", "Avg total ready-queue wait (ms)", "{:.0f}"),
               ("lat_ms", "Avg wait per dispatch (ms)", "{:.1f}")]
    for ax, (k, title, fmt) in zip(axes, metrics):
        vals, errs = [], []
        for pol in ("rr", "mlfq"):
            v = [stats.mean(s[pol][kind][k]) for kind in ("cpu", "io")]
            lo = [min(s[pol][kind][k]) for kind in ("cpu", "io")]
            hi = [max(s[pol][kind][k]) for kind in ("cpu", "io")]
            vals.append(v); errs.append((lo, hi))
        bars(ax, ["CPU-bound", "I/O-bound"], ["Round-robin (stock xv6)", "MLFQ"], vals,
             [ORANGE, BLUE], fmt, errs)
        ax.set_title(title, fontsize=10)
    axes[0].legend(loc="upper left", fontsize=8.5)
    fig.suptitle("Figure 4 – Round-robin vs MLFQ, 1 CPU, 3 CPU-bound + 3 I/O-bound jobs "
                 "(mean of 3 runs, whiskers = min/max)", x=0.01, ha="left",
                 fontsize=11, weight="bold")
    fig.tight_layout()
    save(fig, "fig4_rr_vs_mlfq.png")
    return s


# ------------------------------------------- fig 4: syscalls & queue occupancy
def fig_syscalls():
    runs = parse("exp1_rr_vs_mlfq.txt")
    run = [r for r in runs if r["cfg"]["policy"] == "mlfq"][-1]
    res = sorted(run["res"], key=lambda x: (x["kind"] != "cpu", x["pid"]))
    labels, ci, ii = [], 0, 0
    for x in res:
        if x["kind"] == "cpu":
            ci += 1; labels.append(f"CPU {ci}\n(pid {x['pid']})")
        else:
            ii += 1; labels.append(f"I/O {ii}\n(pid {x['pid']})")
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.6))
    ax = axes[0]
    ax.bar(range(len(res)), [x["nsys"] for x in res],
           color=[KIND[x["kind"]] for x in res], edgecolor="white")
    for i, x in enumerate(res):
        ax.text(i, x["nsys"], str(x["nsys"]), ha="center", va="bottom", fontsize=8.5)
    ax.set_title("System calls made (tracer syscount)", fontsize=10)
    ax.set_xticks(range(len(res))); ax.set_xticklabels(labels, fontsize=7.5)
    ax.grid(axis="x", visible=False); ax.margins(y=0.15)
    ax = axes[1]
    ax.bar(range(len(res)), [x["ndemote"] for x in res],
           color=[KIND[x["kind"]] for x in res], edgecolor="white")
    for i, x in enumerate(res):
        ax.text(i, x["ndemote"], str(x["ndemote"]), ha="center", va="bottom", fontsize=8.5)
    ax.set_title("Demotions", fontsize=10)
    ax.set_xticks(range(len(res))); ax.set_xticklabels(labels, fontsize=7.5)
    ax.grid(axis="x", visible=False); ax.margins(y=0.2)
    ax = axes[2]
    bottom = [0] * len(res)
    for q in range(3):
        v = [x[f"q{q}"] for x in res]
        ax.bar(range(len(res)), v, bottom=bottom, color=SEQ[q], label=f"Q{q}",
               edgecolor="white", linewidth=1.5)
        bottom = [b + c for b, c in zip(bottom, v)]
    ax.set_title("CPU ticks charged at each queue", fontsize=10)
    ax.set_xticks(range(len(res))); ax.set_xticklabels(labels, fontsize=7.5)
    ax.grid(axis="x", visible=False); ax.legend(fontsize=8.5, loc="upper left")
    for i, x in enumerate(res):
        if x["kind"] == "io":
            ax.text(i, 0.5, f"{x['cpu_us']/1000:.0f} ms\nCPU,\nall in Q0", ha="center",
                    va="bottom", fontsize=7, color=INK2)
    fig.suptitle("Figure 6 – Tracer data: I/O-bound jobs make many syscalls and never leave Q0 "
                 "(one MLFQ run)", x=0.01, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    save(fig, "fig6_syscalls_queues.png")
    return res


# ------------------------------------------------------------ fig 5: slices
def fig_slices():
    runs = parse("exp3_slices.txt")
    cfgs = []
    for r in runs:
        if r["cfg"]["slice"] not in cfgs:
            cfgs.append(r["cfg"]["slice"])
    data = {}
    for c in cfgs:
        rs = [r for r in runs if r["cfg"]["slice"] == c]
        data[c] = {k: stats.mean(avg(r["res"], k, "tat") for r in rs) for k in ("cpu", "io")}
        data[c]["io_wait"] = stats.mean(
            stats.mean(x["wait_us"] / max(x["nsched"], 1) for x in r["res"] if x["kind"] == "io")
            for r in rs) / 1000
        data[c]["cpu_resp"] = stats.mean(avg(r["res"], "cpu", "resp") for r in rs)
    labels = ["/".join(map(str, c)) for c in cfgs]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    ax = axes[0]
    for k, lab in (("cpu", "CPU-bound"), ("io", "I/O-bound")):
        ys = [data[c][k] for c in cfgs]
        ax.plot(labels, ys, color=KIND[k], lw=2, marker="o", ms=8,
                markeredgecolor="white", markeredgewidth=2, label=lab)
        ax.text(len(cfgs) - 1 + 0.08, ys[-1], lab, color=INK2, fontsize=8.5, va="center")
    ax.set_title("Avg turnaround (ticks)", fontsize=10)
    ax.set_xlabel("time slices Q0/Q1/Q2 (ticks)")
    ax.legend(fontsize=8.5, loc="upper left")
    ax = axes[1]
    ys = [data[c]["io_wait"] for c in cfgs]
    ax.plot(labels, ys, color=ORANGE, lw=2, marker="o", ms=8, markeredgecolor="white",
            markeredgewidth=2)
    for x, y in zip(labels, ys):
        ax.text(x, y, f" {y:.1f}", fontsize=8.5, va="bottom")
    ax.set_title("I/O-bound job: avg wait per dispatch (ms)", fontsize=10)
    ax.set_xlabel("time slices Q0/Q1/Q2 (ticks)")
    ax.margins(y=0.2)
    fig.suptitle("Figure 7 – Effect of the time-slice length (MLFQ, mean of 2 runs)",
                 x=0.01, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    save(fig, "fig7_slices.png")
    return cfgs, data


# ------------------------------------------------------------- fig 6: boost
def fig_boost():
    runs = parse("exp4_boost.txt")
    ml = [r for r in runs if r["cfg"]["policy"] == "mlfq"]
    rr = [r for r in runs if r["cfg"]["policy"] == "rr"][0]
    labels = ["off" if r["cfg"]["boost"] == 0 else str(r["cfg"]["boost"]) for r in ml]
    cpu = [[x for x in r["res"] if x["kind"] == "cpu"][0] for r in ml]
    rrcpu = [x for x in rr["res"] if x["kind"] == "cpu"][0]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    for ax, key, title, scale, fmt in (
            (axes[0], "tat", "CPU-bound job turnaround (ticks)", 1, "{:.0f}"),
            (axes[1], "maxwait_us", "CPU-bound job: longest single wait (ms)", 1000, "{:.0f}")):
        ys = [c[key] / scale for c in cpu]
        ax.bar(labels, ys, color=BLUE, edgecolor="white", width=0.6)
        for x, y in zip(labels, ys):
            ax.text(x, y, fmt.format(y), ha="center", va="bottom", fontsize=8.5)
        ref = rrcpu[key] / scale
        ax.axhline(ref, color=ORANGE, lw=2, ls="--")
        ax.annotate(f"round-robin: {ref:.0f}", (len(labels) - 0.45, ref), xytext=(0, 4),
                    textcoords="offset points", color=INK2, fontsize=8.5, ha="right",
                    va="bottom", bbox=dict(fc="white", ec="none", pad=1))
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("boost interval (ticks)")
        ax.grid(axis="x", visible=False); ax.margins(y=0.15)
    fig.suptitle("Figure 8 – Starvation and the priority boost (1 CPU job vs 4 "
                 "CPU-heavy interactive jobs)", x=0.01, ha="left", fontsize=11, weight="bold")
    fig.tight_layout()
    save(fig, "fig8_boost.png")
    return ml, rr


# ---------------------------------------------------------- fig 7: multi-CPU
def fig_multicpu():
    runs = parse("exp5_multicpu.txt")
    big = [r for r in runs if len(r["res"]) == 9]
    vals = []
    for pol in ("rr", "mlfq"):
        r = [x for x in big if x["cfg"]["policy"] == pol][0]
        vals.append([avg(r["res"], "cpu", "tat"), avg(r["res"], "io", "tat")])
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    bars(ax, ["CPU-bound (6 jobs)", "I/O-bound (3 jobs)"], ["Round-robin", "MLFQ"], vals,
         [ORANGE, BLUE])
    ax.set_title("Figure 9 – 3 CPUs: average turnaround (ticks)")
    ax.legend(fontsize=8.5, loc="upper right")
    save(fig, "fig9_multicpu.png")
    return runs


# ------------------------------------------------------- terminal captures
def term_image(lines, name, title):
    lines = [l.rstrip("\r") for l in lines]
    h = 0.19 * len(lines) + 0.55
    w = max(len(l) for l in lines) * 0.083 + 0.5
    fig = plt.figure(figsize=(max(w, 6), h))
    fig.patch.set_facecolor("#1e1e1e")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.grid(False)
    ax.set_facecolor("#1e1e1e")
    ax.text(0.015, 1 - 0.12 / h, title, color="#9a9a9a", fontsize=8,
            family="DejaVu Sans", va="top", transform=ax.transAxes)
    for i, l in enumerate(lines):
        col = "#e6e6e6"
        if l.startswith("$"):
            col = "#7ee787"
        elif re.match(r"^\d+: syscall", l):
            col = "#79c0ff"
        ax.text(0.015, 1 - (0.42 + 0.19 * i) / h, l, color=col, fontsize=9,
                family="DejaVu Sans Mono", va="top", transform=ax.transAxes)
    fig.savefig(os.path.join(OUT, name), dpi=170, facecolor="#1e1e1e")
    plt.close(fig)
    print("wrote", name)


def terminals():
    txt = open(os.path.join(RES, "demo_tracer.txt"), errors="replace").read().replace("\r", "")
    sm = open(os.path.join(RES, "smoke.txt"), errors="replace").read().replace("\r", "")
    # strace 32 cat README: keep the trace lines and a little context
    seg = sm[sm.index("$ strace 32"):sm.index("$ ps")].splitlines()
    keep = []
    for l in seg:
        if l.startswith("$") or "syscall" in l:
            # split "text3: syscall" into separate visual lines
            m = re.search(r"(\d+: syscall.*)", l)
            if m and not l.startswith(m.group(1)):
                keep.append(l[:m.start()] + "…")
                keep.append(m.group(1))
            else:
                keep.append(l)
    keep.insert(1, "   (file contents omitted)")
    a = txt.index("$ strace 2147483646")
    b = txt.index("$ cpubound 400")
    seg2 = [l for l in txt[a:b].splitlines()]
    term_image(keep + [""] + seg2, "fig2_strace_demo.png",
               "xv6 console – syscall tracer (strace)")
    a = txt.index("$ cpubound 400")
    seg3 = txt[a:txt.index("QEMU: Terminated")].splitlines()
    seg3 = [l for l in seg3 if l.strip() != "$"]
    term_image(seg3, "fig3_ps_demo.png",
               "xv6 console – ps (getpinfo) while a CPU-bound and an I/O-bound job run")


if __name__ == "__main__":
    fig_design()
    fig_timeline()
    s = fig_rr_vs_mlfq()
    fig_syscalls()
    fig_slices()
    fig_boost()
    fig_multicpu()
    terminals()
