
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================================
# OPTIVIEW-RX | COMPLETE RESEARCH PROTOTYPE
# No HTML, CSS, unsafe_allow_html, or external optics.py required.
# ============================================================

st.set_page_config(
    page_title="OptiView-Rx | Research Prototype",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("👁️ OptiView-Rx")
st.caption(
    "Digital reading preference exploration and computational optics research prototype"
)

st.info(
    "**Research purpose and future vision**\n\n"
    "OptiView-Rx is an experimental research project investigating whether personalised "
    "computational optical compensation could eventually support reading on conventional "
    "smartphones for people with refractive errors. This is a research objective, not an "
    "established capability. The prototype does not provide spectacle replacement or prove "
    "spectacle-free reading."
)

# ============================================================
# 1. HELPER FUNCTIONS
# ============================================================

def spherical_equivalent(sphere, cylinder):
    return sphere + cylinder / 2.0


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def linearize_channel(value):
    value = value / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    r, g, b = (linearize_channel(x) for x in (r, g, b))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(foreground, background):
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    lighter = max(first, second)
    darker = min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def create_sample_image():
    image = Image.new("RGB", (900, 360), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.text(
        (35, 30),
        "OPTIVIEW-RX | IMAGE PROCESSING DEMONSTRATION",
        fill="black",
        font=font
    )

    draw.line((35, 65, 860, 65), fill="gray", width=2)

    lines = [
        "Digital displays produce images using patterns of light.",
        "Image processing can modify edges and spatial frequencies.",
        "Optical systems influence how displayed images are perceived.",
        "Experimental modelling helps investigate these interactions.",
        "This example demonstrates generic Gaussian image degradation.",
    ]

    y = 105

    for line in lines:
        draw.text((35, y), line, fill="black", font=font)
        y += 45

    return image


def make_elliptical_psf(sphere, cylinder, axis_degrees, size=65):
    """Create a normalised elliptical Gaussian kernel for demonstration only."""

    if size % 2 == 0:
        size += 1

    coords = np.arange(size) - size // 2
    xx, yy = np.meshgrid(coords, coords)

    theta = np.deg2rad(axis_degrees)

    rotated_x = xx * np.cos(theta) + yy * np.sin(theta)
    rotated_y = -xx * np.sin(theta) + yy * np.cos(theta)

    meridian_one = abs(float(sphere))
    meridian_two = abs(float(sphere + cylinder))

    sigma_one = 0.8 + min(meridian_one, 12.0) * 0.42
    sigma_two = 0.8 + min(meridian_two, 12.0) * 0.42

    kernel = np.exp(
        -0.5 * (
            (rotated_x / sigma_one) ** 2
            + (rotated_y / sigma_two) ** 2
        )
    )

    total = kernel.sum()

    if total <= 0:
        raise ValueError("The simulated PSF could not be normalised.")

    return kernel / total, sigma_one, sigma_two


def apply_kernel(image_array, kernel):
    """Apply a same-size convolution using NumPy FFT operations."""

    image_float = image_array.astype(np.float32) / 255.0

    height, width = image_float.shape
    kh, kw = kernel.shape

    padded = np.zeros((height, width), dtype=np.float32)
    padded[:kh, :kw] = kernel

    padded = np.roll(padded, -(kh // 2), axis=0)
    padded = np.roll(padded, -(kw // 2), axis=1)

    result = np.fft.ifft2(
        np.fft.fft2(image_float) * np.fft.fft2(padded)
    ).real

    result = np.clip(result, 0.0, 1.0)

    return (result * 255).astype(np.uint8)


def sharpness_proxy(image_array):
    arr = image_array.astype(np.float32)

    gx = np.diff(arr, axis=1)
    gy = np.diff(arr, axis=0)

    return float(
        (np.mean(gx ** 2) + np.mean(gy ** 2)) / 2.0
    )


def calculate_mtf(kernel):
    spectrum = np.abs(
        np.fft.fftshift(np.fft.fft2(kernel))
    )

    spectrum = spectrum / max(float(spectrum.max()), 1e-12)

    centre_y, centre_x = np.array(spectrum.shape) // 2

    y, x = np.indices(spectrum.shape)

    radius = np.sqrt(
        (x - centre_x) ** 2 + (y - centre_y) ** 2
    )

    bins = np.arange(0, min(spectrum.shape) // 2)

    values = []

    for index in bins:
        mask = (
            (radius >= index)
            & (radius < index + 1)
        )

        values.append(
            float(spectrum[mask].mean())
            if np.any(mask)
            else 0.0
        )

    frequencies = bins / float(min(spectrum.shape))

    return frequencies, np.asarray(values)


# ============================================================
# 2. BILATERAL PRESCRIPTION INPUTS
# ============================================================

st.sidebar.header("📋 Visual Profile")

st.sidebar.caption(
    "Optional prescription values for exploratory research analysis."
)

st.sidebar.subheader("Right Eye (OD)")

od_left, od_right = st.sidebar.columns(2)

with od_left:
    od_sph = st.number_input(
        "OD Sphere (D)",
        -20.0,
        20.0,
        -2.50,
        0.25,
        format="%.2f"
    )

    od_cyl = st.number_input(
        "OD Cylinder (D)",
        -8.0,
        8.0,
        -0.75,
        0.25,
        format="%.2f"
    )

with od_right:
    od_axis = st.number_input(
        "OD Axis (°)",
        1,
        180,
        90,
        1,
        disabled=(abs(od_cyl) < 0.001)
    )

    od_add = st.number_input(
        "OD Add (D)",
        0.0,
        4.0,
        0.0,
        0.25,
        format="%.2f"
    )

st.sidebar.divider()
st.sidebar.subheader("Left Eye (OS)")

os_left, os_right = st.sidebar.columns(2)

with os_left:
    os_sph = st.number_input(
        "OS Sphere (D)",
        -20.0,
        20.0,
        -3.00,
        0.25,
        format="%.2f"
    )

    os_cyl = st.number_input(
        "OS Cylinder (D)",
        -8.0,
        8.0,
        -1.25,
        0.25,
        format="%.2f"
    )

with os_right:
    os_axis = st.number_input(
        "OS Axis (°)",
        1,
        180,
        95,
        1,
        disabled=(abs(os_cyl) < 0.001)
    )

    os_add = st.number_input(
        "OS Add (D)",
        0.0,
        4.0,
        0.0,
        0.25,
        format="%.2f"
    )

st.sidebar.caption(
    "Use values from a current, professionally verified prescription."
)


# ============================================================
# 3. PRESCRIPTION SUMMARY
# ============================================================

st.header("1. Bilateral Prescription Analysis")

od_se = spherical_equivalent(od_sph, od_cyl)
os_se = spherical_equivalent(os_sph, os_cyl)

se_difference = abs(od_se - os_se)

m1, m2, m3 = st.columns(3)

m1.metric("OD Spherical Equivalent", f"{od_se:+.2f} D")
m2.metric("OS Spherical Equivalent", f"{os_se:+.2f} D")
m3.metric("Difference between eyes", f"{se_difference:.2f} D")

with st.expander("View complete prescription details"):

    eye1, eye2 = st.columns(2)

    with eye1:
        st.markdown("**Right eye — OD**")
        st.write(f"Sphere: {od_sph:+.2f} D")
        st.write(f"Cylinder: {od_cyl:+.2f} D")

        st.write(
            f"Axis: {od_axis}°"
            if abs(od_cyl) >= 0.001
            else "Axis: Not applicable"
        )

        st.write(f"Near addition: +{od_add:.2f} D")

    with eye2:
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
    "Spherical equivalent is a descriptive summary, not a complete optical correction."
)


# ============================================================
# 4. DIGITAL READING PREFERENCES
# ============================================================

st.divider()
st.header("2. Digital Reading Preferences")

st.write(
    "Explore presentation settings according to personal preference. "
    "They are not calculated from prescription power."
)

themes = {
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
    },
}

pref1, pref2 = st.columns(2)

with pref1:
    theme_name = st.selectbox(
        "Reading theme",
        list(themes.keys())
    )

    font_size = st.slider(
        "Font size",
        14,
        40,
        20,
        1
    )

    line_height = st.slider(
        "Line spacing preference",
        1.2,
        2.2,
        1.6,
        0.1
    )

with pref2:
    font_family = st.selectbox(
        "Font family preference",
        ["Arial", "Verdana", "Georgia", "Trebuchet MS"]
    )

    letter_spacing = st.slider(
        "Letter spacing preference",
        0.0,
        4.0,
        0.5,
        0.1
    )

    reading_width = st.slider(
        "Reading width preference",
        400,
        1000,
        720,
        20
    )

selected_theme = themes[theme_name]

background_color = selected_theme["background"]
text_color = selected_theme["text"]
accent_color = selected_theme["accent"]


# ============================================================
# 5. CONTRAST RATIO
# ============================================================

st.divider()
st.subheader("3. Contrast Evaluation")

body_contrast = contrast_ratio(
    text_color,
    background_color
)

accent_contrast = contrast_ratio(
    accent_color,
    background_color
)

c1, c2 = st.columns(2)

c1.metric(
    "Body text contrast",
    f"{body_contrast:.2f}:1"
)

c2.metric(
    "Accent contrast",
    f"{accent_contrast:.2f}:1"
)

st.caption(
    "Contrast ratios are calculated for the selected colour combinations; "
    "they do not assess the complete user interface."
)


# ============================================================
# 6. GUIDED READING EXPERIENCE
# ============================================================

st.divider()

with st.container(border=True):

    st.header("4. Guided Reading Experience")

    st.caption(
        "Choose a sample, read it at your own pace, and record your experience."
    )

    samples = {
        "Quick sample": (
            "Reading is part of everyday life. We use it to understand "
            "messages, learn new ideas and explore the world around us."
        ),

        "Everyday reading": (
            "Clear and comfortable digital reading depends on several "
            "factors, including typography, contrast, screen brightness, "
            "viewing distance and individual visual preferences. "
            "Different reading settings may feel more comfortable for "
            "different people."
        ),

        "Longer passage": (
            "Digital screens are used for reading throughout the day. "
            "People may read messages, articles, study materials and "
            "long documents on the same device. The experience can be "
            "influenced by text size, spacing, contrast, lighting and "
            "the distance between the eyes and the screen. Exploring "
            "these settings can help users describe their preferences "
            "and identify which presentation feels easier to read."
        ),
    }

    sample_choice = st.selectbox(
        "Step 1 · Choose a reading sample",
        list(samples.keys()),
        key="reading_sample"
    )

    st.divider()
    st.subheader("Step 2 · Your reading space")

    st.caption(
        f"Selected preferences: {theme_name} theme · "
        f"{font_size} font size · {font_family} · "
        f"{line_height:.1f} line spacing"
    )

    with st.container(border=True):
        st.markdown("#### Reading sample")
        st.write(samples[sample_choice])

    with st.expander("View all selected preferences"):
        st.write(f"Theme: {theme_name}")
        st.write(f"Font size: {font_size}")
        st.write(f"Font family: {font_family}")
        st.write(f"Line spacing: {line_height}")
        st.write(f"Letter spacing: {letter_spacing}")
        st.write(f"Reading width: {reading_width}")

    st.divider()
    st.subheader("Step 3 · Record your experience")

    with st.form("reading_feedback_form"):

        comfort = st.radio(
            "How comfortable was the sample to read?",
            [
                "Very comfortable",
                "Comfortable",
                "Somewhat uncomfortable",
                "Difficult to read"
            ],
            index=1
        )

        difficulty = st.radio(
            "Did you notice any difficulty?",
            [
                "No difficulty",
                "Blurred text",
                "Difficulty focusing",
                "Eye strain or discomfort",
                "Other"
            ],
            index=0
        )

        more_samples = st.radio(
            "Would you like to try another sample?",
            [
                "No, I am finished",
                "Yes, a different sample"
            ],
            index=0
        )

        comments = st.text_area(
            "Additional feedback (optional)",
            placeholder="Describe what felt comfortable or difficult...",
            max_chars=1000
        )

        submitted = st.form_submit_button(
            "Submit reading feedback",
            use_container_width=True
        )

    if submitted:

        st.session_state["optiview_feedback"] = {
            "sample": sample_choice,
            "comfort": comfort,
            "difficulty": difficulty,
            "more_samples": more_samples,
            "comments": comments,
        }

        st.success(
            "Your feedback has been recorded for this app session."
        )

        st.markdown("**Your response summary**")

        st.write(f"Sample: {sample_choice}")
        st.write(f"Comfort: {comfort}")
        st.write(f"Difficulty: {difficulty}")
        st.write(f"Try another sample: {more_samples}")

        if comments.strip():
            st.write(f"Additional feedback: {comments}")

st.caption(
    "This activity records subjective feedback only. It is not a visual-acuity test "
    "and does not establish clinical improvement or spectacle-free reading. "
    "Continue prescribed vision correction and follow professional eye-care advice."
)


# ============================================================
# 7. GENERIC IMAGE BLUR DEMONSTRATION
# ============================================================

st.divider()
st.header("5. Image Processing Demonstration")

st.warning(
    "This is a generic Gaussian blur demonstration. It is not a myopia simulation, "
    "retinal image model, optical correction algorithm or clinical test. "
    "The blur strength is manually selected."
)

blur_strength = st.slider(
    "Illustrative Gaussian blur strength",
    0.0,
    8.0,
    2.0,
    0.25
)

original_image = create_sample_image()

blurred_image = original_image.filter(
    ImageFilter.GaussianBlur(radius=blur_strength)
)

img1, img2 = st.columns(2)

with img1:
    st.markdown("**Original image**")
    st.image(
        original_image,
        use_container_width=True
    )

with img2:
    st.markdown("**Illustrative blurred image**")
    st.image(
        blurred_image,
        use_container_width=True
    )


# ============================================================
# 8. COMPUTATIONAL OPTICS EXPLORATION
# ============================================================

st.divider()
st.header("6. Exploratory Computational Optics")

st.warning(
    "Research simulation only. This simplified elliptical Gaussian model "
    "is not an individualized eye model, validated retinal simulation "
    "or clinical correction method."
)

st.write(
    "The model uses sphere and sphere-plus-cylinder as two principal "
    "meridional values. It is an exploratory mathematical approximation, "
    "not a clinical prediction."
)

eye_choice = st.radio(
    "Select eye for simulation",
    ["Right eye (OD)", "Left eye (OS)"],
    horizontal=True
)

if eye_choice == "Right eye (OD)":
    sim_sphere = od_sph
    sim_cylinder = od_cyl
    sim_axis = od_axis
else:
    sim_sphere = os_sph
    sim_cylinder = os_cyl
    sim_axis = os_axis

sim1, sim2, sim3 = st.columns(3)

with sim1:
    pupil_diameter = st.slider(
        "Assumed pupil diameter (mm)",
        1.5,
        6.0,
        3.0,
        0.1
    )

with sim2:
    viewing_distance = st.slider(
        "Viewing distance (mm)",
        200,
        700,
        400,
        10
    )

with sim3:
    pixel_pitch = st.slider(
        "Display pixel pitch (µm)",
        35,
        120,
        55,
        1
    )

psf, sigma_a, sigma_b = make_elliptical_psf(
    sim_sphere,
    sim_cylinder,
    sim_axis
)

source_gray = np.asarray(
    create_sample_image().convert("L"),
    dtype=np.uint8
)

blurred_array = apply_kernel(
    source_gray,
    psf
)

st.subheader("A. Simplified point spread function")

psf_col, detail_col = st.columns([1, 2])

with psf_col:
    st.image(
        (psf / psf.max() * 255).astype(np.uint8),
        caption="Normalised elliptical Gaussian kernel",
        clamp=True,
        use_container_width=True
    )

with detail_col:
    st.write(
        f"Model kernel spread, principal direction 1: **{sigma_a:.2f} pixels**"
    )

    st.write(
        f"Model kernel spread, principal direction 2: **{sigma_b:.2f} pixels**"
    )

    st.write(f"Prescription axis used for orientation: **{sim_axis}°**")
    st.write(f"Assumed pupil diameter: **{pupil_diameter:.1f} mm**")
    st.write(f"Assumed viewing distance: **{viewing_distance} mm**")
    st.write(f"Assumed display pixel pitch: **{pixel_pitch} µm**")

    st.caption(
        "The pupil, viewing distance and pixel pitch are recorded as scenario "
        "assumptions; this simplified kernel does not yet use them in a "
        "validated physical eye model."
    )

st.subheader("B. Image convolution proxy")

conv1, conv2 = st.columns(2)

with conv1:
    st.image(
        source_gray,
        caption="Input greyscale image",
        use_container_width=True
    )

with conv2:
    st.image(
        blurred_array,
        caption="After simplified kernel convolution",
        use_container_width=True
    )

st.subheader("C. Experimental regularised pre-emphasis")

st.caption(
    "This optional numerical experiment applies a frequency-domain inverse filter. "
    "It may amplify noise or create ringing and is not a validated correction technique."
)

regularization = st.slider(
    "Inverse-filter regularisation",
    0.001,
    0.20,
    0.02,
    0.001,
    format="%.3f"
)

run_preemphasis = st.checkbox(
    "Run pre-emphasis experiment",
    value=False
)

if run_preemphasis:

    image_float = source_gray.astype(np.float32) / 255.0

    height, width = image_float.shape
    kernel_pad = np.zeros((height, width), dtype=np.float32)

    kh, kw = psf.shape

    kernel_pad[:kh, :kw] = psf

    kernel_pad = np.roll(
        kernel_pad,
        -(kh // 2),
        axis=0
    )

    kernel_pad = np.roll(
        kernel_pad,
        -(kw // 2),
        axis=1
    )

    transfer = np.fft.fft2(kernel_pad)
    source_frequency = np.fft.fft2(image_float)

    inverse_filter = (
        np.conj(transfer)
        / (np.abs(transfer) ** 2 + regularization)
    )

    preemphasised = np.fft.ifft2(
        source_frequency * inverse_filter
    ).real

    preemphasised = np.clip(
        preemphasised,
        0.0,
        1.0
    )

    preemphasis_image = (
        preemphasised * 255
    ).astype(np.uint8)

    preemphasis_after_blur = apply_kernel(
        preemphasis_image,
        psf
    )

    pre_a, pre_b = st.columns(2)

    with pre_a:
        st.image(
            preemphasis_image,
            caption="Pre-emphasised input",
            use_container_width=True
        )

    with pre_b:
        st.image(
            preemphasis_after_blur,
            caption="After model convolution",
            use_container_width=True
        )

    st.write(
        f"Blurred image sharpness proxy: **{sharpness_proxy(blurred_array):.2f}**"
    )

    st.write(
        f"Pre-emphasis result sharpness proxy: **{sharpness_proxy(preemphasis_after_blur):.2f}**"
    )

    st.caption(
        "A higher sharpness proxy does not establish better readability "
        "or improved human vision."
    )

st.subheader("D. Modulation transfer function estimate")

frequencies, mtf_values = calculate_mtf(psf)

fig, ax = plt.subplots()

ax.plot(
    frequencies,
    mtf_values
)

ax.set_xlabel("Spatial frequency (cycles/pixel)")
ax.set_ylabel("Normalised MTF")
ax.set_ylim(0, 1.05)
ax.set_title("Radially averaged MTF of the model kernel")
ax.grid(True, alpha=0.3)

st.pyplot(fig)
plt.close(fig)

st.info(
    "Interpretation boundary: this model demonstrates mathematical image "
    "processing under simplified assumptions. It does not show that an ordinary "
    "smartphone can overcome refractive error. Further work requires validation "
    "against established optical models and measured optical data."
)


# ============================================================
# 9. RESEARCH ROADMAP
# ============================================================

st.divider()
st.header("7. Research Roadmap")

roadmap = [
    "Validate the simplified PSF against an established optical model",
    "Compare directional MTF for astigmatic blur",
    "Investigate wavefront aberration modelling using appropriate optical data",
    "Evaluate pre-emphasis stability, ringing and noise amplification",
    "Compare model outputs with measured optical bench data",
    "Investigate physical feasibility on conventional displays",
    "Obtain optometry, ophthalmology and optical engineering review",
]

for index, item in enumerate(roadmap):
    st.checkbox(
        item,
        key=f"roadmap_{index}"
    )


# ============================================================
# 10. SCIENTIFIC LIMITATIONS
# ============================================================

st.divider()
st.header("8. Scientific Limitations")

st.markdown("""
**This prototype currently:**

- Collects bilateral spectacle prescription parameters.
- Calculates spherical equivalent for descriptive reporting.
- Allows users to explore reading presentation preferences.
- Calculates contrast ratios for selected colour combinations.
- Collects subjective reading feedback within the current app session.
- Demonstrates generic Gaussian blur and a simplified image-kernel experiment.

**This prototype does not:**

- Simulate an individual's complete optical system.
- Calculate a clinically accurate retinal image.
- Perform validated wavefront-based optical correction.
- Establish that pre-distortion can compensate for refractive error.
- Correct myopia, hyperopia, astigmatism or presbyopia.
- Replace spectacles or contact lenses.
- Demonstrate improved visual acuity or spectacle-free reading in people.
""")

st.info(
    "Future optical modelling requires explicit physical assumptions, "
    "validated mathematical models and reproducible experiments. Any human "
    "study requires appropriate professional oversight and research ethics approval."
)


# ============================================================
# 11. FOOTER
# ============================================================

st.divider()

st.caption(
    "OptiView-Rx | Research Prototype | "
    "Digital Reading Accessibility and Exploratory Computational Optics"
)
