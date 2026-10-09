import streamlit as st

# --- WCAG 2.2 Mathematical Contrast Engine ---
def hex_to_rgb(hex_code: str):
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def linearize_rgb(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def compute_relative_luminance(hex_code: str) -> float:
    r, g, b = hex_to_rgb(hex_code)
    return 0.2126 * linearize_rgb(r) + 0.7152 * linearize_rgb(g) + 0.0722 * linearize_rgb(b)

def compute_contrast_ratio(hex1: str, hex2: str) -> float:
    l1 = compute_relative_luminance(hex1)
    l2 = compute_relative_luminance(hex2)
    top, bottom = (l1, l2) if l1 > l2 else (l2, l1)
    return round((top + 0.05) / (bottom + 0.05), 2)

# --- Optical & Typographic Algorithms ---
def compute_spherical_equivalent(sphere: float, cylinder: float) -> float:
    """Calculates Spherical Equivalent: SE = Sphere + (Cylinder / 2)."""
    return round(sphere + (cylinder / 2.0), 2)

def compute_eye_tokens(sphere: float, cylinder: float, axis: int, reading_add: float = 0.0) -> dict:
    """Calculates typography parameters for an individual eye."""
    if not (-20.0 <= sphere <= 15.0):
        raise ValueError(f"Sphere power {sphere}D exceeds physiological boundary limits [-20.0, +15.0].")
    if not (-10.0 <= cylinder <= 0.0):
        raise ValueError(f"Cylinder power {cylinder}D must be formatted in negative notation [-10.0, 0.0].")
    if not (1 <= axis <= 180):
        raise ValueError(f"Astigmatic axis {axis}° must sit within [1, 180].")
    if not (0.0 <= reading_add <= 4.0):
        raise ValueError(f"Near reading add +{reading_add}D exceeds range [0.0, +4.0].")

    se = compute_spherical_equivalent(sphere, cylinder)
    base_font_size = 16.0
    base_line_height = 1.5

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
    """Binocular summation & worst-case blur prevention synthesis."""
    final_font_size = max(od["font_size_num"], os["font_size_num"])
    final_weight = max(od["font_weight"], os["font_weight"])
    final_line_height = max(od["line_height"], os["line_height"])

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

# --- Streamlit Layout ---
st.set_page_config(
    page_title="OptiScale | Optical Accessibility Engine",
    page_icon="👁",
    layout="wide"
)

st.title("👁️ OptiScale: Optical Accessibility Engine")
st.caption("Translates bilateral spectacle prescriptions (OD & OS) into a unified, binocularly compensated digital typography interface.")

st.divider()

# --- Preset Profiles ---
preset_options = {
    "Custom Rx (Manual Entry)": None,
    "Presbyopic Senior (Add +2.50D)": {
        "od": (+1.25, -0.50, 90, 2.50),
        "os": (+1.50, -0.75, 85, 2.50)
    },
    "High Astigmatic Strain (|CYL| >= 2.50D)": {
        "od": (-0.50, -2.75, 180, 0.00),
        "os": (-0.75, -2.50, 175, 0.00)
    },
    "High Myopic Post-Dilation (Severe Accommodative Fatigue)": {
        "od": (-6.50, -1.00, 90, 2.00),
        "os": (-7.00, -1.25, 95, 2.00)
    },
    "Emmetropic Baseline (20/20 Plano)": {
        "od": (0.00, 0.00, 90, 0.00),
        "os": (0.00, 0.00, 90, 0.00)
    }
}

selected_preset = st.selectbox(
    "📋 Clinical Presets (Quick Demonstration):",
    options=list(preset_options.keys())
)

preset_vals = preset_options[selected_preset]

if preset_vals:
    def_od_sph, def_od_cyl, def_od_axis, def_od_add = preset_vals["od"]
    def_os_sph, def_os_cyl, def_os_axis, def_os_add = preset_vals["os"]
else:
    def_od_sph, def_od_cyl, def_od_axis, def_od_add = (-1.50, -0.75, 90, 1.75)
    def_os_sph, def_os_cyl, def_os_axis, def_os_add = (-2.25, -1.75, 85, 1.75)

col_od, col_os = st.columns(2, gap="medium")

with col_od:
    st.subheader("Right Eye (OD - Oculus Dexter)")
    c1, c2, c3 = st.columns(3)
    with c1:
        od_sph = st.number_input("Sphere (OD)", -20.0, 15.0, float(def_od_sph), 0.25, key="od_s")
    with c2:
        od_cyl = st.number_input("Cylinder (OD)", -10.0, 0.0, float(def_od_cyl), 0.25, key="od_c")
    with c3:
        od_axis = st.number_input("Axis (OD)", 1, 180, int(def_od_axis), 1, key="od_a")
    od_add = st.number_input("Near Add (OD)", 0.0, 4.0, float(def_od_add), 0.25, key="od_add")

with col_os:
    st.subheader("Left Eye (OS - Oculus Sinister)")
    c4, c5, c6 = st.columns(3)
    with c4:
        os_sph = st.number_input("Sphere (OS)", -20.0, 15.0, float(def_os_sph), 0.25, key="os_s")
    with c5:
        os_cyl = st.number_input("Cylinder (OS)", -10.0, 0.0, float(def_os_cyl), 0.25, key="os_c")
    with c6:
        os_axis = st.number_input("Axis (OS)", 1, 180, int(def_os_axis), 1, key="os_a")
    os_add = st.number_input("Near Add (OS)", 0.0, 4.0, float(def_os_add), 0.25, key="os_add")

st.divider()

# --- Compute Engine (Automated Binocular Synthesis) ---
try:
    od_tokens = compute_eye_tokens(od_sph, od_cyl, od_axis, od_add)
    os_tokens = compute_eye_tokens(os_sph, os_cyl, os_axis, os_add)
    active = synthesize_binocular(od_tokens, os_tokens)
except ValueError as err:
    st.error(f"Input Validation Error: {str(err)}")
    st.stop()

# --- Theme Color Mapping & Luminance Calculations ---
if active["theme"] == "ultra_high_contrast":
    bg, txt, bdr = "#000000", "#FFD700", "#FFD700"
    mode_name = "Ultra-High Contrast (Maximum Luminance)"
elif active["theme"] == "high_contrast":
    bg, txt, bdr = "#0F172A", "#F8FAFC", "#38BDF8"
    mode_name = "High Contrast Dark Palette"
else:
    bg, txt, bdr = "#F8FAFC", "#0F172A", "#CBD5E1"
    mode_name = "Standard Balanced Contrast"

contrast_ratio = compute_contrast_ratio(txt, bg)
wcag_aaa = "✅ PASS (>= 7.0:1)" if contrast_ratio >= 7.0 else "❌ FAIL"

# Metrics Ribbon
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Synthesized Sizing", active["font_size_px"])
with m2:
    st.metric("Letter Spacing (Tracking)", active["letter_spacing_px"])
with m3:
    st.metric("WCAG 2.2 Contrast Ratio", f"{contrast_ratio}:1")
with m4:
    st.metric("WCAG AAA Compliance", wcag_aaa)

# Anisometropia detection
se_diff = abs(od_tokens["spherical_equivalent"] - os_tokens["spherical_equivalent"])
if se_diff >= 1.50:
    st.warning(f"⚠️ Anisometropia Detected (|ΔSE| = {se_diff:.2f}D): Substantial difference between OD and OS. The typography has automatically scaled to prevent fatigue on the weaker eye.")

# --- Side-by-Side Comparison ---
show_comparison = st.checkbox("Show Before / After Comparison", value=True)

instruction_body = (
    "<h4>Post-Care & Ophthalmic Instructions</h4>"
    "<p>1. <strong>Pupil Dilation & Cycloplegia:</strong> Photophobia and transient blur may persist for 4-6 hours. Avoid sustained screen exposure without adequate contrast.</p>"
    "<p>2. <strong>Near Distance Tasks:</strong> Refrain from micro-font reading until dynamic accommodation stabilizes.</p>"
    "<p>3. <strong>Emergency Protocol:</strong> Contact eye triage immediately if you experience sudden onset flashes of light or a curtain-like shadow across your visual field.</p>"
)

if show_comparison:
    col_before, col_after = st.columns(2, gap="large")
    with col_before:
        st.markdown("**Standard Healthcare Portal (Uncalibrated)**")
        uncalibrated_html = (
            '<div style="background-color:#FFFFFF; color:#64748B; padding:24px; border-radius:12px; '
            'border:1px solid #E2E8F0; font-size:14px; font-weight:400; line-height:1.4; font-family:sans-serif;">'
            f'{instruction_body}'
            '</div>'
        )
        st.markdown(uncalibrated_html, unsafe_allow_html=True)
        st.caption("Standard 14px static gray text creates high crowding and rapid accommodative fatigue.")

    with col_after:
        st.markdown("**OptiScale Calibrated (Binocularly Compensated)**")
        calibrated_html = (
            f'<div style="background-color:{bg}; color:{txt}; padding:24px; border-radius:12px; '
            f'border:2px solid {bdr}; font-size:{active["font_size_px"]}; font-weight:{active["font_weight"]}; '
            f'line-height:{active["line_height"]}; letter-spacing:{active["letter_spacing_px"]}; font-family:system-ui, sans-serif;">'
            f'{instruction_body}'
            '</div>'
        )
        st.markdown(calibrated_html, unsafe_allow_html=True)
        st.caption(f"Adaptive scale, {active['letter_spacing_px']} tracking, and {contrast_ratio}:1 contrast ratio.")
else:
    calibrated_html = (
        f'<div style="background-color:{bg}; color:{txt}; padding:28px; border-radius:12px; '
        f'border:2px solid {bdr}; font-size:{active["font_size_px"]}; font-weight:{active["font_weight"]}; '
        f'line-height:{active["line_height"]}; letter-spacing:{active["letter_spacing_px"]}; font-family:system-ui, sans-serif;">'
        f'{instruction_body}'
        '</div>'
    )
    st.markdown(calibrated_html, unsafe_allow_html=True)

st.divider()

# --- Export & Token Output ---
col_export, col_css = st.columns(2, gap="large")

with col_export:
    st.subheader("📄 Patient Care Sheet Export")
    st.write("Download a standalone HTML document pre-baked with the unified binocular parameters.")

    export_html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>OptiScale Calibrated Patient Care Sheet</title>
  <style>
    body {{
      background-color: {bg};
      color: {txt};
      font-size: {active['font_size_px']};
      font-weight: {active['font_weight']};
      line-height: {active['line_height']};
      letter-spacing: {active['letter_spacing_px']};
      font-family: system-ui, -apple-system, sans-serif;
      padding: 40px;
      margin: 0;
    }}
    .container {{
      max-width: 800px;
      margin: 0 auto;
      border: 2px solid {bdr};
      border-radius: 12px;
      padding: 32px;
    }}
    .footer {{
      margin-top: 24px;
      font-size: 0.85em;
      opacity: 0.8;
      border-top: 1px solid {bdr};
      padding-top: 12px;
    }}
  </style>
</head>
<body>
  <div class="container">
    {instruction_body}
    <div class="footer">
      Calibrated by OptiScale Engine | Mode: Binocular Compensated | Contrast: {contrast_ratio}:1 (WCAG AAA)
    </div>
  </div>
</body>
</html>"""

    st.download_button(
        label="📥 Download Calibrated Patient Care Sheet (.html)",
        data=export_html_content,
        file_name="optiscale_patient_care_sheet.html",
        mime="text/html"
    )

with col_css:
    st.subheader("💻 Generated CSS Tokens")
    st.code(
        f"/* OptiScale CSS Variables (Binocularly Compensated) */\n"
        f"--rx-font-size: {active['font_size_px']};\n"
        f"--rx-font-weight: {active['font_weight']};\n"
        f"--rx-line-height: {active['line_height']};\n"
        f"--rx-letter-spacing: {active['letter_spacing_px']};\n"
        f"--rx-contrast-ratio: {contrast_ratio}:1;\n"
        f"/* Mode: {mode_name} */",
        language="css"
    )