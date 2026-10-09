import streamlit as st

def compute_spherical_equivalent(sphere: float, cylinder: float) -> float:
    """Calculates Spherical Equivalent: SE = Sphere + (Cylinder / 2)."""
    return round(sphere + (cylinder / 2.0), 2)

def compute_eye_tokens(sphere: float, cylinder: float, axis: int, reading_add: float = 0.0) -> dict:
    """Calculates typography and accessibility tokens for an individual eye."""
    # Defensive checks
    if not (-20.0 <= sphere <= 15.0):
        raise ValueError(f"Sphere power {sphere}D exceeds physiological boundary limits [-20.0, +15.0].")
    if not (-10.0 <= cylinder <= 0.0):
        raise ValueError(f"Cylinder power {cylinder}D must be in negative format [-10.0, 0.0].")
    if not (1 <= axis <= 180):
        raise ValueError(f"Axis {axis}° must sit within [1, 180].")
    if not (0.0 <= reading_add <= 4.0):
        raise ValueError(f"Near reading add +{reading_add}D exceeds range [0.0, +4.0].")

    se = compute_spherical_equivalent(sphere, cylinder)
    base_font_size = 16.0
    base_line_height = 1.5

    # Accommodative & myopic defocus compensation
    near_scale = max(0.0, reading_add) * 0.25
    myopic_blur_scale = max(0.0, abs(sphere)) * 0.12 if sphere < -1.5 else 0.0
    total_scale = 1.0 + near_scale + myopic_blur_scale
    font_size = round(base_font_size * total_scale, 1)

    abs_cyl = abs(cylinder)
    if abs_cyl >= 2.0:
        weight = 700
        letter_spacing = 1.2
        theme = "ultra_high_contrast"
    elif abs_cyl >= 0.75:
        weight = 600
        letter_spacing = 0.6
        theme = "high_contrast"
    else:
        weight = 400
        letter_spacing = 0.0
        theme = "standard"

    line_height = round(base_line_height + (reading_add * 0.1), 2)

    return {
        "spherical_equivalent": se,
        "font_size_px": f"{font_size}px",
        "font_size_num": font_size,
        "font_weight": weight,
        "line_height": line_height,
        "letter_spacing_px": f"{letter_spacing}px",
        "theme": theme,
        "abs_cyl": abs_cyl
    }

def synthesize_binocular(od: dict, os: dict) -> dict:
    """
    Synthesizes OD and OS for binocular viewing:
    - Font size: scaled to the more visually compromised eye (worst-case compensation)
    - Contrast: highest contrast demanded by either eye
    - Letter spacing: widest tracking demanded by either eye
    """
    final_font_size = max(od["font_size_num"], os["font_size_num"])
    final_weight = max(od["font_weight"], os["font_weight"])
    final_line_height = max(od["line_height"], os["line_height"])
    
    # Priority: ultra_high_contrast > high_contrast > standard
    if od["theme"] == "ultra_high_contrast" or os["theme"] == "ultra_high_contrast":
        final_theme = "ultra_high_contrast"
        letter_spacing = 1.2
    elif od["theme"] == "high_contrast" or os["theme"] == "high_contrast":
        final_theme = "high_contrast"
        letter_spacing = 0.6
    else:
        final_theme = "standard"
        letter_spacing = 0.0

    return {
        "font_size_px": f"{final_font_size}px",
        "font_size_num": final_font_size,
        "font_weight": final_weight,
        "line_height": final_line_height,
        "letter_spacing_px": f"{letter_spacing}px",
        "theme": final_theme
    }

# --- Streamlit Presentation Layer ---
st.set_page_config(
    page_title="OptiScale | Binocular Optical Accessibility",
    page_icon="👁",
    layout="wide"
)

st.title("👁️ OptiScale: Binocular Visual Accessibility Engine")
st.caption("Translates bilateral refractive prescriptions (OD, OS, and Binocular Synthesis) into calibrated digital typography.")

st.divider()

col_od, col_os = st.columns(2, gap="medium")

# --- Right Eye (OD) ---
with col_od:
    st.subheader("Right Eye (OD - Oculus Dexter)")
    c1, c2, c3 = st.columns(3)
    with c1:
        od_sph = st.number_input("Sphere (OD)", min_value=-20.0, max_value=+15.0, value=-1.50, step=0.25, key="od_sph")
    with c2:
        od_cyl = st.number_input("Cylinder (OD)", min_value=-10.0, max_value=0.0, value=-0.75, step=0.25, key="od_cyl")
    with c3:
        od_axis = st.number_input("Axis (OD)", min_value=1, max_value=180, value=90, step=1, key="od_axis")
    od_add = st.number_input("Near Add (OD)", min_value=0.0, max_value=+4.0, value=+1.75, step=0.25, key="od_add")

