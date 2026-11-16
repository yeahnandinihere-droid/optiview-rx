
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================================
# OPTIVIEW-RX | RESEARCH PROTOTYPE V2.1
# Digital Accessibility + Exploratory Computational Optics
# ============================================================

st.set_page_config(
    page_title="OptiView-Rx | Research Prototype",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 1. APPLICATION CONFIGURATION
# ============================================================

st.title("👁️ OptiView-Rx")

st.caption(
    "A research prototype for personalised digital reading "
    "accessibility and exploratory optical image simulation."
)

st.info(
    "**Research Purpose and Future Vision**\n\n"
    "OptiView-Rx is an experimental research project investigating "
    "whether personalised computational optical compensation can "
    "enable people with refractive errors to read on conventional "
    "smartphones without wearing spectacles.\n\n"
    "The long-term objective is to develop a software-based solution "
    "that, if successfully developed and scientifically validated, "
    "could potentially reduce the need for spectacles specifically "
    "during everyday smartphone reading.\n\n"
    "This technology is currently under research and development. "
    "Its ability to provide effective spectacle-free reading has not "
    "yet been established."
)

# ============================================================
# 2. MATHEMATICAL FUNCTIONS
# ============================================================

def spherical_equivalent(sphere, cylinder):
    return sphere + cylinder / 2.0


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(
        int(hex_color[i:i + 2], 16)
        for i in (0, 2, 4)
    )


def linearize_channel(value):
    value = value / 255.0

    if value <= 0.04045:
        return value / 12.92

    return ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color):
    r, g, b = hex_to_rgb(hex_color)

    r = linearize_channel(r)
    g = linearize_channel(g)
    b = linearize_channel(b)

    return (
        0.2126 * r
        + 0.7152 * g
        + 0.0722 * b
    )


def contrast_ratio(foreground, background):
    lum1 = relative_luminance(foreground)
    lum2 = relative_luminance(background)

    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)


def contrast_status(ratio):
    if ratio >= 7.0:
        return "AAA for normal text"

    if ratio >= 4.5:
        return "AAA for large text only"

    return "Does not meet AAA text contrast"


# ============================================================
# 3. BILATERAL PRESCRIPTION INPUT
# ============================================================

st.sidebar.header("📋 Visual Profile")

st.sidebar.caption(
    "Optional prescription information for research analysis. "
    "Prescription values do not determine the reading settings."
)

st.sidebar.subheader("Right Eye (OD)")

od_col1, od_col2 = st.sidebar.columns(2)

with od_col1:
    od_sph = st.number_input(
        "OD Sphere (D)",
        -20.00, 20.00, -2.50,
        step=0.25,
        format="%.2f",
        key="od_sph"
    )

    od_cyl = st.number_input(
        "OD Cylinder (D)",
        -8.00, 8.00, -0.75,
        step=0.25,
        format="%.2f",
        key="od_cyl"
    )

with od_col2:
    od_axis = st.number_input(
        "OD Axis (°)",
        1, 180, 90,
        disabled=(abs(od_cyl) < 0.001),
        key="od_axis"
    )

    od_add = st.number_input(
        "OD Add (D)",
        0.00, 4.00, 0.00,
        step=0.25,
        format="%.2f",
        key="od_add"
    )

st.sidebar.markdown("---")
st.sidebar.subheader("Left Eye (OS)")

os_col1, os_col2 = st.sidebar.columns(2)

with os_col1:
    os_sph = st.number_input(
        "OS Sphere (D)",
        -20.00, 20.00, -3.00,
        step=0.25,
        format="%.2f",
        key="os_sph"
    )

    os_cyl = st.number_input(
        "OS Cylinder (D)",
        -8.00, 8.00, -1.25,
        step=0.25,
        format="%.2f",
        key="os_cyl"
    )

