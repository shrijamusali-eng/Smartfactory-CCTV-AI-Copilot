import streamlit as st
from datetime import datetime, timedelta
from database.db import get_connection
from ai.llm import llm_manager

# ==========================================
# 1. DATA ACQUISITION & TELEMETRY LAYER
# ==========================================

def fetch_realtime_dashboard_data() -> dict:
    """Queries live telemetry aggregates to populate real-time dashboard visualization layers."""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    with get_connection() as conn:
        # 1. Timeline Log Distribution (Last 7 Days Trendline)
        trend_rows = conn.execute("""
            SELECT DATE(timestamp) as day, COUNT(*) as count 
            FROM events 
            GROUP BY day 
            ORDER BY day DESC 
            LIMIT 7
        """).fetchall()
        
        # 2. Zone Vulnerability Matrix (Physical Space Hazard Density)
        zone_rows = conn.execute("""
            SELECT zone, COUNT(*) as count 
            FROM events 
            WHERE DATE(timestamp) = ? 
            GROUP BY zone
        """, (today,)).fetchall()
        
        # 3. PPE Gear Attestation (Compliance Percentages)
        total_checks = conn.execute(
            "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ?", (today,)
        ).fetchone()[0] or 1
        
        no_helmet = conn.execute(
            "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event = 'no-helmet'", (today,)
        ).fetchone()[0] or 0
        
        no_vest = conn.execute(
            "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event = 'no-vest'", (today,)
        ).fetchone()[0] or 0
        
        # 4. Day-over-Day overall PPE trend variance for AI narrative grounding
        ppe_today = conn.execute(
            "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event IN ('no-helmet', 'no-vest')", (today,)
        ).fetchone()[0] or 0
        
        ppe_yesterday = conn.execute(
            "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event IN ('no-helmet', 'no-vest')", (yesterday,)
        ).fetchone()[0] or 0

        # 5. Impact Allocation Vectors (Risk Severity Distribution)
        severity_rows = conn.execute("""
            SELECT severity, COUNT(*) as count 
            FROM events 
            WHERE DATE(timestamp) = ? 
            GROUP BY severity
        """, (today,)).fetchall()

    # Calculate day-over-day changes safely
    if ppe_yesterday > 0:
        pct_change = round(((ppe_today - ppe_yesterday) / ppe_yesterday) * 100, 1)
    else:
        pct_change = 100.0 if ppe_today > 0 else 0.0

    # Sort zone rows cleanly to pinpoint the absolute highest hazard localized zone
    sorted_zones = sorted(zone_rows, key=lambda x: x[1], reverse=True) if zone_rows else []
    top_zone = sorted_zones[0][0] if sorted_zones else "All Zones Normal"

    total_ppe_issues = ppe_today if ppe_today > 0 else 1
    helmet_ratio = round((no_helmet / total_ppe_issues) * 100, 1)

    return {
        "date": today,
        "trends": [{"day": r[0], "incidents": r[1]} for r in reversed(trend_rows)] if trend_rows else [{"day": today, "incidents": 0}],
        "heatmap": {r[0]: r[1] for r in zone_rows} if zone_rows else {"Zone A": 0, "Zone B": 0},
        "compliance": {
            "helmet_compliance_rate": round(((total_checks - no_helmet) / total_checks) * 100, 1),
            "vest_compliance_rate": round(((total_checks - no_vest) / total_checks) * 100, 1),
            "total_inspections": total_checks
        },
        "severity": {r[0]: r[1] for r in severity_rows} if severity_rows else {"low": 0, "medium": 0, "high": 0},
        "insights_payload": {
            "change_pct": pct_change,
            "top_zone": top_zone,
            "helmet_share": helmet_ratio
        }
    }

# ==========================================
# 2. AI GENERATIVE NARRATIVE LAYER
# ==========================================

def generate_prescriptive_recommendation(stats: dict) -> str:
    """Leverages the LLM engine to synthesize a data-grounded floor recommendation."""
    llm = llm_manager.get_fast_llm()
    
    system_prompt = (
        "You are an expert industrial safety engineer. Review the raw factory data updates "
        "and provide exactly one specific, highly tactical floor recommendation (under 15 words) "
        "directed to morning/evening shift managers. Do not include pleasantries, introductory prose, "
        "or repeat the data points. Start immediately with the recommendation."
    )
    
    data_payload = (
        f"PPE change today: {stats['change_pct']}%. "
        f"Highest incidents: {stats['top_zone']}. "
        f"Helmet ratio: {stats['helmet_share']}%."
    )
    
    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": data_payload}
        ])
        return response.content.strip()
    except Exception:
        return "Increase physical supervisor walkthroughs during peak transition shifts."

# ==========================================
# 3. INTERFACE VIEW RENDERING LAYER
# ==========================================

def render_analytics_dashboard():
    """Renders the dashboard workspace complete with dynamic telemetry scorecards and AI Insights."""
    st.markdown("## 🏭 SmartFactory Real-Time Safety Command Center")
    st.markdown("Live multi-dimensional telemetry tracking for PPE assurance and facility threat monitoring.")
    
    # 1. Collect all telemetry and baseline metrics from the database tier
    data = fetch_realtime_dashboard_data()
    insights_data = data["insights_payload"]
    
    # 2. UI Component: AI Safety Insights Callout Box
    st.markdown("### 🧠 AI Safety Insights")
    with st.spinner("Analyzing site safety trends..."):
        recommendation = generate_prescriptive_recommendation(insights_data)
        
    insight_markdown = f"""
    * **PPE compliance shift:** Violations changed by **{insights_data['change_pct']}%** today.
    * **Hotspot localized:** **{insights_data['top_zone']}** recorded the highest number of plant floor incidents.
    * **Distribution profile:** Helmet exceptions account for **{insights_data['helmet_share']}%** of all active safety issues.
    * **Recommendation:** {recommendation}
    """
    st.info(insight_markdown)
    st.markdown("---")
    
    # 3. UI Component: Rapid Scorecard Metrics Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Shift Inspections Tracked", f"{data['compliance']['total_inspections']} events")
    with col2:
        st.metric("Helmet Compliance Score", f"{data['compliance']['helmet_compliance_rate']}%")
    with col3:
        st.metric("Safety Vest Compliance Score", f"{data['compliance']['vest_compliance_rate']}%")
        
    st.markdown("---")
    st.markdown("### 📊 Live Plant Floor Operations Analysis")
    
    # (Remaining code for charts, dataframes, or raw log tables can follow below smoothly)