        st.caption("The prescription axis sets the orientation of the simplified elliptical kernel.")

    st.subheader("B. Simulated retinal-image proxy")
    st.caption("This is a display-image convolution proxy, not a prediction of an actual person's retinal image.")
    image_a, image_b = st.columns(2)
    with image_a:
        st.image(sample_array, caption="Input sample", use_container_width=True)
    with image_b:
        st.image(simulated_blur, caption="After model PSF convolution", use_container_width=True)

    st.subheader("C. Experimental pre-emphasis")
    st.caption("The filter is applied to the input image, then the same model PSF is applied to that pre-emphasised image. This is a numerical experiment only.")
    regularization = st.slider("Inverse-filter regularisation", 0.001, 0.20, 0.02, 0.001, format="%.3f")
    preemphasis_enabled = st.checkbox("Run regularised pre-emphasis experiment", value=False)
    if preemphasis_enabled:
        preemphasised = regularized_preemphasis(sample_array, psf, regularization)
        preemphasis_after_blur = apply_psf(preemphasised, psf)
        pre_col1, pre_col2 = st.columns(2)
        with pre_col1:
            st.image(preemphasised, caption="Pre-emphasised input", use_container_width=True)
        with pre_col2:
            st.image(preemphasis_after_blur, caption="Pre-emphasised input after model blur", use_container_width=True)
        base_score = image_sharpness_score(simulated_blur)
        experimental_score = image_sharpness_score(preemphasis_after_blur)
        st.write(f"Blurred baseline sharpness proxy: **{base_score:.2f}**")
        st.write(f"Pre-emphasis result sharpness proxy: **{experimental_score:.2f}**")
        st.caption("A higher sharpness proxy is not proof of better legibility or improved human vision; ringing and noise amplification can increase this score.")

    st.subheader("D. Modulation transfer function (MTF) estimate")
    frequencies, mtf_values = mtf_curve(psf)
    fig, ax = plt.subplots()
    ax.plot(frequencies, mtf_values)
    ax.set_xlabel("Spatial frequency (cycles/pixel)")
    ax.set_ylabel("MTF")
    ax.set_ylim(0, 1.05)
    ax.set_title("Radially averaged MTF of model PSF")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)

    st.info(
        "Interpretation boundary: this engine explores how assumed defocus "
        "parameters affect a simplified image model. It does not establish "
        "that an ordinary smartphone can overcome refractive error. The next "
        "research step is validation against an established optical model "
        "and measured optical/visual data."
    )

except ImportError as error:
    st.error(
        "The computational optics module or one of its dependencies is missing. "
        "Install the packages listed in requirements.txt. "
        f"Technical detail: {error}"
    )
except Exception as error:
    st.error(f"The exploratory optics simulation could not run: {error}")


# ============================================================
# 10. RESEARCH NOTES AND NEXT EXPERIMENTS
# ============================================================

st.markdown("---")
st.header("8. Computational Optics Research Roadmap")

research_topics = [
    "Validate simplified PSF model against an established optical model",
    "Compare directional MTF for astigmatic blur",
    "Add wavefront aberration modelling with appropriate optical data",
    "Evaluate pre-emphasis stability, ringing and noise amplification",
    "Compare model outputs with measured optical bench data",
    "Investigate conventional-display physical feasibility",
    "Obtain optometry/ophthalmology and optical engineering review"
]

for topic in research_topics:
    st.checkbox(
        topic,
        key=f"research_{topic}"
    )


# ============================================================
# 11. RESEARCH LIMITATIONS
# ============================================================

st.markdown("---")
st.header("9. Scientific Limitations")

st.markdown("""
This prototype currently:

- Collects bilateral spectacle prescription parameters.
- Calculates spherical equivalent for descriptive reporting.
- Allows independent digital reading preference adjustments.
- Calculates contrast ratios for selected colour combinations.
- Demonstrates generic Gaussian image degradation.

It does NOT currently:

- Simulate an individual's complete optical system.
- Calculate retinal image formation.
- Model an individual's point spread function.
- Perform wavefront-based optical correction.
- Implement computational optical pre-distortion.
- Correct myopia, hyperopia, astigmatism or presbyopia.
- Replace spectacles or contact lenses.
- Demonstrate improved visual acuity in human participants.
""")

st.info(
    "Future optical modelling must be based on explicit physical "
    "assumptions, validated mathematical models and reproducible "
    "experimental comparisons. Human testing requires appropriate "
    "professional oversight and research ethics approval."
)


# ============================================================
# 12. FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "OptiView-Rx | Research Prototype v2.0 | "
    "Digital Accessibility and Exploratory Computational Optics"
)