with os_col2:
    os_axis = st.number_input(
        "OS Axis (°)",
        1, 180, 95,
        disabled=(abs(os_cyl) < 0.001),
        key="os_axis"
    )

    os_add = st.number_input(
        "OS Add (D)",
        0.00, 4.00, 0.00,
        step=0.25,
        format="%.2f",
        key="os_add"
    )

st.sidebar.caption(
    "Enter values from a current, professionally verified "
    "prescription. Use the same cylinder notation as your prescription."
)

# ============================================================
# 4. PRESCRIPTION ANALYSIS
# ============================================================

od_se = spherical_equivalent(od_sph, od_cyl)
os_se = spherical_equivalent(os_sph, os_cyl)

anisometropia = abs(od_se - os_se)

st.header("1. Bilateral Prescription Analysis")

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "OD Spherical Equivalent",
    f"{od_se:+.2f} D"
)

metric2.metric(
    "OS Spherical Equivalent",
    f"{os_se:+.2f} D"
)

metric3.metric(
    "Spherical Equivalent Difference",
    f"{anisometropia:.2f} D"
)

with st.expander("View complete prescription details"):

    prescription_col1, prescription_col2 = st.columns(2)

    with prescription_col1:
        st.markdown("**Right eye — OD**")
        st.write(f"Sphere: {od_sph:+.2f} D")
        st.write(f"Cylinder: {od_cyl:+.2f} D")
        st.write(
            f"Axis: {od_axis}°"
            if abs(od_cyl) >= 0.001
            else "Axis: Not applicable"
        )
        st.write(f"Near addition: +{od_add:.2f} D")

    with prescription_col2:
        st.markdown("**Left eye — OS**")
        st.write(f"Sphere: {os_sph:+.2f} D")
        st.write(f"Cylinder: {os_cyl:+.2f} D")
        st.write(
            f"Axis: {os_axis}°"
            if abs(os_cyl) >= 0.001
            else "Axis: Not applicable"
        )
        st.write(f"Near addition: +{os_add:.2f} D")

st.caption(
    "Spherical equivalent is a descriptive summary. "
    "It does not represent complete optical correction."
)

# ============================================================
# 5. DIGITAL ACCESSIBILITY ENGINE
# ============================================================

st.markdown("---")
st.header("2. Digital Accessibility Engine")

st.write(
    "Explore reading preferences including typography, "
    "contrast, font size and reading presentation."
)

theme_options = {
    "Dark": {
        "background": "#161E2E",
        "text": "#F9FAFB",
        "accent": "#38BDF8"
    },
    "Light": {
        "background": "#F3F4F6",
        "text": "#111827",
        "accent": "#0369A1"
    },
    "Warm": {
        "background": "#FFF7E8",
        "text": "#292524",
        "accent": "#92400E"
    }
}

setting_col1, setting_col2 = st.columns(2)

with setting_col1:

    theme_name = st.selectbox(
        "Reading theme",
        list(theme_options.keys())
    )

    font_size = st.slider(
        "Font size (pixels)",
        14, 40, 20, 1
    )

    line_height = st.slider(
        "Line height preference",
        1.2, 2.2, 1.6, 0.1
    )

with setting_col2:

    font_family_name = st.selectbox(
        "Font family preference",
        ["Arial", "Verdana", "Georgia", "Trebuchet MS"]
    )

    letter_spacing = st.slider(
        "Letter spacing preference",
        0.0, 4.0, 0.5, 0.1
    )

    reading_width = st.slider(
        "Reading width preference (pixels)",
        400, 1000, 720, 20
    )

colors = theme_options[theme_name]

background_color = colors["background"]
text_color = colors["text"]
accent_color = colors["accent"]

st.caption(
    "These settings record individual reading preferences. "
    "The native Streamlit preview below does not apply custom "
    "font styling, letter spacing or background colours."
)

# ============================================================
# 6. WCAG CONTRAST CALCULATION
# ============================================================

st.markdown("---")
st.subheader("Accessibility Contrast Evaluation")

