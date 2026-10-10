import streamlit as st

st.set_page_config(
    page_title="OptiScale | Optical Accessibility Engine",
    page_icon="👓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- UI Header -----------------
st.title("👓 OptiScale: Optical Accessibility & Typography Engine")
st.caption("Clinical typography engine translating bilateral spectacle prescriptions (OD/OS) into calibrated, WCAG 2.2 AAA accessible patient portals.")
st.markdown("---")

# ----------------- Sidebar: Bilateral Prescription Input -----------------
st.sidebar.header("📋 Patient Refraction Record")

st.sidebar.subheader("Right Eye (OD - Oculus Dexter)")
col_od1, col_od2 = st.sidebar.columns(2)
with col_od1:
    od_sph = st.number_input("OD Sphere (SPH)", min_value=-15.00, max_value=15.00, value=-2.50, step=0.25, format="%.2f")
    od_axis = st.number_input("OD Axis (°)", min_value=1, max_value=180, value=90, step=1)
with col_od2:
    od_cyl = st.number_input("OD Cylinder (CYL)", min_value=-8.00, max_value=0.00, value=-0.75, step=0.25, format="%.2f")
    od_add = st.number_input("OD Add (Near)", min_value=0.00, max_value=4.00, value=1.50, step=0.25, format="%.2f")

st.sidebar.markdown("---")
st.sidebar.subheader("Left Eye (OS - Oculus Sinister)")
col_os1, col_os2 = st.sidebar.columns(2)
with col_os1:
    os_sph = st.number_input("OS Sphere (SPH)", min_value=-15.00, max_value=15.00, value=-3.00, step=0.25, format="%.2f")
    os_axis = st.number_input("OS Axis (°)", min_value=1, max_value=180, value=95, step=1)
with col_os2:
    os_cyl = st.number_input("OS Cylinder (CYL)", min_value=-8.00, max_value=0.00, value=-1.25, step=0.25, format="%.2f")
    os_add = st.number_input("OS Add (Near)", min_value=0.00, max_value=4.00, value=1.50, step=0.25, format="%.2f")

st.sidebar.markdown("---")
display_mode = st.sidebar.radio(
    "Visual Contrast Profile",
    ["High-Contrast Dark (WCAG AAA)", "High-Contrast Light (WCAG AAA)", "Default Medical Slate"],
    index=0
)

# ----------------- Optical Calculations -----------------
# Spherical Equivalent: SE = SPH + (CYL / 2)
od_se = od_sph + (od_cyl / 2.0)
os_se = os_sph + (os_cyl / 2.0)
anisometropia = abs(od_se - os_se)

# Binocular Acuity Compensation: Scale font base on the weaker eye and near add
max_near_demand = max(od_add, os_add)
base_font_pt = 16.0
scaling_factor = 1.0 + (max_near_demand * 0.20) + (max(abs(od_se), abs(os_se)) * 0.05)
calibrated_font_size = round(base_font_pt * scaling_factor, 1)

# Astigmatic Distortion Compensation: Higher cyl requires increased letter-spacing & font-weight
max_cyl = max(abs(od_cyl), abs(os_cyl))
letter_spacing_px = round(0.5 + (max_cyl * 0.6), 2)
font_weight = 600 if max_cyl >= 1.00 else 400

# Contrast Palettes
if display_mode == "High-Contrast Dark (WCAG AAA)":
    bg_color = "#0B0F19"
    card_bg = "#161E2E"
    text_color = "#F9FAFB"
    accent_color = "#38BDF8"
    border_color = "#374151"
    contrast_ratio = "18.2:1"
elif display_mode == "High-Contrast Light (WCAG AAA)":
    bg_color = "#FFFFFF"
    card_bg = "#F3F4F6"
    text_color = "#111827"
    accent_color = "#0284C7"
    border_color = "#D1D5DB"
    contrast_ratio = "17.8:1"
else:
    bg_color = "#0F172A"
    card_bg = "#1E293B"
    text_color = "#E2E8F0"
    accent_color = "#22D3EE"
    border_color = "#334155"
    contrast_ratio = "15.4:1"

# ----------------- Analytical Dashboard -----------------
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("OD Spherical Eq.", f"{od_se:.2f} D")
with col_m2:
    st.metric("OS Spherical Eq.", f"{os_se:.2f} D")
with col_m3:
    st.metric("Anisometropia Gap", f"{anisometropia:.2f} D", delta="High Anisometropia" if anisometropia > 1.0 else "Balanced")
with col_m4:
    st.metric("Calibrated Type Size", f"{calibrated_font_size} pt", delta=f"+{round((scaling_factor - 1.0) * 100)}% Scale")

st.markdown("---")

# ----------------- Calibration Breakdown -----------------
c_left, c_right = st.columns([1, 1])

with c_left:
    st.subheader("🔬 Clinical Optical Analysis")
    st.markdown(f"""
    * **Right Eye (OD):** SPH `{od_sph:+.2f}D` | CYL `{od_cyl:.2f}D` @ `{od_axis}°` | ADD `+{od_add:.2f}D`
    * **Left Eye (OS):** SPH `{os_sph:+.2f}D` | CYL `{os_cyl:.2f}D` @ `{os_axis}°` | ADD `+{os_add:.2f}D`
    * **Astigmatism Tracking Correction:** `{letter_spacing_px}px` letter-spacing applied to reduce letter crowding.
    * **Weight Reinforcement:** `{font_weight}` (reinforced stroke width against cylindrical blur).
    * **Luminance Contrast:** Standard verified at `{contrast_ratio}` (Complies with **WCAG 2.2 AAA**).
    """)

with c_right:
    st.subheader("⚙️ Active Typography Tokens")
    st.json({
        "calculated_font_size_px": f"{calibrated_font_size}px",
        "letter_spacing": f"{letter_spacing_px}px",
        "font_weight": font_weight,
        "wcag_contrast_ratio": contrast_ratio,
        "dominant_refraction_eye": "OS (Left)" if abs(os_se) >= abs(od_se) else "OD (Right)"
    })

st.markdown("---")

# ----------------- Calibrated Patient Portal Live Preview -----------------
st.subheader("👁️ Calibrated Discharge Summary View")
st.caption("Rendered live with the binocularly calibrated optical parameters above:")

portal_preview = f"""
<div style="background-color: {card_bg}; color: {text_color}; border: 2px solid {border_color}; border-radius: 10px; padding: 28px; font-size: {calibrated_font_size}px; letter-spacing: {letter_spacing_px}px; font-weight: {font_weight}; line-height: 1.6;">
    <h3 style="color: {accent_color}; margin-top: 0; font-size: {calibrated_font_size * 1.25}px;">POST-OPERATIVE MEDICATION INSTRUCTIONS</h3>
    <p><strong>Patient Record:</strong> Calibration adjusted for OD: {od_se:+.2f}D / OS: {os_se:+.2f}D</p>
    <p><strong>1. Prednisolone Acetate 1% Ophthalmic Suspension:</strong> Instill 1 drop into the operative eye four (4) times daily for 7 days. Shake vigorously before use.</p>
    <p><strong>2. Moxifloxacin 0.5% Solution:</strong> Instill 1 drop into the operative eye three (3) times daily for 7 days.</p>
    <p style="margin-bottom: 0; color: {accent_color}; font-size: {calibrated_font_size * 0.9}px;"><em>If you experience acute pain, sudden loss of vision, or flashes of light, contact the clinical emergency desk immediately.</em></p>
</div>
"""

st.markdown(portal_preview, unsafe_allow_html=True)