
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageFilter


# ============================================================
# OPTIVIEW-RX
# Personalised Computational Vision Research
# ============================================================

st.set_page_config(
    page_title="OptiView-Rx",
    page_icon="👁️",
    layout="wide"
)


# ============================================================
# 1. INTRODUCTION
# ============================================================

st.title("OptiView-Rx")

st.subheader("Personalised Computational Vision Research")

st.write(
    "An experimental platform exploring personalised "
    "computational optical compensation and digital reading accessibility."
)

st.info(
    "OptiView-Rx investigates whether personalised computational "
    "optical compensation could eventually support reading on "
    "conventional smartphones without spectacles. This capability "
    "has not yet been scientifically established."
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


def create_gaussian_psf(size=31, sigma=2.0):

    coordinates = np.arange(size) - size // 2
    x, y = np.meshgrid(coordinates, coordinates)

    psf = np.exp(
        -(x**2 + y**2) / (2 * sigma**2)
    )

    return psf / np.sum(psf)


def apply_frequency_filter(image_array, psf):

    image_array = image_array.astype(float) / 255.0

    height, width = image_array.shape

    padded_psf = np.zeros((height, width))

    ph, pw = psf.shape

    padded_psf[:ph, :pw] = psf

    padded_psf = np.roll(
        padded_psf,
        (-(ph // 2), -(pw // 2)),
        axis=(0, 1)
    )

    image_fft = np.fft.fft2(image_array)
    psf_fft = np.fft.fft2(padded_psf)

    blurred = np.real(
        np.fft.ifft2(image_fft * psf_fft)
    )

    blurred = np.clip(blurred, 0, 1)

    return (blurred * 255).astype(np.uint8)


def apply_experimental_preemphasis(
    image_array,
    psf,
    regularization=0.02
):

    image_array = image_array.astype(float) / 255.0

    height, width = image_array.shape

    padded_psf = np.zeros((height, width))

    ph, pw = psf.shape

    padded_psf[:ph, :pw] = psf

    padded_psf = np.roll(
        padded_psf,
        (-(ph // 2), -(pw // 2)),
        axis=(0, 1)
    )

    image_fft = np.fft.fft2(image_array)
    psf_fft = np.fft.fft2(padded_psf)

    inverse_filter = (
        np.conj(psf_fft)
        / (np.abs(psf_fft) ** 2 + regularization)
    )

    corrected = np.real(
        np.fft.ifft2(image_fft * inverse_filter)
    )

    corrected = np.clip(corrected, 0, 1)

    return (corrected * 255).astype(np.uint8)


def calculate_mtf(psf):

    optical_transfer = np.fft.fft2(psf)

    optical_transfer = np.fft.fftshift(
        optical_transfer
    )

    mtf = np.abs(optical_transfer)

    if np.max(mtf) > 0:
        mtf = mtf / np.max(mtf)

    return mtf


def calculate_sharpness(image_array):

    image_array = image_array.astype(float)

    laplacian = (
        -4 * image_array
        + np.roll(image_array, 1, axis=0)
        + np.roll(image_array, -1, axis=0)
        + np.roll(image_array, 1, axis=1)
        + np.roll(image_array, -1, axis=1)
    )

    return float(np.var(laplacian))


# ============================================================
# 3. PERSONALised PRESCRIPTION PROFILE
# ============================================================

st.header("1. Personalised Prescription Profile")

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
    f"OD: Sphere {od_sphere:.2f} D | "
    f"Cylinder {od_cylinder:.2f} D | "
    f"Axis {od_axis}° | Add {od_add:.2f} D"
)

st.write(
    f"OS: Sphere {os_sphere:.2f} D | "
    f"Cylinder {os_cylinder:.2f} D | "
    f"Axis {os_axis}° | Add {os_add:.2f} D"
)

st.caption(
    "Spherical equivalent is a simplified prescription calculation."
)


# ============================================================
# 5. DIGITAL READING ACCESSIBILITY
# ============================================================

st.divider()

st.header("3. Digital Reading Accessibility")

col1, col2 = st.columns(2)

with col1:

    font_size = st.slider(
        "Preferred Font Size",
        12, 40, 20
    )

    line_spacing = st.slider(
        "Preferred Line Spacing",
        1.0, 3.0, 1.5, 0.1
    )

    reading_width = st.selectbox(
        "Reading Width",
        ["Narrow", "Medium", "Wide"]
    )


with col2:

    font_family = st.selectbox(
        "Font Family",
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


# ============================================================
# 7. PERSONALISED READING PREVIEW
# ============================================================

st.divider()

st.header("5. Personalised Reading Preview")

st.write(
    "Explore a reading sample and review your selected "
    "reading preferences."
)

reading_sample = """
Digital reading is an important part of everyday life.

People use smartphones to read messages, articles, books,
educational materials and medical information.

OptiView-Rx explores whether personalised computational
methods could improve digital reading experiences.
"""

st.subheader("Digital Reading Sample")

st.write(reading_sample)

st.caption(
    f"Font size: {font_size} | "
    f"Font family: {font_family} | "
    f"Line spacing: {line_spacing} | "
    f"Letter spacing: {letter_spacing} | "
    f"Reading width: {reading_width} | "
    f"Theme: {reading_theme}"
)


# ============================================================
# 8. VISUAL BLUR SIMULATION
# ============================================================

st.divider()

st.header("6. Visual Blur Simulation")

st.write(
    "Explore how different levels of blur affect visual information."
)

sample_text = st.text_input(
    "Enter text for the visual simulation",
    value="OptiView-Rx Digital Reading"
)

blur_amount = st.slider(
    "Blur Intensity",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.5
)

if sample_text.strip():

    from PIL import ImageDraw, ImageFont

    simulation_image = Image.new(
        "RGB",
        (700, 160),
        "white"
    )

    draw = ImageDraw.Draw(simulation_image)

    draw.text(
        (25, 55),
        sample_text,
        fill="black"
    )

    blurred_image = simulation_image.filter(
        ImageFilter.GaussianBlur(radius=blur_amount)
    )

    image_col1, image_col2 = st.columns(2)

    with image_col1:

        st.subheader("Original")

        st.image(
            simulation_image,
            use_container_width=True
        )

    with image_col2:

        st.subheader("Blurred")

        st.image(
            blurred_image,
            use_container_width=True
        )


# ============================================================
# 9. COMPUTATIONAL OPTICS ENGINE
# ============================================================

st.divider()

st.header("7. Computational Optics Engine")

st.write(
    "Explore simplified optical image degradation and "
    "experimental computational pre-emphasis."
)

st.caption(
    "This is a general image-processing demonstration, "
    "not a personalised optical correction."
)

sample_options = [
    "OptiView-Rx",
    "Digital Vision Research",
    "Personalised Reading"
]

optics_text = st.selectbox(
    "Select a sample",
    sample_options,
    key="optics_text"
)

optics_blur = st.slider(
    "Optical Blur Sigma",
    min_value=0.5,
    max_value=8.0,
    value=2.0,
    step=0.5
)

regularization = st.slider(
    "Pre-emphasis Regularization",
    min_value=0.001,
    max_value=0.2,
    value=0.02,
    step=0.001,
    format="%.3f"
)

# Create text image

from PIL import ImageDraw, ImageFont

optics_image = Image.new(
    "L",
    (512, 160),
    255
)

draw = ImageDraw.Draw(optics_image)

draw.text(
    (20, 55),
    optics_text,
    fill=0
)

image_array = np.array(optics_image)

# Create PSF

psf = create_gaussian_psf(
    size=31,
    sigma=optics_blur
)

# Simulated blur

degraded_image = apply_frequency_filter(
    image_array,
    psf
)

# Experimental pre-emphasis

experimental_image = apply_experimental_preemphasis(
    degraded_image,
    psf,
    regularization
)

result_col1, result_col2, result_col3 = st.columns(3)

with result_col1:

    st.subheader("Original")

    st.image(
        image_array,
        use_container_width=True
    )

with result_col2:

    st.subheader("Simulated Blur")

    st.image(
        degraded_image,
        use_container_width=True
    )

with result_col3:

    st.subheader("Experimental Output")

    st.image(
        experimental_image,
        use_container_width=True
    )


# Sharpness comparison

st.subheader("Image Sharpness Comparison")

original_sharpness = calculate_sharpness(image_array)

blurred_sharpness = calculate_sharpness(degraded_image)

corrected_sharpness = calculate_sharpness(experimental_image)

sharp_col1, sharp_col2, sharp_col3 = st.columns(3)

sharp_col1.metric(
    "Original",
    f"{original_sharpness:.2f}"
)

sharp_col2.metric(
    "Blurred",
    f"{blurred_sharpness:.2f}"
)

sharp_col3.metric(
    "Experimental Output",
    f"{corrected_sharpness:.2f}"
)


# PSF visualisation

st.subheader("Point Spread Function (PSF)")

fig_psf, ax_psf = plt.subplots()

ax_psf.imshow(
    psf,
    cmap="viridis"
)

ax_psf.set_title("Gaussian PSF")

ax_psf.set_xlabel("X")
ax_psf.set_ylabel("Y")

st.pyplot(fig_psf)

plt.close(fig_psf)


# MTF visualisation

st.subheader("Modulation Transfer Function (MTF)")

mtf = calculate_mtf(psf)

fig_mtf, ax_mtf = plt.subplots()

ax_mtf.plot(
    mtf[mtf.shape[0] // 2, :]
)

ax_mtf.set_title("Simplified MTF")

ax_mtf.set_xlabel("Spatial Frequency Position")
ax_mtf.set_ylabel("Normalised MTF")

ax_mtf.grid(True)

st.pyplot(fig_mtf)

plt.close(fig_mtf)


# ============================================================
# 10. RESEARCH ROADMAP
# ============================================================

st.divider()

st.header("Research Roadmap")

st.markdown(
    """
    1. Personalised refractive prescription modelling.

    2. Bilateral optical parameter analysis.

    3. Digital reading accessibility.

    4. Simplified optical modelling.

    5. Computational image processing.

    6. Experimental pre-emphasis development.

    7. Future scientific and clinical validation.
    """
)


# ============================================================
# 11. RESEARCH INFORMATION
# ============================================================

st.divider()

st.header("About the Research")

st.write(
    "OptiView-Rx brings together refractive prescription "
    "information, reading preferences and computational "
    "vision experiments in one platform."
)

st.write(
    "The long-term research direction is to investigate "
    "whether personalised computational methods can improve "
    "digital reading for people with refractive errors."
)

st.caption(
    "Experimental research prototype. Not intended for diagnosis "
    "or as a replacement for prescribed spectacles."
)


# ============================================================
# 12. FOOTER
# ============================================================

st.divider()

st.caption(
    "OptiView-Rx | Personalised Computational Vision Research"
)
