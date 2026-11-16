
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# OPTIVIEW-RX
# Personalised Computational Vision Research Platform
# ============================================================

st.set_page_config(
    page_title="OptiView-Rx",
    page_icon="👁️",
    layout="wide"
)


# ============================================================
# 1. APPLICATION INTRODUCTION
# ============================================================

st.title("OptiView-Rx")

st.subheader("Personalised Computational Vision Research")

st.write(
    "An experimental platform exploring personalised vision "
    "assessment, digital reading accessibility and computational "
    "optical compensation."
)

st.info(
    "OptiView-Rx investigates whether personalised computational "
    "methods could eventually support digital reading for people "
    "with refractive errors. Its ability to provide spectacle-free "
    "reading has not yet been scientifically established."
)

st.divider()


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def spherical_equivalent(sphere, cylinder):
    return sphere + (cylinder / 2)


def calculate_contrast_ratio(background, foreground):

    def luminance(hex_color):

        hex_color = hex_color.lstrip("#")

        rgb = [
            int(hex_color[i:i + 2], 16) / 255
            for i in (0, 2, 4)
        ]

        corrected = []

        for value in rgb:

            if value <= 0.04045:
                corrected.append(value / 12.92)

            else:
                corrected.append(
                    ((value + 0.055) / 1.055) ** 2.4
                )

        return (
            0.2126 * corrected[0]
            + 0.7152 * corrected[1]
            + 0.0722 * corrected[2]
        )

    l1 = luminance(background)
    l2 = luminance(foreground)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)


# ============================================================
# 3. PERSONALised PRESCRIPTION PROFILE
# ============================================================

st.header("1. Personalised Prescription Profile")

st.write(
    "Enter the refractive prescription for the right and left eyes."
)

left_column, right_column = st.columns(2)

with left_column:

    st.subheader("Right Eye (OD)")

    od_sphere = st.number_input(
        "OD Sphere (D)",
        min_value=-20.0,
        max_value=20.0,
        value=0.0,
        step=0.25
    )

    od_cylinder = st.number_input(
        "OD Cylinder (D)",
        min_value=-10.0,
        max_value=10.0,
        value=0.0,
        step=0.25
    )

    od_axis = st.number_input(
        "OD Axis",
        min_value=0,
        max_value=180,
        value=0
    )

    od_add = st.number_input(
        "OD Add (D)",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.25
    )


with right_column:

    st.subheader("Left Eye (OS)")

    os_sphere = st.number_input(
        "OS Sphere (D)",
        min_value=-20.0,
        max_value=20.0,
        value=0.0,
        step=0.25
    )

    os_cylinder = st.number_input(
        "OS Cylinder (D)",
        min_value=-10.0,
        max_value=10.0,
        value=0.0,
        step=0.25
    )

    os_axis = st.number_input(
        "OS Axis",
        min_value=0,
        max_value=180,
        value=0
    )

    os_add = st.number_input(
        "OS Add (D)",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.25
    )


# ============================================================
# 4. PRESCRIPTION ANALYSIS
# ============================================================

st.divider()

st.header("2. Prescription Analysis")

od_se = spherical_equivalent(
    od_sphere,
    od_cylinder
)

os_se = spherical_equivalent(
    os_sphere,
    os_cylinder
)

anisometropia = abs(od_se - os_se)

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "Right Eye Spherical Equivalent",
    f"{od_se:.2f} D"
)

metric2.metric(
    "Left Eye Spherical Equivalent",
    f"{os_se:.2f} D"
)

metric3.metric(
    "Inter-eye Difference",
    f"{anisometropia:.2f} D"
)

st.subheader("Prescription Summary")

st.write(
    f"Right eye: Sphere {od_sphere:.2f} D, "
    f"Cylinder {od_cylinder:.2f} D, "
    f"Axis {od_axis}°, Add {od_add:.2f} D"
)

st.write(
    f"Left eye: Sphere {os_sphere:.2f} D, "
    f"Cylinder {os_cylinder:.2f} D, "
    f"Axis {os_axis}°, Add {os_add:.2f} D"
)

st.caption(
    "Spherical equivalent is a simplified calculation. "
    "It does not fully represent astigmatism, binocular vision "
    "or the complete optical state of either eye."
)


# ============================================================
# 5. DIGITAL READING ACCESSIBILITY
# ============================================================

st.divider()

st.header("3. Digital Reading Accessibility")

st.write(
    "Configure preferred reading conditions."
)

col1, col2 = st.columns(2)

