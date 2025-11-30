# src/ui.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt

from simulator_core import run_standard_with_steps, run_dynamic_with_steps
from banker import count_need

st.set_page_config(page_title="Dynamic Banker Simulator — Level 2", layout="wide")
st.title("Dynamic Banker Simulator — Level 2 (Step-by-step + Metrics)")

# helpers
def render_matrix(title, mat):
    st.subheader(title)
    st.dataframe(pd.DataFrame(mat))

def parse_arrival_input(text):
    """
    Expected format: t:4,3,3;1:2,1,1  meaning at T0 a process [4,3,3], at T1 a process [2,1,1]
    Multiple arrivals at same T allowed by comma groups: 2:[4,3,3]|[1,2,1] but we'll use ; separated entries
    Simpler accepted format: "0:4,3,3;2:2,1,1" -> returns dict {0: [[4,3,3]], 2: [[2,1,1]]}
    """
    if not text or text.strip() == "":
        return {}
    out = {}
    parts = [p.strip() for p in text.split(";") if p.strip()]
    for p in parts:
        if ":" not in p:
            continue
        t_str, vec_str = p.split(":", 1)
        try:
            t = int(t_str.strip())
        except:
            continue
        # allow multiple vectors separated by '|' or ';' - we'll only support single vec per t in this UI
        vecs = []
        for vraw in vec_str.split("|"):
            vraw = vraw.strip()
            if not vraw:
                continue
            try:
                vec = [int(x.strip()) for x in vraw.split(",") if x.strip() != ""]
                vecs.append(vec)
            except:
                continue
        if vecs:
            out[t] = vecs
    return out

# Sidebar: upload / sample
st.sidebar.header("Input")
uploaded = st.sidebar.file_uploader("Upload JSON input", type="json")
use_sample = st.sidebar.checkbox("Use sample input", value=False)

if use_sample or not uploaded:
    # sample JSON
    sample = {
      "resources": ["A", "B", "C"],
      "available": [3, 3, 2],
      "allocation": [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1]
      ],
      "max": [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2]
      ]
    }
    data = sample
else:
    data = json.load(uploaded)

alloc = data["allocation"]
maxm = data["max"]
avail = data["available"]

st.sidebar.subheader("Arrival schedule (dynamic)")
st.sidebar.caption("Format: t:vec ; multiple entries separated by ; Example: 1:4,3,3;3:2,1,1")
arrival_raw = st.sidebar.text_input("Arrivals", value="")
arrival_schedule = parse_arrival_input(arrival_raw)

# Left column: Matrices + controls
col1, col2 = st.columns([1, 1])

with col1:
    st.header("System Matrices")
    st.write("Allocation")
    st.dataframe(pd.DataFrame(alloc))
    st.write("Max")
    st.dataframe(pd.DataFrame(maxm))
    st.write("Available")
    st.write(avail)
    st.write("Need (Max - Allocation)")
    st.dataframe(pd.DataFrame(count_need(alloc, maxm)))

with col2:
    st.header("Run Simulation")
    if st.button("Run Standard Banker"):
        steps_std, metrics_std, seq_std = run_standard_with_steps(alloc, maxm, avail)
        st.session_state["std"] = {"steps": steps_std, "metrics": metrics_std, "seq": seq_std, "index": 0}
        st.success("Standard simulation completed")
    if st.button("Run Dynamic Banker"):
        steps_dyn, metrics_dyn, seq_dyn = run_dynamic_with_steps(alloc, maxm, avail, arrival_schedule)
        st.session_state["dyn"] = {"steps": steps_dyn, "metrics": metrics_dyn, "seq": seq_dyn, "index": 0}
        st.success("Dynamic simulation completed")

    st.markdown("---")
    st.header("Quick Metrics (last run)")
    if "std" in st.session_state:
        m = st.session_state["std"]["metrics"]
        st.subheader("Standard")
        st.write(f"Safe sequence: {st.session_state['std']['seq']}")
        st.write(f"Total comparisons: {m['total_comparisons']}")
        st.write(f"Iterations: {m['total_iterations']}")
        st.write(f"Elapsed (s): {m['elapsed_time']:.6f}")

    if "dyn" in st.session_state:
        m = st.session_state["dyn"]["metrics"]
        st.subheader("Dynamic")
        st.write(f"Safe sequence: {st.session_state['dyn']['seq']}")
        st.write(f"Total comparisons: {m['total_comparisons']}")
        st.write(f"Iterations: {m['total_iterations']}")
        st.write(f"Elapsed (s): {m['elapsed_time']:.6f}")

# Middle area: Step viewer
st.markdown("---")
st.header("Step-by-step Viewer")

which = st.radio("Which simulation", options=["Standard", "Dynamic"])
key = "std" if which == "Standard" else "dyn"

if key not in st.session_state:
    st.info("Run the corresponding simulation first from the right panel.")
else:
    sim = st.session_state[key]
    steps = sim["steps"]
    idx = sim.get("index", 0)

    cola, colb, colc = st.columns([1, 4, 1])
    with cola:
        if st.button("<< Prev"):
            idx = max(0, idx-1)
        st.session_state[key]["index"] = idx

    with colc:
        if st.button("Next >>"):
            idx = min(len(steps)-1, idx+1)
        st.session_state[key]["index"] = idx

    # show step info
    cur = steps[idx]
    st.subheader(f"Step {idx} — {cur.get('t', '')}")
    if cur.get("arrivals"):
        st.info(f"Arrivals at this step: {cur.get('arrivals')}")
    executed = cur.get("executed")
    if executed is not None:
        st.success(f"Process executed: P{executed}")

    st.write(f"Comparisons so far: {cur.get('comparisons_so_far', 0)}")

    # show matrices side-by-side
    a1, a2, a3 = st.columns(3)
    with a1:
        st.write("Allocation")
        df_alloc = pd.DataFrame(cur["allocation"])
        # highlight executed row
        def highlight_exec(row):
            i = executed
            if i is None:
                return [""]*len(row)
            return ["background-color: #b6f5b6" if idx_row==i else "" for idx_row in range(len(row))]
        st.dataframe(df_alloc.style.apply(lambda r: highlight_exec(r), axis=1))

    with a2:
        st.write("Max")
        st.dataframe(pd.DataFrame(cur["max"]))

    with a3:
        st.write("Need")
        st.dataframe(pd.DataFrame(cur["need"]))

    st.write("Available")
    st.write(cur["available"])

    # bottom: charts comparing metrics if both runs done
    if "std" in st.session_state and "dyn" in st.session_state:
        st.markdown("---")
        st.header("Comparison Charts")
        mstd = st.session_state["std"]["metrics"]
        mdyn = st.session_state["dyn"]["metrics"]
        comp_df = pd.DataFrame({
            "metric": ["comparisons", "iterations", "time_s"],
            "standard": [mstd["total_comparisons"], mstd["total_iterations"], mstd["elapsed_time"]],
            "dynamic": [mdyn["total_comparisons"], mdyn["total_iterations"], mdyn["elapsed_time"]],
        }).set_index("metric")
        st.write(comp_df)

        # simple bar chart
        st.subheader("Bar chart (standard vs dynamic)")
        fig, ax = plt.subplots()
        comp_df.plot.bar(ax=ax)
        st.pyplot(fig)