body_ratio = contrast_ratio(
    text_color,
    background_color
)

accent_ratio = contrast_ratio(
    accent_color,
    background_color
)

contrast_col1, contrast_col2 = st.columns(2)

with contrast_col1:

    st.metric(
        "Body text contrast",
        f"{body_ratio:.2f}:1"
    )

    st.write(contrast_status(body_ratio))

with contrast_col2:

    st.metric(
        "Accent text contrast",
        f"{accent_ratio:.2f}:1"
    )

    st.write(contrast_status(accent_ratio))

st.caption(
    "WCAG AAA thresholds: 7:1 for normal text and 4.5:1 "
    "for large text. These calculations evaluate selected "
    "colour pairs only; they do not certify the entire "
    "application as WCAG compliant."
)

# ============================================================
# 7. PERSONALISED READING PREVIEW
# ============================================================

st.markdown("---")
st.header("3. Personalised Reading Preview")

st.subheader("Digital Reading Sample")

reading_sample = (
    "Clear and comfortable digital reading depends on several "
    "factors, including typography, contrast, screen brightness, "
    "viewing distance, and individual visual preferences. "
    "Personalised reading settings can be explored and evaluated "
    "through structured reading assessments. Users should continue "
    "to follow their prescribed vision correction and professional "
    "eye-care advice."
)

st.write(reading_sample)

# ============================================================
# 8. EXPLORATORY IMAGE BLUR SANDBOX
# ============================================================

st.markdown("---")
st.header("4. Exploratory Image Processing Sandbox")

st.warning(
    "This is a generic Gaussian image-blur demonstration. "
    "It is NOT a myopia simulation, retinal image model, "
    "optical correction algorithm or clinical test. "
    "The blur parameter is manually selected and is not "
    "derived from the prescription."
)

blur_strength = st.slider(
    "Illustrative Gaussian blur strength",
    0.0, 8.0, 2.0, 0.25
)


def create_sample_image():

    image = Image.new(
        "RGB",
        (1100, 460),
        color="white"
    )

    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.text(
        (45, 45),
        "OPTIVIEW-RX | IMAGE PROCESSING DEMONSTRATION",
        fill="black",
        font=font
    )

    draw.line(
        (45, 85, 1050, 85),
        fill="gray",
        width=2
    )

    sample_lines = [
        "Digital displays produce images using patterns of light.",
        "Image processing can modify edges and spatial frequencies.",
        "Optical systems can affect how displayed images are perceived.",
        "Experimental modelling helps investigate these interactions.",
        "This demonstration uses generic Gaussian image degradation."
    ]

    y_position = 130

    for line in sample_lines:

        draw.text(
            (45, y_position),
            line,
            fill="black",
            font=font
        )

        y_position += 55

    return image


original_image = create_sample_image()

blurred_image = original_image.filter(
    ImageFilter.GaussianBlur(
        radius=blur_strength
    )
)

image_col1, image_col2 = st.columns(2)

with image_col1:

    st.markdown("**Original image**")

    st.image(
        original_image,
        use_container_width=True
    )

with image_col2:

    st.markdown("**Illustrative blurred image**")

    st.image(
        blurred_image,
        use_container_width=True
    )

st.caption(
    "This comparison demonstrates image degradation only. "
    "It does not demonstrate that pre-distortion can restore "
    "vision or compensate for an individual's refractive error."
)

# ============================================================
# 9. EXPLORATORY COMPUTATIONAL OPTICS ENGINE
# ============================================================

st.markdown("---")
st.header("5. Exploratory Computational Optics Engine")

st.warning(
    "Research simulation only. This is a simplified, "
    "monochromatic defocus/PSF model using an elliptical "
    "Gaussian approximation. It is not an individualized "
    "eye model, clinical retinal simulation, validated "
    "correction method, or evidence of spectacle-free reading."
)

