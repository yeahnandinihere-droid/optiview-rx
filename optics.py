"""
OptiView-Rx exploratory computational optics module.

This module implements a deliberately simplified, monochromatic,
paraxial/geometric defocus model for research demonstrations.

It is NOT a clinical eye model, a prescription calculator, a validated
retinal image simulator, or a vision-correction algorithm.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.signal import fftconvolve


def meridional_defocus(sphere_d: float, cylinder_d: float) -> tuple[float, float]:
    """Return absolute defocus magnitudes in the two principal meridians.

    The two meridional powers represented by a minus/plus-cylinder
    prescription are sphere and sphere+cylinder. Axis orientation is
    handled separately. Prescription sign is discarded because this
    simplified blur model uses magnitude only.
    """
    return abs(float(sphere_d)), abs(float(sphere_d) + float(cylinder_d))


def _pixel_blur_sigmas(
    defocus_d: tuple[float, float],
    pupil_diameter_mm: float,
    viewing_distance_mm: float,
    pixel_pitch_um: float,
) -> tuple[float, float]:
    """Approximate Gaussian sigma in display pixels for each meridian.

    Approximation:
      blur-circle diameter (retinal) ~= pupil * eye focal length * |D|
      and convert its visual angle to display pixels.

    The eye focal length cancels in the angular/pixel conversion, leaving
      blur diameter in pixels ~= pupil_m * |D| * distance_m / pixel_pitch_m.
    A Gaussian with sigma = blur diameter / 4 approximates a defocus disk.
    """
    if pupil_diameter_mm <= 0 or viewing_distance_mm <= 0 or pixel_pitch_um <= 0:
        raise ValueError("Pupil diameter, viewing distance and pixel pitch must be positive.")
    pupil_m = pupil_diameter_mm / 1000.0
    distance_m = viewing_distance_mm / 1000.0
    pixel_pitch_m = pixel_pitch_um / 1_000_000.0
    sigmas = []
    for power in defocus_d:
        blur_diameter_px = pupil_m * abs(power) * distance_m / pixel_pitch_m
        sigmas.append(blur_diameter_px / 4.0)
    return float(sigmas[0]), float(sigmas[1])


def make_astigmatic_psf(
    sphere_d: float,
    cylinder_d: float,
    axis_deg: float,
    pupil_diameter_mm: float = 3.0,
    viewing_distance_mm: float = 400.0,
    pixel_pitch_um: float = 55.0,
    kernel_limit: int = 161,
) -> tuple[np.ndarray, dict]:
    """Create a normalised, oriented elliptical Gaussian PSF approximation.

    Sigma parallel to the cylinder axis uses |sphere|; sigma perpendicular
    to it uses |sphere+cylinder|. This is a simplified principal-meridian
    approximation, not a full wave-optics or ray-tracing model.
    """
    if not 0 <= float(axis_deg) <= 180:
        raise ValueError("Axis must be between 0 and 180 degrees.")
    d_axis, d_perp = meridional_defocus(sphere_d, cylinder_d)
    sigma_axis, sigma_perp = _pixel_blur_sigmas(
        (d_axis, d_perp), pupil_diameter_mm, viewing_distance_mm, pixel_pitch_um
    )

    # A small numerical floor avoids a singular covariance for zero cylinder.
    sx = max(sigma_axis, 0.08)
    sy = max(sigma_perp, 0.08)
    radius = int(math.ceil(4.0 * max(sx, sy)))
    radius = max(2, min(radius, (kernel_limit - 1) // 2))
    coords = np.arange(-radius, radius + 1, dtype=float)
    xx, yy = np.meshgrid(coords, coords)

    theta = math.radians(float(axis_deg))
    # Rotate image coordinates into the prescription's principal meridians.
    along_axis = xx * math.cos(theta) + yy * math.sin(theta)
    perpendicular = -xx * math.sin(theta) + yy * math.cos(theta)
    psf = np.exp(
        -0.5 * ((along_axis / sx) ** 2 + (perpendicular / sy) ** 2)
    )
    total = float(psf.sum())
    if total > 0:
        psf /= total

    metadata = {
        "sigma_parallel_px": sigma_axis,
        "sigma_perpendicular_px": sigma_perp,
        "meridional_defocus_d": (d_axis, d_perp),
        "axis_deg": float(axis_deg),
        "kernel_size": int(psf.shape[0]),
        "model": "elliptical Gaussian approximation to geometric defocus",
    }
    return psf.astype(np.float32), metadata


def apply_psf(image: np.ndarray, psf: np.ndarray) -> np.ndarray:
    """Convolve a grayscale or RGB image with a PSF, preserving image size."""
    arr = np.asarray(image, dtype=np.float32)
    if arr.ndim == 2:
        result = fftconvolve(arr, psf, mode="same")
    elif arr.ndim == 3:
        result = np.stack(
            [fftconvolve(arr[..., channel], psf, mode="same")
             for channel in range(arr.shape[2])],
            axis=-1,
        )
    else:
        raise ValueError("Image must be a 2D grayscale or 3D channel image.")
    return np.clip(result, 0, 255).astype(np.uint8)


def regularized_preemphasis(
    image: np.ndarray,
    psf: np.ndarray,
    regularization: float = 0.02,
) -> np.ndarray:
    """Experimental regularised frequency-domain pre-emphasis.

    This is a simulation-only inverse-filter experiment. Regularisation
    limits unstable amplification; it cannot restore information that is
    absent from the display/optical system or guarantee better human vision.
    """
    if not 0.001 <= float(regularization) <= 1.0:
        raise ValueError("Regularization must be between 0.001 and 1.0.")
    arr = np.asarray(image, dtype=np.float32)
    if arr.ndim == 2:
        channels = arr[..., None]
        squeeze = True
    elif arr.ndim == 3:
        channels = arr
        squeeze = False
    else:
        raise ValueError("Image must be a 2D grayscale or 3D channel image.")

    outputs = []
    for channel in range(channels.shape[2]):
        plane = channels[..., channel]
        padded = np.zeros_like(plane)
        kh, kw = psf.shape
        padded[:kh, :kw] = psf
        padded = np.roll(padded, (-(kh // 2), -(kw // 2)), axis=(0, 1))
        transfer = np.fft.fft2(padded)
        observed = np.fft.fft2(plane)
        inverse_filter = np.conj(transfer) / (
            np.abs(transfer) ** 2 + float(regularization)
        )
        reconstructed = np.fft.ifft2(observed * inverse_filter).real
        outputs.append(np.clip(reconstructed, 0, 255))
    result = np.stack(outputs, axis=-1).astype(np.uint8)
    return result[..., 0] if squeeze else result


def mtf_curve(psf: np.ndarray, samples: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """Return a radial-average MTF estimate in cycles/pixel.

    For the generally oriented/astigmatic PSF this radial average is a
    compact summary; it hides directional differences, so it is not a
    complete MTF characterisation.
    """
    h, w = psf.shape
    padded = np.zeros((max(128, h), max(128, w)), dtype=np.float32)
    padded[:h, :w] = psf
    padded = np.roll(padded, (-(h // 2), -(w // 2)), axis=(0, 1))
    otf = np.fft.fftshift(np.fft.fft2(padded))
    mtf = np.abs(otf)
    mtf /= max(float(mtf.max()), 1e-12)

    yy, xx = np.indices(mtf.shape)
    cy, cx = np.array(mtf.shape) // 2
    radius = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    max_freq = min(padded.shape) / 2.0
    bins = np.linspace(0, max_freq, samples + 1)
    radial = np.zeros(samples, dtype=float)
    frequencies = (bins[:-1] + bins[1:]) / 2.0
    for index in range(samples):
        mask = (radius >= bins[index]) & (radius < bins[index + 1])
        radial[index] = float(mtf[mask].mean()) if np.any(mask) else 0.0
    return frequencies / max(padded.shape), radial


def image_sharpness_score(image: np.ndarray) -> float:
    """Return variance of the Laplacian as a simple image-detail proxy."""
    arr = np.asarray(image, dtype=np.float32)
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    lap = (
        -4.0 * arr
        + np.roll(arr, 1, axis=0) + np.roll(arr, -1, axis=0)
        + np.roll(arr, 1, axis=1) + np.roll(arr, -1, axis=1)
    )
    return float(np.var(lap))
