# Changes in Python 2.1

This page records what changed between the Python port 2.0 (`Mixing_QMPD.py` of March 2020) and
version 2.1 (November 2026), and the effect of each change on the numbers. Read it before comparing
results produced by the two versions.

## Summary

| Change | Effect on results |
|---|---|
| Coordinates follow the C# / OpenCV convention and particle positions are absolute | Particle measures change for any target that is not a square at the origin (see below) |
| Variogram term is `(a - b)²` as in C# (was `a - b²`) | Variograms, mean length scales change |
| Multi-target, multi-image and calibration runs no longer crash | New capability, no effect on single-target runs |
| Explicit errors for invalid inputs | Clear `ValueError` instead of `IndexError`, `NameError`, `ZeroDivisionError`, ... |
| Pixel and particle loops vectorised with numpy | Same formulas; results identical up to floating-point rounding; 10 to 1000 times faster |
| `mixing_dim_*` return dictionaries | New capability (they used to print only) |
| Command-line interface and desktop application | New |
| Output images written to an output folder with descriptive names | `0.jpg` to `5.jpg` are no longer written to the working directory |

## Coordinates and particle positions

Version 2.0 mixed two conventions. `Rectangle.X` and `BitMap.Width` indexed the rows of the numpy array
(axis 0), while the particle positions stored from `keypoint.pt` were `(column, row)` relative to the
cropped target. The grid of quadrats, the transects and the hexagonal grid used the rectangle (absolute,
row first) against the particles (relative, column first). The two only coincided for a square target at
the origin.

Version 2.1 uses the convention of the C# original and of OpenCV everywhere:

- `Rectangle(X, Y, Width, Height)`: `X` column, `Y` row, `Width` columns, `Height` rows. This is the
  tuple returned by `cv2.selectROI`, so it can be passed directly.
- `Point(X, Y)`: `X` column, `Y` row, absolute coordinates of the full image. As in the C# code
  (`Blobdetectionimage`), a particle belongs to the target that contains it.
- `BitMap.Width` is the number of columns and `BitMap.Height` the number of rows.
- Concentration arrays keep the C# `[x, y]` layout: shape `(Width, Height)`, first index along the
  image width. The *horizontal* variogram runs along axis 0.

Consequence for the sample run: the 2.0 default `Rectangle(24, 82, 2700, 2180)` was interpreted as rows
24 to 2723 (clipped to 2207) and columns 82 to 2261. The same crop in 2.1 is `Rectangle(82, 24, 2180, 2184)`.
The 2.1 default of `MIQUOD_v1.py` is `Rectangle(24, 82, 2700, 2120)`, columns 24 to 2723 and rows 82 to
2201, which is what the numbers were meant to describe (the old height of 2180 does not fit the 2208-row
image).

## Variogram

C# `CalculateHorizontalvariograms` uses `Math.Pow(standdata[x, y] - standdata[x + dist, y], 2)`. The
2.0 port had `standard_data[x][y] - standard_data[x + dist][y] ** 2`, which squares only the second
term. 2.1 uses `(a - b)²`. The mean length scales, which use `γ(1) - γ(0)`, change accordingly. The Kotlin
port still has the 2.0 expression.

## Reference values of the sample image

`3colors_unmixed.png`, 2752 columns by 2208 rows, red particles, gray threshold 50.

### Particle data

| Run | Particles | Mean spacing | Max. striation | CoV | M | σ_fpp | i_dis | xg |
|---|---|---|---|---|---|---|---|---|
| 2.0 default (`Rectangle(24, 82, 2700, 2180)`, rows 24-2207, cols 82-2261) | 4956 | 22 | 273 | 1.1236 | 0 | 217.39 | 323.78 | 45.91 |
| 2.1, same crop (`Rectangle(82, 24, 2180, 2184)`) | 4956 | 22 | 273 | 0.9091 | 0.0909 | 193.85 | 336.10 | 39.77 |
| 2.1 default (`Rectangle(24, 82, 2700, 2120)`) | 5589 | 24 | 361 | 0.9095 | 0.0905 | 195.41 | 354.44 | 43.09 |

The detection, the mean spacing and the maximum striation thickness of the old crop are unchanged
because they do not depend on the offset. The quadrat concentrations and the PNN distribution of the old
crop differ from 2.0 because the particles are now compared with the grid in the same coordinates.

### Concentration data (2.1 default target, no calibration)