try:

    from optics import (
        make_astigmatic_psf,
        apply_psf,
        regularized_preemphasis,
        mtf_curve,
        image_sharpness_score
    )

    st.write(
        "Select one eye and display assumptions. The model uses "
        "the two principal meridians represented by sphere and "
        "sphere plus cylinder. Prescription sign is reduced to "
        "blur magnitude in this exploratory model."
    )

    eye_choice = st.radio(
        "Eye to simulate",
        ["Right eye (OD)", "Left eye (OS)"],
        horizontal=True
    )

    if eye_choice == "Right eye (OD)":

        sim_sph = od_sph
        sim_cyl = od_cyl
        sim_axis = od_axis

    else:

        sim_sph = os_sph
        sim_cyl = os_cyl
        sim_axis = os_axis

    sim_col1, sim_col2, sim_col3 = st.columns(3)

    with sim_col1:

        pupil_mm = st.slider(
            "Assumed pupil diameter (mm)",
            1.5, 6.0, 3.0, 0.1
        )

    with sim_col2:

        viewing_mm = st.slider(
            "Viewing distance (mm)",
            200, 700, 400, 10
        )

    with sim_col3:

        pixel_pitch_um = st.slider(
            "Display pixel pitch (µm)",
            35, 120, 55, 1
        )

    psf, psf_info = make_astigmatic_psf(
        sim_sph,
        sim_cyl,
        sim_axis,
        pupil_diameter_mm=pupil_mm,
        viewing_distance_mm=viewing_mm,
        pixel_pitch_um=pixel_pitch_um
    )

    sample = create_sample_image().convert("L")

    sample_array = np.asarray(
        sample,
        dtype=np.uint8
    )

    simulated_blur = apply_psf(
        sample_array,
        psf
    )

    st.subheader("A. Simplified Point Spread Function (PSF)")

    psf_col, info_col = st.columns([1, 2])

    with psf_col:

        st.image(
            psf,
            caption="Normalised model PSF",
            clamp=True,
            use_container_width=True
        )

    with info_col:

        st.write(
            f"Parallel-meridian blur sigma: "
            f"**{psf_info['sigma_parallel_px']:.2f} pixels**"
        )

        st.write(
            f"Perpendicular-meridian blur sigma: "
            f"**{psf_info['sigma_perpendicular_px']:.2f} pixels**"
        )

        st.write(
            f"Principal meridional defocus magnitudes: "
            f"**{psf_info['meridional_defocus_d'][0]:.2f} D** "
            f"and **{psf_info['meridional_defocus_d'][1]:.2f} D**"
        )

        st.caption(
            "The prescription axis sets the orientation "
            "of the simplified elliptical kernel."
        )

    st.subheader("B. Simulated Retinal-Image Proxy")

    st.caption(
        "This is a display-image convolution proxy, "
        "not a prediction of an actual person's retinal image."
    )

    image_a, image_b = st.columns(2)

    with image_a:

        st.image(
            sample_array,
            caption="Input sample",
            use_container_width=True
        )

    with image_b:

        st.image(
            simulated_blur,
            caption="After model PSF convolution",
            use_container_width=True
        )

    st.subheader("C. Experimental Pre-emphasis")

    st.caption(
        "The filter is applied to the input image, then the "
        "same model PSF is applied to that pre-emphasised image. "
        "This is a numerical experiment only."
    )

    regularization = st.slider(
        "Inverse-filter regularisation",
        0.001, 0.20, 0.02, 0.001,
        format="%.3f"
    )

    preemphasis_enabled = st.checkbox(
        "Run regularised pre-emphasis experiment",
        value=False
    )

    if preemphasis_enabled:

        preemphasised = regularized_preemphasis(
            sample_array,
            psf,
            regularization
        )

        preemphasis_after_blur = apply_psf(
            preemphasised,
            psf
        )

        pre_col1, pre_col2 = st.columns(2)

        with pre_col1:

            st.image(
                preemphasised,
                caption="Pre-emphasised input",
                use_container_width=True
            )

        with pre_col2:

            st.image(
                preemphasis_after_blur,
                caption="Pre-emphasised input after model blur",
                use_container_width=True
            )

        base_score = image_sharpness_score(
            simulated_blur
        )

        experimental_score = image_sharpness_score(
            preemphasis_after_blur
        )

        st.write(
            f"Blurred baseline sharpness proxy: **{base_score:.2f}**"
        )

        st.write(
            f"Pre-emphasis result sharpness proxy: "
            f"**{experimental_score:.2f}**"
        )

        st.caption(
            "A higher sharpness proxy is not proof of better "
            "legibility or improved human vision. Ringing and "
            "noise amplification can increase this score."
        )

    st.subheader("D. Modulation Transfer Function (MTF) Estimate")

    frequencies, mtf_values = mtf_curve(psf)

    fig, ax = plt.subplots()

    ax.plot(
        frequencies,
        mtf_values
    )

    ax.set_xlabel("Spatial frequency (cycles/pixel)")
    ax.set_ylabel("MTF")
    ax.set_ylim(0, 1.05)
    ax.set_title("Radially averaged MTF of model PSF")
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

    plt.close(fig)

    st.info(
        "Interpretation boundary: this engine explores how "
        "assumed defocus parameters affect a simplified image "
        "model. It does not establish that an ordinary smartphone "
        "can overcome refractive error. The next research step is "
        "validation against an established optical model and "
        "measured optical or visual data."
    )