# --- Left Eye (OS) ---
with col_os:
    st.subheader("Left Eye (OS - Oculus Sinister)")
    c4, c5, c6 = st.columns(3)
    with c4:
        os_sph = st.number_input("Sphere (OS)", min_value=-20.0, max_value=+15.0, value=-2.25, step=0.25, key="os_sph")
    with c5:
        os_cyl = st.number_input("Cylinder (OS)", min_value=-10.0, max_value=0.0, value=-1.75, step=0.25, key="os_cyl")
    with c6:
        os_axis = st.number_input("Axis (OS)", min_value=1, max_value=180, value=85, step=1, key="os_axis")
    os_add = st.number_input("Near Add (OS)", min_value=0.0, max_value=+4.0, value=+1.75, step=0.25, key="os_add")

st.divider()

# --- Compute Models ---
try:
    od_tokens = compute_eye_tokens(od_sph, od_cyl, od_axis, od_add)
    os_tokens = compute_eye_tokens(os_sph, os_cyl, os_axis, os_add)
    bino_tokens = synthesize_binocular(od_tokens, os_tokens)
except ValueError as err:
    st.error(f"Input Validation Error: {str(err)}")
    st.stop()

# --- Tabbed Visualizer ---
st.subheader("Calibrated Typographic View")
view_mode = st.radio(
    "Select Perspective to Preview:",
    ["Binocular View (Both Eyes Compensated)", "Right Eye (OD) Isolated", "Left Eye (OS) Isolated"],
    horizontal=True
)

if view_mode == "Right Eye (OD) Isolated":
    active_tokens = od_tokens
    active_label = "OD (Right Eye)"
    se_display = f"OD Spherical Equivalent: {od_tokens['spherical_equivalent']:+.2f} D"
elif view_mode == "Left Eye (OS) Isolated":
    active_tokens = os_tokens
    active_label = "OS (Left Eye)"
    se_display = f"OS Spherical Equivalent: {os_tokens['spherical_equivalent']:+.2f} D"
else:
    active_tokens = bino_tokens
    active_label = "Binocular (Both Eyes Combined)"
    se_display = f"OD SE: {od_tokens['spherical_equivalent']:+.2f} D | OS SE: {os_tokens['spherical_equivalent']:+.2f} D"

# Metric & Clinical Badges
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Active Mode", active_label)
with col_m2:
    st.metric("Prescribed Font Scale", active_tokens["font_size_px"])
with col_m3:
    st.metric("Calculated SE", se_display)

# Anisometropia detection (> 1.50D difference between eyes)
se_diff = abs(od_tokens['spherical_equivalent'] - os_tokens['spherical_equivalent'])
if se_diff >= 1.50:
    st.warning(f"⚠️ Anisometropia Alert (|ΔSE| = {se_diff:.2f}D): Significant refractive asymmetry detected between eyes. Binocular sizing has been prioritized for the weaker meridian.")

# Theme Styling
theme = active_tokens["theme"]
if theme == "ultra_high_contrast":
    bg, txt, bdr = "#000000", "#FFD700", "#FFD700"
elif theme == "high_contrast":
    bg, txt, bdr = "#0F172A", "#F8FAFC", "#38BDF8"
else:
    bg, txt, bdr = "#F8FAFC", "#0F172A", "#CBD5E1"

style_block = (
    f"background-color:{bg}; color:{txt}; padding:28px; border-radius:12px; "
    f"border:2px solid {bdr}; font-size:{active_tokens['font_size_px']}; "
    f"font-weight:{active_tokens['font_weight']}; line-height:{active_tokens['line_height']}; "
    f"letter-spacing:{active_tokens['letter_spacing_px']}; font-family:system-ui, sans-serif;"
)

preview_html = (
    f'<div style="{style_block}">'
    '<h4 style="margin-top:0; color:inherit;">Ophthalmic Care & Post-Exam Instructions</h4>'
    '<p>1. <strong>Pupil Dilation:</strong> Photophobia and transient cycloplegia may persist for 4 to 6 hours. Wear UV-protective sunglasses outdoors.</p>'
    '<p>2. <strong>Near Distance Tasks:</strong> Avoid sustained micro-print reading until dynamic accommodation stabilizes.</p>'
    '<p>3. <strong>Emergency Warning:</strong> Seek acute ophthalmic care immediately if you notice sudden shower of floaters, flashes of light, or visual field loss.</p>'
    '</div>'
)

st.markdown(preview_html, unsafe_allow_html=True)

st.markdown("#### Generated CSS Output")
st.code(
    f"/* Synthesized CSS Tokens for {active_label} */\n"
    f"font-size: {active_tokens['font_size_px']};\n"
    f"font-weight: {active_tokens['font_weight']};\n"
    f"line-height: {active_tokens['line_height']};\n"
    f"letter-spacing: {active_tokens['letter_spacing_px']};\n"
    f"/* Contrast mode: {active_tokens['theme']} */",
    language="css"
)