with col1:

    font_size = st.slider(
        "Preferred Font Size",
        min_value=12,
        max_value=40,
        value=20
    )

    line_spacing = st.slider(
        "Preferred Line Spacing",
        min_value=1.0,
        max_value=3.0,
        value=1.5,
        step=0.1
    )

    reading_width = st.selectbox(
        "Reading Width",
        ["Narrow", "Medium", "Wide"]
    )


with col2:

    font_family = st.selectbox(
        "Preferred Font Family",
        ["Default", "Serif", "Sans Serif", "Monospace"]
    )

    letter_spacing = st.selectbox(
        "Letter Spacing",
        ["Normal", "Slightly Increased", "Increased"]
    )

    reading_theme = st.selectbox(
        "Reading Theme",
        ["Light", "Dark", "Warm"]
    )


# ============================================================
# 6. CONTRAST ACCESSIBILITY ANALYSIS
# ============================================================

st.divider()

st.header("4. Contrast Accessibility Analysis")

background_options = {
    "Light": "#FFFFFF",
    "Dark": "#121212",
    "Warm": "#F5EBD7"
}

text_options = {
    "Light": "#000000",
    "Dark": "#FFFFFF",
    "Warm": "#3B3025"
}

background_color = background_options[reading_theme]
text_color = text_options[reading_theme]

contrast_ratio = calculate_contrast_ratio(
    background_color,
    text_color
)

st.metric(
    "Calculated Contrast Ratio",
    f"{contrast_ratio:.2f}:1"
)

if contrast_ratio >= 7:

    st.success(
        "Meets WCAG AAA contrast threshold for normal text."
    )

elif contrast_ratio >= 4.5:

    st.info(
        "Meets WCAG AA contrast threshold for normal text."
    )

else:

    st.warning(
        "Does not meet WCAG AA contrast threshold for normal text."
    )

st.caption(
    "This evaluates the selected text and background colours. "
    "It does not establish overall visual accessibility."
)


# ============================================================
# 7. PERSONALISED READING ASSESSMENT
# ============================================================

st.divider()

st.header("5. Personalised Reading Assessment")

st.write(
    "Record the user's subjective reading experience under "
    "their selected digital reading conditions."
)

st.subheader("Reading Experience")

reading_comfort = st.slider(
    "How comfortable does reading feel?",
    min_value=1,
    max_value=10,
    value=5,
    help="1 = Very uncomfortable, 10 = Very comfortable"
)

letter_difficulty = st.slider(
    "Difficulty identifying letters",
    min_value=1,
    max_value=10,
    value=5,
    help="1 = No difficulty, 10 = Extreme difficulty"
)

small_text_difficulty = st.slider(
    "Difficulty reading small text",
    min_value=1,
    max_value=10,
    value=5,
    help="1 = No difficulty, 10 = Extreme difficulty"
)

eye_strain = st.slider(
    "Perceived eye strain",
    min_value=1,
    max_value=10,
    value=5,
    help="1 = No perceived strain, 10 = Severe perceived strain"
)

reading_distance = st.number_input(
    "Usual smartphone reading distance (cm)",
    min_value=10,
    max_value=100,
    value=35
)

reading_duration = st.number_input(
    "Typical continuous reading duration (minutes)",
    min_value=1,
    max_value=240,
    value=20
)

st.caption(
    "These are self-reported observations, not diagnostic "
    "measurements."
)


# ============================================================
# 8. VISUAL ACUITY AND READING PERFORMANCE
# ============================================================

st.divider()

st.header("6. Visual Acuity and Reading Performance")

st.write(
    "Record available visual acuity measurements and "
    "reading performance observations."
)

st.subheader("Visual Acuity")

st.caption(
    "Enter measurements only if obtained through an appropriate "
    "visual acuity assessment. Leave the fields empty if unknown."
)

acuity_options = [
    "Not measured",
    "6/6",
    "6/9",
    "6/12",
    "6/18",
    "6/24",
    "6/36",
    "6/60",
    "Other"
]

acuity_col1, acuity_col2 = st.columns(2)

with acuity_col1:

    od_acuity = st.selectbox(
        "Right Eye Visual Acuity",
        acuity_options
    )

with acuity_col2:

    os_acuity = st.selectbox(
        "Left Eye Visual Acuity",
        acuity_options
    )

st.subheader("Reading Performance")

reading_speed = st.number_input(
    "Reading Speed (words per minute)",
    min_value=0,
    max_value=2000,
    value=0,
    help="Enter 0 if not measured."
)

reading_errors = st.number_input(
    "Number of Reading Errors",
    min_value=0,
    max_value=1000,
    value=0
)

