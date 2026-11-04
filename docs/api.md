# API reference: `Mixing_QMPD.py`

Version 2.1. Import it from the `Python/` folder (`import Mixing_QMPD as Mf`). The measures are described
in [method.md](method.md).

## Conventions

- **Coordinates** follow C# `System.Drawing` and OpenCV: `X` is a column, `Y` a row.
  `Rectangle(X, Y, Width, Height)` has `Width` columns and `Height` rows, the order `cv2.selectROI` returns.
  Particle positions are absolute coordinates of the full image.
- **Images** are numpy arrays as read by `cv2.imread` (rows, columns, BGR). `BitMap.Width` is the number of
  columns and `BitMap.Height` the number of rows.
- **Concentration arrays** are indexed `[x][y]`, so their shape is `(Width, Height)`, the transpose of
  the numpy crop. The horizontal variogram runs along axis 0.
- **Result containers** are nested lists indexed `[image][target]`. Images without concentration data
  (reference images used for calibration) hold an empty list.
- **Errors**: invalid inputs raise `ValueError` with a message that names the image, the target and the
  cause. Nothing is printed unless `verbose=True`; nothing opens a window unless `show=True`.

## Data structures

| Class | Description |
|---|---|
| `Point(X, Y)` | Column and row. `as_tuple()`. `Point(packed_int)` unpacks a C# 32-bit point. |
| `Rectangle(X, Y, Width, Height)` | Target area or transect. Properties `right`, `bottom` (last column/row inside), `area`; `contains(x, y)`, `as_tuple()`. Raises `ValueError` for a non-positive size. |
| `Coordinate(X, Y)` | Pair of values (mean length scales: `X` horizontal, `Y` vertical). |
| `RefImg(ImageIndex, Concentration)` | Reference image for calibration: index in the image list and known concentration in %. |
| `Transect(TargetArea, Rect, MeanSpacingOfPart)` | Kept for compatibility. |
| `ListPoints(x, y).list_points(n)` | Kept for compatibility. |
| `BitMap(img)` | Wraps a numpy image. `Width`, `Height`, `Dimension` (2 for gray, 3 for BGR), `Img`. `clone(rect)` returns the crop (a view) after `check_rectangle(rect)`, which raises `ValueError` when the rectangle is not inside the image. `pixel(x, y, layer)` returns one pixel (`layer` 'R', 'G' or 'B' for BGR images). `BitMap(None)` raises `ValueError`. |
| `BlobDetector(threshold, flag_area, limit_area, flag_circularity, min_cir, flag_convexity, convexity, flag_inertia, ratio_inertia, flag_color, split_touching=False)` | Wrapper of `cv2.SimpleBlobDetector`. `detect_blobs(img)` returns key points (from `split_touching_particles` when `split_touching` is set); `rectangles(points)` their bounding squares; `settings` holds the constructor arguments. |

Constants: `COLOR_RANGES` (list of HSV `(lower, upper)` bounds per named colour: red 0-10 and 170-179,
yellow 18-38, green 50-65, blue 85-130, all with saturation and value of at least 100), `COLOR_DRAW` (BGR
colour used to draw each named colour), `DEFAULT_DETECTOR_SETTINGS` (keyword arguments of the
`BlobDetector` used for particle counting), `__version__`.

## Colour specifications

