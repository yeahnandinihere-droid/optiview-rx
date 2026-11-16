
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from PIL import Image, ImageFilter, ImageOps


# ============================================================
# OPTIVIEW-RX
# Experimental Computational Vision Research Platform
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
    "An experimental research platform exploring personalised "
    "computational optical compensation and digital reading accessibility."
)

st.info(
    "OptiView-Rx is an experimental research project investigating "
    "whether personalised computational optical compensation could "
    "eventually support reading on conventional smartphones without "
    "spectacles. This capability has not yet been scientifically established."
)

st.divider()


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def spherical_equivalent(sphere, cylinder):
    """Calculate spherical equivalent."""
    return sphere + (cylinder / 2)


def calculate_anisometropia(od, os):
    """Calculate the difference between two spherical equivalents."""
    return abs(od - os)


def calculate_contrast_ratio(background, foreground):
    """Calculate WCAG contrast ratio."""

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
    """Create a simplified Gaussian point spread function."""

    coordinates = np.arange(size) - size // 2
    x, y = np.meshgrid(coordinates, coordinates)

    psf = np.exp(
        -(x**2 + y**2) / (2 * sigma**2)
    )

    psf = psf / np.sum(psf)

    return psf


def apply_frequency_filter(image_array, psf):
    """Apply a simplified frequency-domain blur model."""

    image_array = image_array.astype(float) / 255.0

    height, width = image_array.shape

    padded_psf = np.zeros((height, width))

    ph, pw = psf.shape

    padded_psf[:ph, :pw] = psf

    padded_psf = np.roll(
        padded_psf,
        (-ph // 2, -pw // 2),
        axis=(0, 1)
    )

    image_fft = np.fft.fft2(image_array)
    psf_fft = np.fft.fft2(padded_psf)

    blurred_fft = image_fft * psf_fft

    blurred = np.real(
        np.fft.ifft2(blurred_fft)
    )

    blurred = np.clip(blurred, 0, 1)

    return (blurred * 255).astype(np.uint8)


def apply_experimental_preemphasis(image_array, psf, regularization=0.02):
    """
    Experimental regularised frequency-domain pre-emphasis.

    This is a simplified computational model, not a validated
    optical correction algorithm.
    """

    image_array = image_array.astype(float) / 255.0

    height, width = image_array.shape

    padded_psf = np.zeros((height, width))

    ph, pw = psf.shape

    padded_psf[:ph, :pw] = psf

    padded_psf = np.roll(
        padded_psf,
        (-ph // 2, -pw // 2),
        axis=(0, 1)
    )

    image_fft = np.fft.fft2(image_array)
    psf_fft = np.fft.fft2(padded_psf)

    inverse_filter = (
        np.conj(psf_fft)
        / (np.abs(psf_fft) ** 2 + regularization)
    )

    corrected_fft = image_fft * inverse_filter

    corrected = np.real(
        np.fft.ifft2(corrected_fft)
    )

    corrected = np.clip(corrected, 0, 1)

    return (corrected * 255).astype(np.uint8)


def calculate_mtf(psf):
    """Calculate a simplified modulation transfer function."""

    optical_transfer = np.fft.fft2(psf)

    optical_transfer = np.fft.fftshift(
        optical_transfer
    )

    mtf = np.abs(optical_transfer)

    if np.max(mtf) > 0:
        mtf = mtf / np.max(mtf)

    return mtf


def calculate_sharpness(image_array):
    """Calculate a simple image sharpness proxy."""

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
# 3. BILATERAL PRESCRIPTION INPUT
# ============================================================

st.header("1. Personalised Prescription Profile")

st.write(
    "Enter the refractive prescription for each eye."
)

left_column, right_column = st.columns(2)

with left_column:

    st.subheader("Right Eye (OD)")

    od_sphere = st.number_input(
        "OD Sphere (D)",
        min_value=-20.0,
        max_value=20.0,
        value=0.0,
        step=0.25,
        key="od_sphere"
    )

    od_cylinder = st.number_input(
        "OD Cylinder (D)",
        min_value=-10.0,
        max_value=10.0,
        value=0.0,
        step=0.25,
        key="od_cylinder"
    )

    od_axis = st.number_input(
        "OD Axis",
        min_value=0,
        max_value=180,
        value=0,
        step=1,
        key="od_axis"
    )

    od_add = st.number_input(
        "OD Add (D)",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.25,
        key="od_add"
    )


with right_column:

    st.subheader("Left Eye (OS)")

    os_sphere = st.number_input(
        "OS Sphere (D)",
        min_value=-20.0,
        max_value=20.0,
        value=0.0,
        step=0.25,
        key="os_sphere"
    )

    os_cylinder = st.number_input(
        "OS Cylinder (D)",
        min_value=-10.0,
        max_value=10.0,
        value=0.0,
        step=0.25,
        key="os_cylinder"
    )

    os_axis = st.number_input(
        "OS Axis",
        min_value=0,
        max_value=180,
        value=0,
        step=1,
        key="os_axis"
    )

    os_add = st.number_input(
        "OS Add (D)",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.25,
        key="os_add"
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

anisometropia = calculate_anisometropia(
    od_se,
    os_se
)

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

st.write("**Prescription interpretation**")

if anisometropia >= 2.0:
    st.warning(
        "The calculated inter-eye spherical equivalent difference "
        "is 2.00 D or greater. This is a screening observation, "
        "not a clinical diagnosis."
    )
else:
    st.success(
        "The calculated inter-eye spherical equivalent difference "
        "is below 2.00 D."
    )

st.caption(
    "Spherical equivalent is a simplified summary. It does not "
    "fully represent astigmatism, axis, accommodation, binocular "
    "vision or the complete optical state of either eye."
)


# ============================================================
# 5. READING ACCESSIBILITY SETTINGS
# ============================================================

st.divider()

st.header("3. Digital Reading Accessibility")

st.write(
    "Explore reading preferences and their potential role "
    "in improving digital reading comfort."
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

    reading_width = st.select_slider(
        "Reading Width",
        options=["Narrow", "Medium", "Wide"],
        value="Medium"
    )

with col2:

    font_family = st.selectbox(
        "Preferred Font Family",
        [
            "Default",
            "Serif",
            "Sans Serif",
            "Monospace"
        ]
    )

    letter_spacing = st.select_slider(
        "Preferred Letter Spacing",
        options=[
            "Normal",
            "Slightly Increased",
            "Increased"
        ],
        value="Normal"
    )

    reading_theme = st.selectbox(
        "Reading Theme",
        [
            "Light",
            "Dark",
            "Warm"
        ]
    )


# ============================================================
# 6. CONTRAST ANALYSIS
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
        "The selected combination meets the WCAG AAA "
        "contrast threshold for normal text."
    )

elif contrast_ratio >= 4.5:
    st.info(
        "The selected combination meets the WCAG AA "
        "contrast threshold for normal text."
    )

else:
    st.warning(
        "The selected combination does not meet the "
        "WCAG AA contrast threshold for normal text."
    )

st.caption(
    "Contrast compliance is calculated for the selected "
    "foreground and background colours. It does not establish "
    "overall accessibility or visual comfort."
)


# ============================================================
# 7. NATIVE READING PREVIEW
# ============================================================

st.divider()

st.header("5. Personalised Reading Preview")

st.write(
    "This is a native Streamlit text preview. The selected "
    "typography and theme preferences are recorded above, "
    "but native text rendering does not apply all those "
    "custom visual settings."
)

reading_sample = """
Digital reading is an important part of everyday life.

People use smartphones to read messages, articles, books,
educational materials and medical information.

OptiView-Rx explores whether personalised computational
methods could eventually improve the digital reading
experience for people with refractive errors.
"""

st.subheader("Digital Reading Sample")

st.write(reading_sample)

st.caption(
    f"Selected font size: {font_size} | "
    f"Line spacing preference: {line_spacing} | "
    f"Font family preference: {font_family} | "
    f"Letter spacing preference: {letter_spacing} | "
    f"Reading width: {reading_width} | "
    f"Theme preference: {reading_theme}"
)


# ============================================================
# 8. IMAGE BLUR SANDBOX
# ============================================================

st.divider()

st.header("6. Visual Blur Simulation")

st.write(
    "Upload an image to explore the effect of simplified "
    "image blur on digital visual information."
)

uploaded_image = st.file_uploader(
    "Upload an image",
    type=["png", "jpg", "jpeg"]
)

if uploaded_image is not None:

    original_image = Image.open(
        uploaded_image
    ).convert("RGB")

    blur_amount = st.slider(
        "Blur Intensity",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.5
    )

    blurred_image = original_image.filter(
        ImageFilter.GaussianBlur(
            radius=blur_amount
        )
    )

    image_col1, image_col2 = st.columns(2)

    with image_col1:
        st.subheader("Original Image")
        st.image(
            original_image,
            use_container_width=True
        )

    with image_col2:
        st.subheader("Blurred Image")
        st.image(
            blurred_image,
            use_container_width=True
        )

    st.caption(
        "This is a generic image blur demonstration. "
        "It does not reproduce an individual's actual retinal "
        "image or optical aberrations."
    )

else:

    st.info(
        "Upload an image to start the visual blur simulation."
    )


# ============================================================
# 9. COMPUTATIONAL OPTICS EXPERIMENT
# ============================================================

st.divider()

st.header("7. Experimental Computational Optics Engine")

st.write(
    "Explore a simplified point spread function, image "
    "degradation and experimental frequency-domain "
    "pre-emphasis."
)

st.warning(
    "The following model is experimental. A Gaussian point "
    "spread function is not a complete representation of "
    "real human ocular optics."
)

optics_image = st.file_uploader(
    "Upload an image for computational optics",
    type=["png", "jpg", "jpeg"],
    key="optics_upload"
)

if optics_image is not None:

    input_image = Image.open(
        optics_image
    ).convert("L")

    input_image = ImageOps.contain(
        input_image,
        (512, 512)
    )

    image_array = np.array(input_image)

    st.subheader("Optical Model Parameters")

    sigma = st.slider(
        "Gaussian PSF Sigma",
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

    psf = create_gaussian_psf(
        size=31,
        sigma=sigma
    )

    degraded_image = apply_frequency_filter(
        image_array,
        psf
    )

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

        st.subheader("Experimental Pre-emphasis")

        st.image(
            experimental_image,
            use_container_width=True
        )

    # Sharpness comparison

    original_sharpness = calculate_sharpness(
        image_array
    )

    degraded_sharpness = calculate_sharpness(
        degraded_image
    )

    experimental_sharpness = calculate_sharpness(
        experimental_image
    )

    st.subheader("Sharpness Proxy Comparison")

    sharp_col1, sharp_col2, sharp_col3 = st.columns(3)

    sharp_col1.metric(
        "Original",
        f"{original_sharpness:.2f}"
    )

    sharp_col2.metric(
        "Simulated Blur",
        f"{degraded_sharpness:.2f}"
    )

    sharp_col3.metric(
        "Experimental Output",
        f"{experimental_sharpness:.2f}"
    )

    st.caption(
        "Sharpness variance is a computational image metric. "
        "An increase does not necessarily mean improved visual "
        "acuity, reading performance or clinical benefit."
    )

    # PSF visualisation

    st.subheader("Point Spread Function")

    fig_psf, ax_psf = plt.subplots()

    ax_psf.imshow(
        psf,
        cmap="viridis"
    )

    ax_psf.set_title(
        "Simplified Gaussian PSF"
    )

    ax_psf.set_xlabel("X")
    ax_psf.set_ylabel("Y")

    st.pyplot(fig_psf)

    plt.close(fig_psf)

    # MTF visualisation

    st.subheader("Modulation Transfer Function")

    mtf = calculate_mtf(psf)

    fig_mtf, ax_mtf = plt.subplots()

    ax_mtf.plot(
        mtf[mtf.shape[0] // 2, :]
    )

    ax_mtf.set_title(
        "Simplified MTF"
    )

    ax_mtf.set_xlabel("Spatial Frequency Position")
    ax_mtf.set_ylabel("Normalised MTF")

    ax_mtf.grid(True)

    st.pyplot(fig_mtf)

    plt.close(fig_mtf)

else:

    st.info(
        "Upload an image to explore the computational optics engine."
    )


# ============================================================
# 10. RESEARCH ROADMAP
# ============================================================

st.divider()

st.header("8. Research Roadmap")

st.write("**Current research directions**")

st.markdown(
    """
    1. Personalised refractive prescription modelling.

    2. Bilateral optical parameter analysis.

    3. Digital reading accessibility evaluation.

    4. Simplified point spread function modelling.

    5. Frequency-domain image processing.

    6. Experimental computational pre-emphasis.

    7. Quantitative image quality evaluation.

    8. Future validation using appropriate optical models
       and supervised human studies.
    """
)

st.subheader("Scientific Limitations")

st.markdown(
    """
    - The current optical model is simplified.
    - The Gaussian PSF does not represent all ocular aberrations.
    - Spherical equivalent does not fully describe refractive error.
    - A conventional smartphone displays the same image to both eyes.
    - Binocular vision and neural adaptation are not modelled.
    - Image sharpness metrics do not establish visual acuity.
    - The platform has not been clinically validated.
    - It must not be used as a substitute for prescribed spectacles.
    """
)

st.info(
    "Human testing requires appropriate institutional approval, "
    "ethical oversight and professional supervision. The platform "
    "must not be represented as a validated spectacle replacement."
)


# ============================================================
# 11. FOOTER
# ============================================================

st.divider()

st.caption(
    "OptiView-Rx | Experimental Computational Vision Research"
)

st.caption(
    "Research and educational prototype. "
    "Not intended for diagnosis or treatment."
)
