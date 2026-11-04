# Method

MIQUOD describes mixing with the three dimensions proposed by Kukukova, Aubin and Kresta: the
*intensity* of segregation (how far the local concentration is from the mean), the *scale* of
segregation (how large the segregated regions are) and the *exposure* (the potential for the
segregation to decrease). The measures are computed on rectangular target areas of an image, from
either of two data types.

All formulas below are the ones implemented in `Mixing_QMPD.py` (version 2.1), which follow the C#
original (MIQUOD 1.0). Coordinates: `X` is a column, `Y` a row; a target is `Rectangle(X, Y, W, H)`.

## Particle data

Particle data is the list of positions of the dyed particles detected inside a target.

### 1. Detection

For each target (function `detect_particles_in_target`):

1. The target is cropped and converted to HSV.
2. A mask keeps the pixels inside the HSV range of the dye colour (`COLOR_RANGES`; red is H 0-10,
   S and V 100-255 on OpenCV's 0-180 / 0-255 scales).
3. The masked crop is converted to grayscale, dilated and eroded with a 2 x 2 kernel (removes isolated
   pixels), and binarised with an inverse threshold at the gray value `T` (`--threshold`): particles
   become black on a white background.
4. `cv2.SimpleBlobDetector` finds the dark blobs (internal thresholds 150-255, area between 1 and 50 px by
   default, no circularity, convexity, inertia or colour filter). The area limits are set per target.
   With the *split touching particles* option the blobs are instead the peaks of the distance transform
   of the particle pixels, one per round particle even when particles touch or overlap, with the same
   area limits applied to `π r²`.
5. Each blob centre `(u, v)` (relative to the crop) is stored as the absolute position
   `Point(X + u, Y + v)`.

### 2. Mean particle spacing

For every particle `i`, `d_i` is the distance to its nearest other particle, truncated to an integer and
bounded by the image diagonal. The mean spacing is

    s = 2 * floor( (1/N) * sum_i d_i )

(`calculate_mean_spacing`). It is the thickness of the transects and the gap that separates two striations.

### 3. Maximum striation thickness

A transect is a horizontal band of the target with thickness `s` (rows `j` to `j + s - 1`). It is slid over
every starting row `j` from `Y` to `Y + H - 2 - s` (`initiate_max_str_thickness`). Inside a transect the
particle columns are sorted; consecutive particles whose gap is at most `s` belong to the same striation
and the thickness of a striation is the distance between its first and last particle. The maximum
striation thickness `MST` is the largest thickness over all striations and all transects, and never less
than `s` (`calculate_max_str_thickness`). The transect where the maximum occurred is reported.

### 4. Quadrat concentration

The target is divided into square quadrats of side `MST`: `col = floor(W / MST)` columns and
`row = floor(H / MST)` rows, centred in the target (margins `(W - col*MST)/2` and `(H - row*MST)/2`).
The concentration of a quadrat is the number of particles it contains divided by its area
(`get_concentration_from_particles`). The result is an array of shape `(col, row)`.

### 5. Intensity of segregation

With `N` particles and the quadrat concentrations `c_q` (`segregation_intensity_ifp`):

    Cm  = N / (W * H)                              mean concentration
    σ   = sqrt( (1/n) * sum_q (c_q - Cm)^2 )       n = number of quadrats
    CoV = σ / Cm                                   coefficient of variation
    M   = max(0, 1 - CoV)                          mixing index
    Cmax, Cmin                                     largest and smallest quadrat concentration

`M` is clamped at 0 in the Python versions (the C# original reports negative values, which mean that the
unmixed condition must be defined by inlets).

### 6. Ideal hexagonal grid

With `k = floor(sqrt(N))`, the ideal positions of `k*k` particles form a hexagonal grid inside the target
(`ideal_particle_position`): spacing `dx = W / k`, `dy = H / k`, rows `n = 0 .. k-1` at
`y = Y0 + n*dy`, columns `m = 0 .. k-1` at `x = X0 + m*dx` on even rows and `x = X0 + dx/2 + m*dx` on odd
rows, where `X0` and `Y0` centre the grid in the target:

    X0 = X + ceil( (W - ceil((dx - 1)/2) - (k - 1)*dx) / 2 )
    Y0 = Y + ceil( (H - dy*k) / 2 ) + ceil(dy / 2)

### 7. Point-particle nearest-neighbour (PNN) distribution

For every grid point `i`, `ξ_i` is the distance to the closest detected particle, bounded by the target
diagonal (`pnn_method_distribution`). `m = k*k` values.

### 8. Scale of segregation

(`scale_segregation_for_particles`)

    xg      = (dx + 2*sqrt(dx^2 + dy^2)) / 3        spatial resolution of the grid
    xr      = xg / 2                                 filter radius
    var_fpp = sum_{ξ_i >= xr} (ξ_i - xr)^2 / (m - 1)
    σ_fpp   = sqrt(var_fpp)                          filtered point-particle deviation
    i_dis   = var_fpp / mean(ξ)                      index of dispersion

A perfectly dispersed sample gives `ξ_i < xr` everywhere and `σ_fpp = 0`.

## Concentration data

Concentration data is an array with one concentration per pixel of the target.

### 1. Filtering

The image is smoothed with a 5 x 5 median filter and converted to grayscale (`filter_image`). The crop of
each target is taken from this filtered image.

### 2. Concentration from intensity

Without calibration (`concentration_matrix`), with `Imin` and `Imax` the minimum and maximum gray value of
the whole filtered image:

    c = (I - Imin) / (Imax - Imin)                 bright pixels = high concentration
    c = 1 - (I - Imin) / (Imax - Imin)             with the "dark areas" option

With calibration, every image to analyse has at least two reference images of known concentration
(`RefImg(image_index, concentration_in_percent)`). The concentration `c` of a pixel is obtained from a
least-squares line `c = b*I + a` fitted on the references:

- *complex* calibration, when all images and targets have the same size: the line is fitted pixel by
  pixel, with the intensity of the same pixel in every reference image;
- *simple* calibration otherwise: one line per target, with the mean intensity of the target in every
  reference image.

When the references do not vary (zero variance of intensity or of concentration), the mean reference
concentration is used.

### 3. Intensity of segregation

(`segregation_intensity_index_factors`) with `n` pixels of concentration `c_p`:

    Cm  = (1/n) * sum_p c_p
    σ   = sqrt( (1/n) * sum_p (c_p - Cm)^2 )
    CoV = σ / Cm
    M   = 1 - CoV
    Cmax, Cmin

`M < 0` (`CoV > 1`) means that the unmixed condition should be defined by inlet targets to normalise the
CoV; the result dictionary flags it with `need_for_inlets`. This normalisation (`NormalizeCoV` in C#) is
not implemented in Python.

### 4. Variograms

The concentration is standardised, `z = (c - Cm) / σ` (`standarized_array`), and the semivariogram is
computed along the width (horizontal, `horizontal_var_diagram`) and along the height (vertical,
`vertical_var_diagram`) for lags `h = 1 .. floor(L/2)`, `L` being the target width or height:

    γ(h) = sum_pairs (z(s) - z(s + h))^2 / (2 * N(h))         γ(0) = 0

where the sum runs over all pairs of pixels separated by `h` in that direction and `N(h)` is their number.

### 5. Mean length scales

(`mean_length_scales`) with `p = Cm` and the slope of the variogram at the origin approximated by
`γ(1) - γ(0)`:

    L_horizontal = p / (γx(1) - γx(0))
    L_vertical   = p / (γy(1) - γy(0))

in pixels. A direction with no variation (zero slope) gives an infinite length scale and a warning.

### 6. Exposure

(`calculate_exposure_indexes`)

    E = sum_p sum_{q in N4(p)} (1/2) * |c_p - c_q|

over the four neighbours of every pixel, which is the sum of the absolute concentration difference of
every pair of adjacent pixels.

## Result containers

Every function that works on several images and targets returns lists indexed `[image][target]`;
`run_particle_analysis` and `run_concentration_analysis` process one image, so the first index is 0.
`intensity_measures` holds `[σ, CoV, M, Cm, Cmax, Cmin, n]` (plus `N` for particle data);
`scale_segregation_indexes` holds `[σ_fpp, i_dis, xg]`; `mean_length_scales` holds
`Coordinate(X=horizontal, Y=vertical)`.

## References

The code cites the following work; please check the bibliographic details before quoting them.

- A. Kukukova, J. Aubin, S. M. Kresta, *A new definition of mixing and segregation: Three dimensions of a
  key process variable*, Chemical Engineering Research and Design 87 (2009) 633-647. Three dimensions of
  mixing; exposure.
- A. Kukukova, J. Aubin, S. M. Kresta, *Measuring the scale of segregation in mixing data*, The Canadian
  Journal of Chemical Engineering 89 (2011) 1122-1138. Variograms, mean length scales, maximum striation
  thickness and the point-particle (PNN) measures of the scale of segregation.
- H. Betancourt Cervantes, *MIQUOD v1.0, Mixing Quantification of Devices Software*, 2017. Original C#
  implementation.