| σ | CoV | M | Cm | Horizontal length scale | Vertical length scale | Exposure |
|---|---|---|---|---|---|---|
| 0.148255 | 0.751249 | 0.248751 | 0.197344 | 23.714 | 23.7954 | 56005 |

Version 2.0 could not finish this run in reasonable time (the variogram loops in pure Python need billions
of iterations), so there is no 2.0 value to compare with. The concentration path of 2.1 takes about 30 s
on this target.

## Crashes fixed

| Scenario in 2.0 | Cause | 2.1 |
|---|---|---|
| Two targets on one image (concentration) | `store_concentration_data[i]` initialised as `[[]]` and indexed with the target number | Lists are built by appending |
| Calibration, same-size images | `images_with_references[img].__len__` without parentheses; `.pixel` on a numpy array; result stored at `[img]` instead of `[img][j]` | Fixed, vectorised |
| Calibration, different-size images | `.pixel` on a numpy array | Fixed, vectorised |
| Two targets or two images (particles) | `max_str_thickness[tgt_ind]` instead of `[img_ind]`; `trg_ind` never incremented in `blob_detection_image`; `store_part_pos[index] = [[]]` reset per target; `scl_segregation_ind[i] = ...` and `store_max_str_thick[i] = ...` overwrote the per-target lists; `pnn_distribution = [[]]` for one image only; `exposure_indexes[i]` lost the per-target values | Fixed |
| No particles detected | `im_with_keypoints2` only defined inside the keypoint loop; division by zero in `calculate_mean_spacing` | Warning at detection, `ValueError` with the target and the number of particles found |
| Image path wrong or script started from another folder | `cv2.imread` returned `None` and `BitMap` failed on `.shape` | `MIQUOD_v1.py` resolves the sample image next to itself and exits with the path; `BitMap(None)` raises a clear error |
| Greek letters in the result labels on a cp1252 console | `UnicodeEncodeError` | stdout reconfigured to UTF-8 |

## Behaviour kept on purpose

These differences from the C# original were reviewed and kept, because changing them changes published
numbers. They can be revisited later.

- The particle-data mixing index `M = 1 - CoV` is clamped at 0 (C# lets it go negative).
- `NormalizeCoV()` (normalisation of the CoV by the unmixed inlet condition) is not implemented. It needs
  the inlet assignment dialog of the C# application; the Python port has no inlet data. `need_for_inlets`
  in the concentration results tells when `CoV > 1`.
- The spacing of the hexagonal grid uses float division (`width / k`); C# uses integer division.
- `statistical_measures` initialises the maximum at 0, so `Cmax` is never negative (as in C#).
- `calculate_mean_spacing` has no lower bound; the C# application forces at least 3 px.
- Grayscale conversion uses OpenCV's BT.601 weights; C# (AForge) uses BT.709 weights. The particle
  detection of 2.x also adds an HSV colour mask and a 2x2 dilation/erosion that the C# version does not have.
- The maximum striation thickness scans every transect position and keeps the largest value (2.0
  behaviour); in the C# application the user clicks one transect.

## API changes

- `blob_detection_image(img_to_process, threshold_value, store_target_areas, color='red', detector=None,
  show=False, out_dir=None, verbose=True, stages_out=None)`: the colour mask is a parameter (it was
  hard-coded to red); windows are only shown with `show=True`; images are written only with `out_dir`.
- `initiate_max_str_thickness(..., horizontal=True)` returns the transect where the maximum was found.
- `mixing_dim_particle_data(..., verbose=True)` and `mixing_dim_concentration_data(..., verbose=True)`
  return dictionaries. The old positional arguments are still accepted; the pre-allocated result lists
  of the 2.0 script are ignored.
- New: `detect_particles_in_target`, `annotate_particles`, `draw_particles`, `show_detection_stages`,
  `run_particle_analysis`, `run_concentration_analysis`, `summarize_particle_results`,
  `summarize_concentration_results`, `to_jsonable`, `COLOR_RANGES`, `DEFAULT_DETECTOR_SETTINGS`,
  `Rectangle.right/bottom/area/contains/as_tuple`, `BitMap.check_rectangle`.
- `ideal_particle_position` still returns a list of `Point`; `pnn_method_distribution` returns numpy
  arrays.
- `BitMap.pixel(x, y, 'R')` now returns the red channel of a BGR image (it returned the blue one).
