
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from xml.sax.saxutils import escape
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

# ============================================================
# OPTIVIEW-RX | COMPLETE RESEARCH PROTOTYPE
# ============================================================

st.set_page_config(
    page_title="OptiView-Rx | Research Prototype",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("👁️ OptiView-Rx")
st.caption(
    "Digital reading preference exploration and computational optics research prototype"
)

st.info(
    "**Research purpose and future vision**\n\n"
    "OptiView-Rx is an experimental research project investigating whether "
    "personalised computational optical compensation could eventually support "
    "reading on conventional smartphones for people with refractive errors. "
    "This is a research objective, not an established capability. The prototype "
    "does not provide spectacle replacement or prove spectacle-free reading."
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
        "This example demonstrates generic Gaussian image degradation."
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
            if np.any(mask) else 0.0
        )

    frequencies = bins / float(min(spectrum.shape))
    return frequencies, np.asarray(values)


# ============================================================
# 2. PDF REPORT HELPER FUNCTIONS
# ============================================================

def signed_diopters(value):
    return f"{value:+.2f} D"


def eye_interpretation(sphere, cylinder, axis, add):

    if sphere < -0.001:
        sphere_text = (
            f"The sphere value is {signed_diopters(sphere)}. A negative sphere "
            "is commonly used to prescribe correction for myopia (short-sightedness). "
            "This value alone does not tell us the person's unaided visual acuity."
        )
    elif sphere > 0.001:
        sphere_text = (
            f"The sphere value is {signed_diopters(sphere)}. A positive sphere "
            "is commonly used to prescribe correction for hyperopia (long-sightedness). "
            "This value alone does not tell us the person's unaided visual acuity."
        )
    else:
        sphere_text = (
            "The sphere value is 0.00 D, so no spherical power is entered for this eye. "
            "This does not rule out other visual or focusing issues."
        )

    if abs(cylinder) >= 0.001:
        cylinder_text = (
            f"The cylinder value is {signed_diopters(cylinder)}, with an axis of "
            f"{axis} degrees. Cylinder represents the prescribed amount of "
            "astigmatic correction; the axis describes its orientation, not its "
            "severity. The entered cylinder sign convention is preserved."
        )
    else:
        cylinder_text = (
            "The cylinder value is 0.00 D, so no astigmatic correction is entered "
            "for this eye. An axis is therefore not applicable."
        )

    if add > 0.001:
        add_text = (
            f"The near addition is +{add:.2f} D. This is an additional lens power "
            "that may be prescribed for near tasks. It is not, by itself, a measure "
            "of reading ability."
        )
    else:
        add_text = (
            "No near addition is entered for this eye (0.00 D). This does not "
            "establish how comfortably or clearly the person can read at near."
        )

    return sphere_text, cylinder_text, add_text


def build_eye_report_pdf(
    od_sph, od_cyl, od_axis, od_add, od_se,
    os_sph, os_cyl, os_axis, os_add, os_se,
    theme_name, font_size, font_family, line_height,
    letter_spacing, reading_width, body_contrast, accent_contrast,
    sample_choice, comfort, difficulty, comments,
    pupil_diameter, viewing_distance, pixel_pitch
):
    """Build a patient-friendly bilateral computational research report."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=17 * mm,
        title="OptiView-Rx Bilateral Eye Assessment Report",
        author="OptiView-Rx Research Prototype"
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"),
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#17365D"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name="ReportBody",
        parent=styles["BodyText"],
        fontSize=8.7,
        leading=12.5,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        name="SmallNote",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name="Callout",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#7A3412"),
        spaceAfter=3
    ))

    story = []

    def para(text, style="ReportBody"):
        story.append(Paragraph(text, styles[style]))

    def section(title):
        para(escape(title), "SectionHeading")

    def bullet(text):
        para("&#8226;&nbsp;&nbsp;" + text, "ReportBody")

    story.append(Spacer(1, 3 * mm))

    para("BILATERAL EYE ASSESSMENT REPORT", "ReportTitle")

    para(
        "OptiView-Rx computational research report — not a clinical diagnosis "
        "or an eye-care professional's prescription",
        "ReportSubtitle"
    )

    meta = [
        ["Report generated", date.today().strftime("%d %B %Y")],
        ["Assessment basis", "User-entered spectacle prescription values"],
        ["Report status", "Exploratory / informational"]
    ]

    meta_table = Table(meta, colWidths=[42 * mm, 125 * mm])

    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F6")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222222")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8D2DC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
    ]))

    story.append(meta_table)
    story.append(Spacer(1, 7))

    para(
        "<b>Important:</b> This report interprets the values entered into the "
        "OptiView-Rx prototype. It does not measure eyesight, diagnose an eye "
        "condition, verify the prescription, or determine whether spectacles "
        "can safely be stopped.",
        "Callout"
    )

    # Prescription overview
    section("1. Prescription overview")

    rows = [
        ["Parameter", "Right eye (OD)", "Left eye (OS)"],
        ["Sphere", signed_diopters(od_sph), signed_diopters(os_sph)],
        ["Cylinder", signed_diopters(od_cyl), signed_diopters(os_cyl)],
        [
            "Axis",
            f"{od_axis}°" if abs(od_cyl) >= 0.001 else "Not applicable",
            f"{os_axis}°" if abs(os_cyl) >= 0.001 else "Not applicable"
        ],
        ["Near addition (ADD)", f"+{od_add:.2f} D", f"+{os_add:.2f} D"],
        ["Spherical equivalent", signed_diopters(od_se), signed_diopters(os_se)]
    ]

    prescription_table = Table(
        rows,
        colWidths=[53 * mm, 57 * mm, 57 * mm],
        repeatRows=1
    )

    prescription_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8D2DC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F5F8FB")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
    ]))

    story.append(prescription_table)

    para(
        "Spherical equivalent is calculated as sphere + (cylinder ÷ 2). "
        "It is a simplified numerical summary and does not represent the full "
        "optical prescription.",
        "SmallNote"
    )

    # Right eye
    section("2. Right eye assessment (OD)")

    od_sphere_text, od_cylinder_text, od_add_text = eye_interpretation(
        od_sph, od_cyl, od_axis, od_add
    )

    para("<b>Sphere:</b> " + escape(od_sphere_text))
    para("<b>Cylinder and axis:</b> " + escape(od_cylinder_text))
    para("<b>Near addition:</b> " + escape(od_add_text))

    para(
        f"<b>Calculated spherical equivalent:</b> {od_se:+.2f} D. "
        "This calculation summarises the entered sphere and cylinder values; "
        "it does not measure unaided vision."
    )

    # Left eye
    section("3. Left eye assessment (OS)")

    os_sphere_text, os_cylinder_text, os_add_text = eye_interpretation(
        os_sph, os_cyl, os_axis, os_add
    )

    para("<b>Sphere:</b> " + escape(os_sphere_text))
    para("<b>Cylinder and axis:</b> " + escape(os_cylinder_text))
    para("<b>Near addition:</b> " + escape(os_add_text))

    para(
        f"<b>Calculated spherical equivalent:</b> {os_se:+.2f} D. "
        "This calculation summarises the entered sphere and cylinder values; "
        "it does not measure unaided vision."
    )

    # Bilateral comparison
    section("4. Comparison of both eyes")

    se_difference = abs(od_se - os_se)
    cyl_difference = abs(abs(od_cyl) - abs(os_cyl))
    add_difference = abs(od_add - os_add)

    para(
        f"The difference between the two spherical-equivalent values is "
        f"{se_difference:.2f} D. The difference between the absolute cylinder "
        f"magnitudes is {cyl_difference:.2f} D, and the difference between "
        f"the entered near additions is {add_difference:.2f} D."
    )

    para(
        "The two eyes may have different prescription requirements. These "
        "numerical differences are descriptive only; they do not, on their own, "
        "establish whether the difference is clinically significant or how well "
        "the eyes work together."
    )

    # Understanding visual correction
    section("5. Understanding Your Visual Correction")

    para(
        "<b>1. What your prescription indicates about your vision.</b> "
        "Sphere and cylinder values describe lens powers prescribed to address "
        "refractive components. Negative sphere is commonly associated with "
        "myopic correction, while positive sphere is commonly associated with "
        "hyperopic correction. Cylinder describes astigmatic correction."
    )

    para(
        "<b>2. How spherical power and astigmatism may affect image clarity.</b> "
        "Refractive error can contribute to blur when the eye is not adequately "
        "corrected. Astigmatism can cause directional differences in focus. "
        "The experience varies between individuals and cannot be quantified "
        "from these values alone."
    )

    para(
        "<b>3. Why your right and left eyes may require different corrections.</b> "
        "Each eye can have a different combination of sphere, cylinder and axis. "
        "The prescription records those individual requirements; it does not "
        "by itself describe binocular vision or visual comfort."
    )

    para(
        "<b>4. How near-vision addition may influence reading.</b> "
        "An ADD value is extra lens power prescribed for near tasks when needed. "
        "It does not independently establish reading speed, reading comfort, "
        "or the ability to read without spectacles."
    )

    para(
        "<b>5. Spectacle-Free Vision Possibility.</b> "
        "<b>Result: Not determined from prescription data.</b> Sphere, cylinder, "
        "axis and ADD values alone cannot reliably predict whether you can see "
        "clearly or read comfortably without spectacles. This report therefore "
        "does not classify your unaided vision as suitable or unsuitable for "
        "spectacle-free reading. A qualified eye-care professional must measure "
        "unaided distance and near visual acuity and assess your actual visual "
        "function. Do not stop or change prescribed spectacle use based on this "
        "report."
    )

    # Digital preferences
    section("6. Digital reading preferences recorded")

    preference_rows = [
        ["Setting", "Selected value"],
        ["Theme", escape(str(theme_name))],
        ["Font size", f"{font_size}"],
        ["Font family", escape(str(font_family))],
        ["Line spacing", f"{line_height:.1f}"],
        ["Letter spacing", f"{letter_spacing:.1f}"],
        ["Reading width", f"{reading_width}"],
        ["Body text contrast", f"{body_contrast:.2f}:1"],
        ["Accent contrast", f"{accent_contrast:.2f}:1"]
    ]

    pref_table = Table(
        preference_rows,
        colWidths=[65 * mm, 102 * mm]
    )

    pref_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8D2DC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F5F8FB")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
    ]))

    story.append(pref_table)

    para(
        "These are user-selected display preferences, not settings calculated "
        "from the prescription. Contrast values apply only to the selected "
        "foreground/background colour combinations and do not evaluate the "
        "entire interface.",
        "SmallNote"
    )

    # Guided reading feedback
    section("7. Guided reading feedback")

    para(f"<b>Reading sample:</b> {escape(str(sample_choice))}")

    if comfort:
        para(f"<b>Reported comfort:</b> {escape(str(comfort))}")
        para(f"<b>Reported difficulty:</b> {escape(str(difficulty))}")

        para(
            "This feedback is subjective and was recorded within the current "
            "app session. It is not a standardised reading assessment or "
            "visual-acuity measurement."
        )
    else:
        para("No reading feedback was submitted during this app session.")

    if comments and str(comments).strip():
        para("<b>Additional comment:</b> " + escape(str(comments)))

    # Computational research scenario
    section("8. Computational research scenario")

    para(
        f"The current simulation scenario records an assumed pupil diameter "
        f"of {pupil_diameter:.1f} mm, viewing distance of {viewing_distance} mm, "
        f"and display pixel pitch of {pixel_pitch} µm."
    )

    para(
        "The prototype's simplified elliptical Gaussian kernel and image "
        "processing demonstrations are exploratory mathematical illustrations. "
        "They are not an individualized eye model, a validated retinal image "
        "simulation, or a clinically tested correction method. The assumed "
        "pupil, viewing distance and pixel pitch are scenario inputs and are "
        "not incorporated into a validated physical eye model."
    )

    # Limitations
    section("9. Important limitations and recommended next steps")

    bullet(
        "This report is based on manually entered prescription values; the "
        "prototype does not verify the prescription."
    )

    bullet(
        "No unaided visual-acuity, refraction, binocular-vision or clinical "
        "reading test is performed by this app."
    )

    bullet(
        "The app does not diagnose eye disease, correct refractive error, "
        "or replace spectacles or contact lenses."
    )

    bullet(
        "Discuss the prescription and any difficulty with reading or seeing "
        "with a qualified optometrist or ophthalmologist."
    )

    bullet(
        "Continue using prescribed vision correction unless your eye-care "
        "professional advises otherwise."
    )

    bullet(
        "Any human research evaluating spectacle-free reading requires "
        "appropriate research ethics approval and professional oversight."
    )

    story.append(Spacer(1, 8))

    para(
        "<b>Research status:</b> OptiView-Rx is an experimental software "
        "prototype exploring digital reading preferences and simplified "
        "computational optics. Its long-term spectacle-free reading objective "
        "has not been established or clinically validated.",
        "SmallNote"
    )

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(
            18 * mm, 10 * mm, "OptiView-Rx | Research report"
        )
        canvas.drawRightString(
            A4[0] - 18 * mm,
            10 * mm,
            f"Page {document.page}"
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 3. BILATERAL PRESCRIPTION INPUTS
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
        -20.0, 20.0, -2.50, 0.25,
        format="%.2f"
    )

    od_cyl = st.number_input(
        "OD Cylinder (D)",
        -8.0, 8.0, -0.75, 0.25,
        format="%.2f"
    )

with od_right:
    od_axis = st.number_input(
        "OD Axis (°)",
        1, 180, 90, 1,
        disabled=(abs(od_cyl) < 0.001)
    )

    od_add = st.number_input(
        "OD Add (D)",
        0.0, 4.0, 0.0, 0.25,
        format="%.2f"
    )

st.sidebar.divider()
st.sidebar.subheader("Left Eye (OS)")

os_left, os_right = st.sidebar.columns(2)

with os_left:
    os_sph = st.number_input(
        "OS Sphere (D)",
        -20.0, 20.0, -3.00, 0.25,
        format="%.2f"
    )

    os_cyl = st.number_input(
        "OS Cylinder (D)",
        -8.0, 8.0, -1.25, 0.25,
        format="%.2f"
    )

with os_right:
    os_axis = st.number_input(
        "OS Axis (°)",
        1, 180, 95, 1,
        disabled=(abs(os_cyl) < 0.001)
    )

    os_add = st.number_input(
        "OS Add (D)",
        0.0, 4.0, 0.0, 0.25,
        format="%.2f"
    )

st.sidebar.caption(
    "Use values from a current, professionally verified prescription."
)


# ============================================================
# 4. PRESCRIPTION SUMMARY
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
# 5. DIGITAL READING PREFERENCES
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
    }
}

pref1, pref2 = st.columns(2)

with pref1:
    theme_name = st.selectbox(
        "Reading theme",
        list(themes.keys())
    )

    font_size = st.slider(
        "Font size",
        14, 40, 20, 1
    )

    line_height = st.slider(
        "Line spacing preference",
        1.2, 2.2, 1.6, 0.1
    )

with pref2:
    font_family = st.selectbox(
        "Font family preference",
        ["Arial", "Verdana", "Georgia", "Trebuchet MS"]
    )

    letter_spacing = st.slider(
        "Letter spacing preference",
        0.0, 4.0, 0.5, 0.1
    )

    reading_width = st.slider(
        "Reading width preference",
        400, 1000, 720, 20
    )

selected_theme = themes[theme_name]

background_color = selected_theme["background"]
text_color = selected_theme["text"]
accent_color = selected_theme["accent"]


# ============================================================
# 6. CONTRAST RATIO
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
# 7. GUIDED READING EXPERIENCE
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
        )
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
            "comments": comments
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
# 8. GENERIC IMAGE BLUR DEMONSTRATION
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
    0.0, 8.0, 2.0, 0.25
)

original_image = create_sample_image()

blurred_image = original_image.filter(
    ImageFilter.GaussianBlur(radius=blur_strength)
)

img1, img2 = st.columns(2)

with img1:
    st.markdown("**Original image**")
    st.image(original_image, use_container_width=True)

with img2:
    st.markdown("**Illustrative blurred image**")
    st.image(blurred_image, use_container_width=True)


# ============================================================
# 9. COMPUTATIONAL OPTICS EXPLORATION
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
        1.5, 6.0, 3.0, 0.1
    )

with sim2:
    viewing_distance = st.slider(
        "Viewing distance (mm)",
        200, 700, 400, 10
    )

with sim3:
    pixel_pitch = st.slider(
        "Display pixel pitch (µm)",
        35, 120, 55, 1
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

blurred_array = apply_kernel(source_gray, psf)

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
    0.001, 0.20, 0.02, 0.001,
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
        f"Pre-emphasis result sharpness proxy: "
        f"**{sharpness_proxy(preemphasis_after_blur):.2f}**"
    )

    st.caption(
        "A higher sharpness proxy does not establish better readability "
        "or improved human vision."
    )

st.subheader("D. Modulation transfer function estimate")

frequencies, mtf_values = calculate_mtf(psf)

fig, ax = plt.subplots()

ax.plot(frequencies, mtf_values)
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
# 10. RESEARCH ROADMAP
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
    "Obtain optometry, ophthalmology and optical engineering review"
]

for index, item in enumerate(roadmap):
    st.checkbox(item, key=f"roadmap_{index}")


# ============================================================
# 11. SCIENTIFIC LIMITATIONS
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
# 12. DOWNLOADABLE BILATERAL EYE ASSESSMENT REPORT
# ============================================================

st.divider()
st.header("9. Bilateral Eye Assessment Report")

st.write(
    "Generate a downloadable report that explains the entered prescription "
    "for each eye, compares both eyes, and discusses what can and cannot be "
    "concluded about spectacle-free reading."
)

feedback = st.session_state.get("optiview_feedback", {})

pdf_bytes = build_eye_report_pdf(
    od_sph=od_sph,
    od_cyl=od_cyl,
    od_axis=od_axis,
    od_add=od_add,
    od_se=od_se,
    os_sph=os_sph,
    os_cyl=os_cyl,
    os_axis=os_axis,
    os_add=os_add,
    os_se=os_se,
    theme_name=theme_name,
    font_size=font_size,
    font_family=font_family,
    line_height=line_height,
    letter_spacing=letter_spacing,
    reading_width=reading_width,
    body_contrast=body_contrast,
    accent_contrast=accent_contrast,
    sample_choice=feedback.get("sample", sample_choice),
    comfort=feedback.get("comfort", ""),
    difficulty=feedback.get("difficulty", ""),
    comments=feedback.get("comments", ""),
    pupil_diameter=pupil_diameter,
    viewing_distance=viewing_distance,
    pixel_pitch=pixel_pitch
)

st.download_button(
    label="Download Bilateral Eye Assessment Report (PDF)",
    data=pdf_bytes,
    file_name="OptiView-Rx_Bilateral_Eye_Assessment_Report.pdf",
    mime="application/pdf",
    use_container_width=True
)

st.caption(
    "The PDF is a computational research report, not a doctor's diagnosis, "
    "clinical eye examination, or confirmation that you can read without spectacles."
)


# ============================================================
# 13. FOOTER
# ============================================================

st.divider()

st.caption(
    "OptiView-Rx | Research Prototype | "
    "Digital Reading Accessibility and Exploratory Computational Optics"
)