comprehension_score = st.slider(
    "Reading Comprehension Score (%)",
    min_value=0,
    max_value=100,
    value=0
)

st.caption(
    "Reading speed and comprehension should be measured using "
    "a consistent passage and testing procedure. A zero value "
    "means the measurement has not been entered."
)


# ============================================================
# 9. PERSONALISED VISION RESEARCH DASHBOARD
# ============================================================

st.divider()

st.header("7. Personalised Vision Research Dashboard")

st.write(
    "A consolidated overview of the entered prescription, "
    "reading preferences and reading performance observations."
)

st.subheader("Prescription Profile")

profile_col1, profile_col2 = st.columns(2)

with profile_col1:

    st.metric(
        "OD Spherical Equivalent",
        f"{od_se:.2f} D"
    )

    st.write(f"OD Visual Acuity: {od_acuity}")

with profile_col2:

    st.metric(
        "OS Spherical Equivalent",
        f"{os_se:.2f} D"
    )

    st.write(f"OS Visual Acuity: {os_acuity}")


st.subheader("Reading Preferences")

preference_data = {
    "Parameter": [
        "Font Size",
        "Font Family",
        "Line Spacing",
        "Letter Spacing",
        "Reading Width",
        "Reading Theme"
    ],
    "Selected Value": [
        f"{font_size}",
        font_family,
        f"{line_spacing}",
        letter_spacing,
        reading_width,
        reading_theme
    ]
}

st.dataframe(
    pd.DataFrame(preference_data),
    use_container_width=True,
    hide_index=True
)


st.subheader("Reading Experience")

experience_col1, experience_col2 = st.columns(2)

experience_col1.metric(
    "Reading Comfort",
    f"{reading_comfort}/10"
)

experience_col1.metric(
    "Letter Identification Difficulty",
    f"{letter_difficulty}/10"
)

experience_col2.metric(
    "Small Text Difficulty",
    f"{small_text_difficulty}/10"
)

experience_col2.metric(
    "Perceived Eye Strain",
    f"{eye_strain}/10"
)


st.subheader("Reading Performance")

performance_col1, performance_col2, performance_col3 = st.columns(3)

performance_col1.metric(
    "Reading Speed",
    f"{reading_speed} WPM"
)

performance_col2.metric(
    "Reading Errors",
    f"{reading_errors}"
)

performance_col3.metric(
    "Comprehension",
    f"{comprehension_score}%"
)


st.subheader("Reading Conditions")

st.write(
    f"Usual reading distance: {reading_distance} cm"
)

st.write(
    f"Continuous reading duration: {reading_duration} minutes"
)


# ============================================================
# 10. RESEARCH INTERPRETATION
# ============================================================

st.divider()

st.header("Research Observations")

st.write(
    "The dashboard brings together prescription parameters, "
    "digital reading preferences and self-reported reading "
    "experiences."
)

st.write(
    "These observations can help define future research "
    "questions about personalised digital reading and "
    "computational optical compensation."
)

st.warning(
    "The dashboard does not calculate a spectacle replacement "
    "prescription or establish clinical improvement. "
    "Comparisons require standardised measurements and "
    "appropriate scientific validation."
)


# ============================================================
# 11. RESEARCH ROADMAP
# ============================================================

st.divider()

st.header("Research Roadmap")

st.markdown(
    """
    1. Bilateral refractive prescription modelling.

    2. Personalised digital reading profiles.

    3. Reading accessibility assessment.

    4. Visual performance data collection.

    5. Individual reading experience analysis.

    6. Development of personalised computational optical models.

    7. Validation against appropriate optical and clinical
       reference measurements.
    """
)


# ============================================================
# 12. SCIENTIFIC LIMITATIONS
# ============================================================

st.divider()

st.header("Scientific Limitations")

st.markdown(
    """
    - Spherical equivalent does not fully represent refractive error.
    - Subjective reading comfort is not equivalent to visual acuity.
    - Reading speed depends on language, passage difficulty and
      testing conditions.
    - The current application does not model binocular vision.
    - No validated personalised optical correction is currently
      implemented.
    - The platform has not established spectacle-free reading.
    - It must not be used as a substitute for prescribed spectacles.
    """
)

st.info(
    "Human research requires appropriate institutional approval, "
    "ethical oversight and professional supervision."
)


# ============================================================
# 13. FOOTER
# ============================================================

st.divider()

st.caption(
    "OptiView-Rx | Personalised Computational Vision Research"
)

st.caption(
    "Experimental research prototype. "
    "Not intended for diagnosis or treatment."
)