except ImportError as error:

    st.error(
        "The computational optics module or one of its "
        "dependencies is missing. Install the packages "
        "listed in requirements.txt. "
        f"Technical detail: {error}"
    )

except Exception as error:

    st.error(
        f"The exploratory optics simulation could not run: {error}"
    )

# ============================================================
# 10. RESEARCH NOTES AND NEXT EXPERIMENTS
# ============================================================

st.markdown("---")
st.header("6. Computational Optics Research Roadmap")

research_topics = [
    "Validate simplified PSF model against an established optical model",
    "Compare directional MTF for astigmatic blur",
    "Add wavefront aberration modelling with appropriate optical data",
    "Evaluate pre-emphasis stability, ringing and noise amplification",
    "Compare model outputs with measured optical bench data",
    "Investigate conventional-display physical feasibility",
    "Obtain optometry, ophthalmology and optical engineering review"
]

for index, topic in enumerate(research_topics):

    st.checkbox(
        topic,
        key=f"research_{index}"
    )

# ============================================================
# 11. SCIENTIFIC LIMITATIONS
# ============================================================

st.markdown("---")
st.header("7. Scientific Limitations")

st.markdown("""
This prototype currently:

- Collects bilateral spectacle prescription parameters.
- Calculates spherical equivalent for descriptive reporting.
- Allows users to select digital reading preferences.
- Calculates contrast ratios for selected colour combinations.
- Demonstrates generic Gaussian image degradation.
- Explores simplified computational PSF and MTF models.
- Includes an experimental regularised pre-emphasis operation.

It does NOT currently:

- Simulate an individual's complete optical system.
- Calculate actual retinal image formation.
- Model an individual's measured point spread function.
- Perform wavefront-based optical correction.
- Implement a validated personalised optical pre-distortion method.
- Correct myopia, hyperopia, astigmatism or presbyopia.
- Replace spectacles or contact lenses.
- Demonstrate improved visual acuity in human participants.
""")

st.info(
    "Future optical modelling must be based on explicit physical "
    "assumptions, validated mathematical models and reproducible "
    "experimental comparisons. Human testing requires appropriate
    "professional oversight and research ethics approval."
)

# ============================================================
# 12. FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "OptiView-Rx | Research Prototype v2.1 | "
    "Digital Accessibility and Exploratory Computational Optics"
)
