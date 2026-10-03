import streamlit as st

def compute_typography_styles(sphere: float, cylinder: float, axis: int, reading_add: float = 0.0) -> dict:
    spherical_equivalent = sphere + (cylinder / 2.0)
    
    base_font_size = 16.0
    base_line_height = 1.5
    
    near_scale = max(0.0, reading_add) * 0.25
    myopic_blur_scale = max(0.0, abs(sphere)) * 0.12 if sphere < -1.5 else 0.0
    total_scale = 1.0 + near_scale + myopic_blur_scale
    final_font_size = round(base_font_size * total_scale, 1)
    
    abs_cyl = abs(cylinder)
    if abs_cyl >= 2.0:
        font_weight = 700
        letter_spacing = 1.2
        theme = "ultra_high_contrast"
    elif abs_cyl >= 0.75:
        font_weight = 600
        letter_spacing = 0.6
        theme = "high_contrast"
    else:
        font_weight = 400
        letter_spacing = 0.0
        theme = "standard"
        
    final_line_height = round(base_line_height + (reading_add * 0.1), 2)
    
    return {
        "spherical_equivalent": round(spherical_equivalent, 2),
        "font_size_px": f"{final_font_size}px",
        "font_weight": font_weight,
        "line_height": final_line_height,
        "letter_spacing_px": f"{letter_spacing}px",
        "theme": theme
    }

st.set_page_config(
    page_title="OptiScale | Optical Accessibility",
    page_icon="👁️",
    layout="wide"
)

st.title("👁️ OptiScale: Prescriptive Visual Accessibility Engine")
st.caption("Translates refractive spectacle prescriptions (Sphere, Cylinder, Axis, Add) into real-time responsive digital typography.")

st.divider()

col_input, col_preview = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("1. Spectacle Prescription (Rx)")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        sph = st.number_input("Sphere (SPH)", min_value=-15.0, max_value=+10.0, value=+1.50, step=0.25)
    with c2:
        cyl = st.number_input("Cylinder (CYL)", min_value=-8.0, max_value=0.0, value=-1.25, step=0.25)
    with c3:
        axis = st.number_input("Axis (°)", min_value=1, max_value=180, value=90, step=1)
        
    add_power = st.number_input("Near Reading Add (ADD)", min_value=0.0, max_value=+4.0, value=+2.00, step=0.25)
    
    result = compute_typography_styles(sph, cyl, axis, add_power)
    
    st.markdown("#### Clinical Optical Summary")
    st.metric("Spherical Equivalent (SE)", f"{result['spherical_equivalent']:+.2f} D")

with col_preview:
    st.subheader("2. Calibrated Eye Care Typography")
    
    theme = result["theme"]
    if theme == "ultra_high_contrast":
        bg, txt, bdr = "#000000", "#FFD700", "#FFD700"
    elif theme == "high_contrast":
        bg, txt, bdr = "#0F172A", "#F8FAFC", "#38BDF8"
    else:
        bg, txt, bdr = "#F8FAFC", "#0F172A", "#CBD5E1"

    style_block = (
        f"background-color:{bg}; color:{txt}; padding:24px; border-radius:12px; "
        f"border:2px solid {bdr}; font-size:{result['font_size_px']}; "
        f"font-weight:{result['font_weight']}; line-height:{result['line_height']}; "
        f"letter-spacing:{result['letter_spacing_px']}; font-family:system-ui, sans-serif;"
    )

    preview_html = (
        f'st.markdown(preview_html, unsafe_allow_html=True)

st.markdown("#### Dynamic CSS Output")
st.code(
    f"font-size: {result['font_size_px']};\n"
    f"font-weight: {result['font_weight']};\n"
    f"line-height: {result['line_height']};\n"
    f"letter-spacing: {result['letter_spacing_px']};\n"
    f"theme: {result['theme']};",
    language="css"
)