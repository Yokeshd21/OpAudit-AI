import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from utils import load_css, extract_text, calculate_performance, create_excel_download, create_pdf_download, apply_color_coding
from ai_wrapper import get_groq_client, evaluate_performance

st.set_page_config(
    page_title="OpAudit AI — Enterprise Performance Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css("style.css")

# ─── Inline global overrides ─────────────────────────────────────────────────
st.markdown("""
<style>
/* Layout padding */
.block-container {
    padding: 1.5rem 2.5rem 2rem 2.5rem !important;
    max-width: 100% !important;
}

/* ── Hero Header ── */
.hero-wrap {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem 1rem;
    margin-bottom: 1.5rem;
}
.hero-logo {
    font-size: 3.5rem;
    display: block;
    margin-bottom: 0.4rem;
    filter: drop-shadow(0 0 18px rgba(0,229,255,0.6));
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -1px;
    text-shadow: 0 0 20px rgba(0,229,255,0.5), 0 0 40px rgba(0,85,255,0.3);
    margin: 0 0 0.35rem 0;
    line-height: 1.15;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: #8fa0ba;
    letter-spacing: 0.3px;
    margin: 0;
}
.hero-divider {
    width: 100px;
    height: 3px;
    background: linear-gradient(90deg, #0055ff, #00e5ff);
    border-radius: 99px;
    margin: 1.2rem auto 0 auto;
}

/* ── KPI Metric Cards ── */
.metric-card {
    background: rgba(16, 25, 43, 0.55);
    border: 1px solid rgba(0,229,255,0.15);
    border-radius: 14px;
    padding: 22px 18px;
    text-align: center;
    height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: all 0.35s ease;
}
.metric-card:hover {
    border-color: rgba(0,229,255,0.45);
    box-shadow: 0 0 22px rgba(0,229,255,0.12);
    transform: translateY(-3px);
}
.metric-card .label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #8fa0ba;
    text-transform: uppercase;
    letter-spacing: 1.8px;
    margin-bottom: 8px;
}
.metric-card .value {
    font-size: 2.2rem;
    font-weight: 900;
    line-height: 1;
    color: #00e5ff;
    text-shadow: 0 0 14px rgba(0,229,255,0.4);
}
.metric-card .value.good { color: #00ffaa; text-shadow: 0 0 14px rgba(0,255,170,0.4); }
.metric-card .value.warn { color: #ffc400; text-shadow: 0 0 14px rgba(255,196,0,0.4); }
.metric-card .value.bad  { color: #ff3366; text-shadow: 0 0 14px rgba(255,51,102,0.4); }

/* ── Section headers ── */
.sec-head {
    font-size: 1.15rem;
    font-weight: 800;
    color: #fff;
    text-shadow: 0 0 12px rgba(0,229,255,0.35);
    border-bottom: 1px solid rgba(0,229,255,0.2);
    padding-bottom: 0.5rem;
    margin: 2rem 0 1rem 0;
}

/* ── Sidebar polish ── */
[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1.2rem !important;
}
[data-testid="stSidebar"] .stFileUploader > label {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #e0e6ed !important;
}
[data-testid="stSidebar"] h3 {
    font-size: 1rem !important;
    margin-top: 1.2rem !important;
    margin-bottom: 0.4rem !important;
}

/* ── Executive Summary items ── */
.exec-item {
    background: rgba(0,229,255,0.04);
    border-left: 3px solid rgba(0,229,255,0.3);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 10px;
}
.exec-item .ek {
    font-size: 0.72rem;
    color: #8fa0ba;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 3px;
}
.exec-item .ev {
    font-size: 0.9rem;
    color: #e0e6ed;
    line-height: 1.4;
}

/* ── Download buttons ── */
.stDownloadButton > button {
    background: linear-gradient(90deg, #0055ff, #00ccff) !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)


# ─── State ────────────────────────────────────────────────────────────────────
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_evaluation' not in st.session_state:
    st.session_state.current_evaluation = None

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 0.5rem 0 1.2rem 0;'>
        <span style='font-size:2.8rem; filter:drop-shadow(0 0 12px rgba(0,229,255,0.6));'>🛡️</span>
        <div style='font-size:1.1rem; font-weight:800; color:#fff; letter-spacing:-0.5px; margin-top:6px;'>OpAudit AI</div>
        <div style='font-size:0.75rem; color:#8fa0ba; letter-spacing:1px; text-transform:uppercase;'>Operational Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(0,229,255,0.05); padding:14px; border-radius:10px; border:1px solid rgba(0,229,255,0.18); margin-bottom:1.2rem;'>
        <div style='font-size:0.78rem; font-weight:700; color:#00e5ff; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px;'>System Directives</div>
        <ul style='font-size:0.83rem; padding-left:18px; color:#8fa0ba; margin:0; line-height:1.8;'>
            <li>Upload the official <b style='color:#e0e6ed;'>Operational Rubric</b></li>
            <li>Upload the official <b style='color:#e0e6ed;'>Employee Narrative</b></li>
            <li>AI audits strict compliance and execution gaps</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.78rem; font-weight:700; color:#00e5ff; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px;'>Document Ingestion</div>", unsafe_allow_html=True)
    rubric_file = st.file_uploader("📋 Operational Rubric", type=["pdf", "docx", "txt"])
    narrative_file = st.file_uploader("📝 Employee Narrative", type=["pdf", "docx", "txt"])

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    analyze_btn = st.button("🚀 Execute Operational Audit", use_container_width=True)

    st.markdown("<div style='margin: 1.2rem 0; border-top: 1px solid rgba(0,229,255,0.12);'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.78rem; font-weight:700; color:#00e5ff; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px;'>🕒 Session History</div>", unsafe_allow_html=True)
    if not st.session_state.history:
        st.markdown("<p style='font-size:0.8rem; color:rgba(255,255,255,0.28); margin:0;'>No audits performed yet.</p>", unsafe_allow_html=True)
    else:
        for record in reversed(st.session_state.history[-5:]):
            color = '#00ffaa' if record['score'] >= 75 else '#ffc400' if record['score'] >= 50 else '#ff3366'
            st.markdown(f"""
            <div style='background:rgba(16,25,43,0.5); padding:10px 14px; border-radius:8px; margin-bottom:8px; border-left:3px solid {color};'>
                <div style='font-size:0.72rem; color:#8fa0ba;'>{time.strftime('%d %b  %H:%M', time.localtime(record['timestamp']))}</div>
                <div style='font-weight:800; font-size:1.05rem; color:{color}; margin-top:2px;'>{record['score']}%</div>
            </div>""", unsafe_allow_html=True)

# ─── HERO HEADER ──────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero-wrap'>
    <span class='hero-logo'>🛡️</span>
    <h1 class='hero-title'>Enterprise Operational Performance Intelligence</h1>
    <p class='hero-subtitle'>AI-powered strict operational audit &amp; compliance evaluation platform</p>
    <div class='hero-divider'></div>
</div>
""", unsafe_allow_html=True)

# ─── AUDIT TRIGGER ────────────────────────────────────────────────────────────
if analyze_btn:
    if not rubric_file or not narrative_file:
        st.error("⚠️  Please upload both the Rubric and Narrative documents.")
    else:
        client = get_groq_client()
        if not client:
            st.error("🔑  Groq API Key missing. Set the `GROQ_API_KEY` environment variable.")
        else:
            with st.spinner("🤖  AI Auditor analysing operational data…"):
                rubric_text   = extract_text(rubric_file)
                narrative_text = extract_text(narrative_file)
                result_json   = evaluate_performance(
                    client=client,
                    rubric_text=rubric_text,
                    narrative_text=narrative_text,
                    model="llama-3.3-70b-versatile",
                    temperature=0.0
                )
                if result_json:
                    st.session_state.current_evaluation = result_json
                    st.session_state.history.append({
                        "timestamp": time.time(),
                        "score": calculate_performance(result_json)[0],
                        "data": result_json
                    })
                    st.success("✅  Audit Complete!")

# ─── RESULTS DASHBOARD ────────────────────────────────────────────────────────
if st.session_state.current_evaluation:
    data = st.session_state.current_evaluation
    score, band, risk, supervision, badge_html = calculate_performance(data)
    meets = all(str(i.get("Status","")).strip().upper() == "YES" for i in data.get("Evaluation", []))

    def color_class(val, good, bad):
        v = str(val).strip().upper()
        if v in bad:  return "bad"
        if v in good: return "good"
        return "warn"

    sc = "good" if score >= 75 else "warn" if score >= 50 else "bad"
    rc = color_class(risk, {"LOW"}, {"HIGH","CRITICAL"})
    vc = color_class(supervision, {"MINIMAL","STANDARD"}, {"DIRECT"})
    mc = "good" if meets else "bad"

    # ── KPI ROW ──────────────────────────────────────────────────────────────
    st.markdown("<div class='sec-head'>📊  Performance Overview</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    metrics = [
        (c1, "Performance Score", f"{score}%", sc, badge_html),
        (c2, "Compliance Risk",   risk,         rc, ""),
        (c3, "Supervision Level", supervision,  vc, ""),
        (c4, "Meets Standards",   "PASS" if meets else "FAIL", mc, ""),
    ]
    for col, label, value, cls, extra in metrics:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='label'>{label}</div>
                <div class='value {cls}'>{value}</div>
                {"<div style='margin-top:8px;'>"+extra+"</div>" if extra else ""}
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── AUDIT TABLE ──────────────────────────────────────────────────────────
    st.markdown("<div class='sec-head'>🗂  Operational Audit Matrix</div>", unsafe_allow_html=True)
    if "Evaluation" in data:
        df = pd.DataFrame(data["Evaluation"])
        st.dataframe(
            df.style.map(apply_color_coding),
            use_container_width=True,
            hide_index=True,
            height=360
        )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── INSIGHTS: RADAR CHART ────────────────────────────────────────────────
    st.markdown("<div class='sec-head'>📡  Criteria Radar — Compliance Coverage</div>", unsafe_allow_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)

    if "Evaluation" in data:
        evals = data["Evaluation"]
        criteria   = [i.get("Criterion", "?")        for i in evals]
        status_r   = [1.0 if str(i.get("Status","")).strip().upper()=="YES" else 0.15 for i in evals]
        ev_map     = {"STRONG":1.0, "MODERATE":0.65, "WEAK":0.35, "NONE":0.1}
        evi_r      = [ev_map.get(str(i.get("Evidence Strength","")).strip().upper(), 0.1) for i in evals]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=[*status_r, status_r[0]],
            theta=[*criteria, criteria[0]],
            fill='toself',
            fillcolor='rgba(0,229,255,0.15)',
            line=dict(color='#00e5ff', width=2.5),
            name='Compliance Status',
            hovertemplate='<b>%{theta}</b><br>Status Score: %{r:.0%}<extra></extra>'
        ))

        fig.add_trace(go.Scatterpolar(
            r=[*evi_r, evi_r[0]],
            theta=[*criteria, criteria[0]],
            fill='toself',
            fillcolor='rgba(255,196,0,0.08)',
            line=dict(color='#ffc400', width=1.8, dash='dot'),
            name='Evidence Strength',
            hovertemplate='<b>%{theta}</b><br>Evidence Score: %{r:.0%}<extra></extra>'
        ))

        fig.update_layout(
            polar=dict(
                bgcolor='rgba(4,11,22,0.6)',
                radialaxis=dict(
                    visible=True,
                    range=[0, 1.05],
                    tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                    ticktext=['0%','25%','50%','75%','100%'],
                    tickfont=dict(size=10, color='#8fa0ba'),
                    gridcolor='rgba(255,255,255,0.08)',
                    linecolor='rgba(255,255,255,0.08)',
                ),
                angularaxis=dict(
                    tickfont=dict(size=12, color='#e0e6ed'),
                    gridcolor='rgba(255,255,255,0.07)',
                    linecolor='rgba(0,229,255,0.15)',
                )
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', color='#e0e6ed'),
            legend=dict(
                orientation='h',
                yanchor='bottom', y=-0.15,
                xanchor='center', x=0.5,
                font=dict(size=12, color='#e0e6ed'),
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(l=60, r=60, t=30, b=60),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── INSIGHTS: EXECUTIVE SUMMARY ──────────────────────────────────────────
    st.markdown("<div class='sec-head'>📋  Executive Operational Summary</div>", unsafe_allow_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if "Executive Summary" in data:
        for k, v in data["Executive Summary"].items():
            st.markdown(f"""
            <div class='exec-item'>
                <div class='ek'>{k}</div>
                <div class='ev'>{v}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── EXPORT ───────────────────────────────────────────────────────────────
    st.markdown("<div class='sec-head'>💾  Export Intelligence</div>", unsafe_allow_html=True)
    export_df  = pd.DataFrame(data.get("Evaluation", []))
    excel_data = create_excel_download(export_df)
    pdf_data   = create_pdf_download(data)

    dl1, dl2, _sp = st.columns([1, 1, 1.8], gap="medium")
    with dl1:
        st.download_button("📥 Download Excel", data=excel_data,
            file_name="audit_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with dl2:
        st.download_button("📄 Download PDF", data=pdf_data,
            file_name="audit_report.pdf", mime="application/pdf",
            use_container_width=True)

elif not analyze_btn:
    st.markdown("""
    <div class='glass-card' style='text-align:center; padding:80px 40px; margin-top:10px;'>
        <div style='font-size:3.5rem; margin-bottom:16px;'>🛡️</div>
        <h2 style='color:rgba(255,255,255,0.55); font-size:1.6rem; margin-bottom:10px;'>Awaiting Data Ingestion</h2>
        <p style='color:rgba(255,255,255,0.3); font-size:1rem; max-width:480px; margin:0 auto; line-height:1.6;'>
            Upload an Operational Rubric and Employee Narrative via the sidebar to initiate the AI intelligence audit.
        </p>
    </div>
    """, unsafe_allow_html=True)