A particle colour is given as a name of `COLOR_RANGES`, a dict `{'hue': h, 'tolerance': 10, 's_min': 100,
'v_min': 100}` (hue on OpenCV's 0-179 scale), one HSV `(lower, upper)` pair, or a list of pairs.

| Function | Description |
|---|---|
| `hsv_ranges_from_hue(hue, tolerance=10, s_min=100, v_min=100)` | HSV bounds for `hue ± tolerance`; two ranges when the interval wraps around 0 (the rule of the Android app). |
| `resolve_color(color)` | Any specification -> list of `(lower, upper)` arrays. Raises `ValueError` for an unknown name. |
| `color_mask(hsv, color)` | Binary mask (0/255) of the pixels of an HSV image inside any range of the colour. |
| `color_label(color)` | Text for a specification: `'red'`, `'hue 60 ±10'`, `'custom'`. |
| `color_for_drawing(color)` | BGR colour to draw particles of that specification. |

## High-level functions

### `run_particle_analysis(image_bgr, targets, threshold_value=50, color='red', detector=None, out_dir=None, show=False, verbose=False, horizontal=True, collect_stages=False, colors=None, area_limits=None, split_touching=None)`

Full particle pipeline for one image and a list of `Rectangle`. `color` applies to every target; `colors`
gives one specification per target. `area_limits` gives one `(min_area, max_area)` pair per target (a
detector with those limits and the other settings of `detector` is built for each target) and
`split_touching` a bool, or one per target, to count touching particles one by one. Returns the
dictionary of `mixing_dim_particle_data` plus `particle_positions`, `blob_rectangles`, `mean_spacing`,
`transects`, `targets`, `colors` (label per target), `color_ranges`, `area_limits`, `split_touching` and,
with `collect_stages`, `detection_stages`. Raises `ValueError` when a target is outside the image or the
number of colours, limits or flags does not match, and `NotEnoughParticles` (a `ValueError` subclass with
the attributes `positions`, `rectangles` and `stages` holding what was detected) when a target has fewer
than four particles.

### Particle size helpers

| Function | Description |
|---|---|
| `split_touching_particles(binary, min_area=1, max_area=None)` | Key points of round particles that touch or overlap, from the binary image given to the blob detector (particles black on white): one peak of the distance transform per particle, merged within the radius of the smallest accepted particle; the key point size is the inscribed diameter and particles with estimated area `π r²` outside the limits are dropped. |
| `detectors_for_area_limits(area_limits, base=None, split_touching=None)` | One `BlobDetector` per `(min, max)` pair with the other settings of `base` (a settings dict). |
| `measure_blob_area_at(image_bgr, x, y, color, window=400)` | Estimated area (`π r²`, `r` from the distance transform) of the particle of that colour under pixel `(x, y)`, 0 when the pixel is outside the colour mask. Used by the application's right click. |

### `run_particle_analysis_by_color(image_bgr, targets, colors, threshold_value=50, detector=None, out_dir=None, show=False, verbose=False, horizontal=True, collect_stages=False)`

`run_particle_analysis` once per colour (a list of names or a dict `label -> specification`), as the
Android application does. Returns `label -> results`; a colour with too few particles gets an entry with
`error` and the detected `particle_positions`, `blob_rectangles` and `detection_stages`. Images go to
`out_dir/<label>`.

### `run_concentration_analysis(image_bgr, targets, dark_areas_higher=False, verbose=False, collect_stages=False)`

Full concentration pipeline (no calibration) for one image. Returns the dictionary of
`mixing_dim_concentration_data` plus `targets` and, with `collect_stages`, `concentration_stages`
(the dictionaries of `concentration_stages` per target).

### Images

| Function | Description |
|---|---|
| `montage_images(images, tile_width=480, columns=3, labels=True)` | One labelled BGR sheet with the named images (gray or BGR) as tiles of `tile_width` pixels, `columns` per row. Used for the `*_sequence.jpg` files. |
| `concentration_to_image(concentration, colormap=cv2.COLORMAP_JET)` | Colour map of a concentration array (`[x][y]`), returned as a BGR image oriented like the crop and scaled between the array's minimum and maximum. |
| `concentration_stages(image_bgr, rect, concentration)` | Dict `crop`, `filtered` (median-filtered gray crop), `concentration` (colour map) of one target. |

### `to_jsonable(obj)`

Converts results (numpy arrays and scalars, `Point`, `Coordinate`, `Rectangle`, `RefImg`, nested lists and
dictionaries) into values accepted by `json.dump`.

## Particle detection

| Function | Description |
|---|---|
| `detect_particles_in_target(crop_bgr, threshold_value, color='red', detector=None, hsv_range=None)` | Detection pipeline of one crop for one colour specification. Returns `(key_points, stages)`; `stages` is a dict of the intermediate images `crop`, `mask`, `color`, `gray`, `binary`, `particles`. |
| `blob_detection_image(img_to_process, threshold_value, store_target_areas, color='red', detector=None, show=False, out_dir=None, verbose=True, stages_out=None, colors=None)` | Detection of every target of every `BitMap`; `colors[image][target]` gives each target its own colour. Returns `(store_part_pos, store_blob_rectangles)` indexed `[image][target]` with absolute positions. Writes the stages to `out_dir` as `img{i}_target{j}_{k}_{stage}.jpg` plus a `img{i}_target{j}_sequence.jpg` sheet; appends them to `stages_out` when given. Warns when a target has no particle. |
| `annotate_particles(image_bgr, key_points, color=(255, 255, 255), thickness=4)` | Copy of the crop with a circle around every key point. |
| `draw_particles(image_bgr, points, radius=4, color=(255, 255, 255), thickness=2, rect=None)` | Copy of the full image with the absolute positions and, optionally, the target drawn. |
| `show_detection_stages(stages, title='')` | Shows the stages with matplotlib (blocking). |

## Particle measures

| Function | Description |
|---|---|
| `calculate_mean_spacing(img_ind, trg, img_to_process, store_part_pos)` | Twice the mean truncated nearest-neighbour distance (int). Needs at least two particles. |
| `initiate_max_str_thickness(img_to_process, store_part_pos, store_trg_areas, horizontal=True)` | Mean spacing, best transect and maximum striation thickness of every target: `(m_part_spacing, defined_transects, max_str_thickness)`. |
| `calculate_max_str_thickness(img_ind, trg_ind, m_part_spacing, store_part_pos, defined_transects, store_trg_areas)` | Maximum striation thickness inside one given transect (horizontal when its height differs from the target height). |
| `get_concentration_from_particles(store_target_areas, loaded_image_info, store_part_positions, max_striation_thickness)` | Quadrat concentration arrays, shape `(cols, rows)`. Raises when the striation thickness is larger than the target. |
| `statistical_measures_particles(data, target_area, num_of_particles)` | `[μ, σ, min, max, n]` with `μ = N / area`. |
| `segregation_intensity_ifp(store_con_particle_data, store_part_positions, store_trg_areas)` | `[σ, CoV, M, Cm, Cmax, Cmin, n, N]` per target; `M` clamped at 0. |
| `maximum_striation_thickness(max_str_thick)` | Copy of the per-target values (compatibility). |
| `ideal_particle_position(tgt_area, num_of_part)` | Hexagonal grid of `k*k` `Point` (float coordinates), `k = int(sqrt(N))`. |
| `pnn_method_distribution(store_trg_areas, store_part_pos)` | Distance from every grid point to the closest particle, numpy array per target. |
| `scale_segregation_for_particles(store_trg_areas, store_part_pos, pnn_distribution)` | `[σ_fpp, i_dis, xg]` per target. Needs at least four particles. |
| `mixing_dim_particle_data(store_trg_areas, loaded_img_info, store_part_pos, max_striation_thick, verbose=True)` | Runs the four steps above and returns a dictionary with `particle_concentration`, `intensity_measures`, `max_striation_thickness`, `pnn_distribution`, `scale_segregation_indexes`, `pnn_parameters`. |
| `summarize_particle_results(results, loaded_img_info=None)` | Text summary of that dictionary. |

## Concentration measures

| Function | Description |
|---|---|
| `filter_image(bitmap)` | 5 x 5 median filter and grayscale; returns a `BitMap`. |
| `get_intensity_max_min(filtered_image)` | `Point(X=max, Y=min)` gray value. |
| `get_mean_intensity_value(img_index, target, img_to_process, store_target_areas)` | Mean filtered gray value of a target. |
| `concentration_matrix(img_to_process, store_trg_areas, store_concentration_data=None, images_with_references=None, loaded_image_info=None, dark_checkbox=False)` | Concentration arrays per target, normalised or calibrated (see [method.md](method.md)). Images without references get an empty list. Raises for a target outside the image or an image with uniform intensity. |
| `statistical_measures(data)` | `[μ, σ (population), min, max (never below 0), n]`. |
| `segregation_intensity_index_factors(intensity_measures, img_to_process, store_con_data)` | `[σ, CoV, M, Cm, Cmax, Cmin, n]` per target. First argument ignored (compatibility). |
| `standarized_array(image_index, target, store_con_data, intensity_measures)` | `(c - μ) / σ`; raises when `σ = 0`. |
| `horizontal_var_diagram(hor_var_diagrams, store_con_data, img_to_process, intensity_measures)` | `γx(h)`, `h = 0 .. Width // 2`, per target. First argument ignored. |
| `vertical_var_diagram(ver_var_diagrams, img_to_process, store_con_data, intensity_measures)` | `γy(h)`, `h = 0 .. Height // 2`, per target. First argument ignored. |
| `mean_length_scales(img_to_process, store_concentration_data, intensity_measures, hor_var_diagrams, ver_var_diagrams)` | `Coordinate(X=horizontal, Y=vertical)` per target; infinite with a warning when a variogram has zero slope. |
| `calculate_exposure_indexes(img_to_process, store_concentration_data)` | Exposure per target. |
| `get_intensity_array(image_index, target_area, img_to_process2, store_target_areas2)` | Filtered gray values of a target, `[x][y]`. |
| `full_image_data_array(image_index, img_to_process2)` | Filtered gray values of the whole image, `[x][y]`. |
| `mixing_dim_concentration_data(img_to_process, store_target_areas, store_concentration_data=None, images_with_references=None, loaded_img_info=None, dark_checkbox=False, intensity_measures=None, hor_var_diagrams=None, ver_var_diagrams=None, verbose=True)` | Runs the whole concentration flow and returns a dictionary with `concentration_data`, `intensity_measures`, `horizontal_variograms`, `vertical_variograms`, `mean_length_scales`, `exposure_indexes`, `need_for_inlets`. The pre-allocated lists of the 2.0 script are accepted and ignored. |
| `summarize_concentration_results(results, loaded_img_info=None)` | Text summary of that dictionary. |

## Calibration rules

`concentration_matrix` calibrates only when every entry of `images_with_references` has zero or at least
two references, no entry has exactly one, and the number of images involved (references plus calibrated
images) is at least the number of images. Otherwise the intensities are normalised. Calibration is
"complex" (per pixel) when every image has the same size and the same target sizes as its references, and
"simple" (per target mean) otherwise. A single `RefImg(0, 1)` per image, as in the sample script,
therefore selects the normalisation.

## Error conditions

| Condition | Exception |
|---|---|
| `BitMap(None)` (image not read) | `ValueError: BitMap received None ...` |
| Target not inside the image | `ValueError: target area Rectangle(...) lies outside the image (...)` |
| Fewer than 2 particles (mean spacing) / fewer than 4 (scale of segregation) | `ValueError` naming the target and the count |
| Fewer than 4 particles in `run_particle_analysis` | `NotEnoughParticles` (subclass of `ValueError`) carrying the detected positions and stage images |
| Maximum striation thickness larger than the target | `ValueError: ... no quadrat fits` |
| Uniform image (cannot normalise) or uniform target (`σ = 0`) | `ValueError` |
| Mean concentration zero with non-zero deviation | `ValueError` |
| Unknown colour name | `ValueError: unknown colour ...` |
| No particles in a target during detection | `UserWarning` (the error comes later if that target is processed) |
| Variogram with zero slope | `UserWarning`, infinite length scale |
