# Usage

This page covers the Python implementation: installation, the command-line tool, the desktop
application, the library and the files they write. The measures themselves are explained in
[method.md](method.md) and the functions in [api.md](api.md).

## Installation

Python 3.11 or newer is required (the code is tested with 3.13). Create a virtual environment in the
repository root and install the pinned dependencies:

```powershell
# Windows (PowerShell)
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r Python\requirements.txt
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r Python/requirements.txt
```

The desktop application uses `tkinter`, which ships with the python.org installers for Windows and
macOS. On Debian/Ubuntu install it with `sudo apt install python3-tk`.

PyCharm: select the interpreter `.venv\Scripts\python.exe` in *Settings > Project > Python Interpreter*
(*Add Interpreter > Existing*). PyCharm usually offers it automatically when it finds the `.venv` folder.

## Command line: `MIQUOD_v1.py`

Run it from the `Python/` folder (or with its full path; it finds the sample image next to itself).

```
python MIQUOD_v1.py [IMAGE] [--roi X Y WIDTH HEIGHT]... [--select-roi]
                    [--mode {particles,concentration,both}] [--threshold 0-255]
                    [--color {blue,green,red,yellow}] [--dark]
                    [--out-dir DIR] [--no-images] [--show] [--quiet] [--version]
```

| Option | Meaning | Default |
|---|---|---|
| `IMAGE` | Image to analyse (any format OpenCV reads). | `3colors_unmixed.png` next to the script |
| `--roi X Y WIDTH HEIGHT` | Target area; repeat the option for several targets. `X` and `Y` are the column and row of the top-left corner, in pixels. Same order as `cv2.selectROI`. | Sample target `24 82 2700 2120` for the sample image; the whole image otherwise |
| `--select-roi` | Draw the targets with the mouse. ENTER or SPACE confirms a rectangle, ESC finishes. The chosen values are printed so they can be reused with `--roi`. | off |
| `--mode` | `particles` (blob detection, striation thickness, PNN), `concentration` (intensity normalisation, variograms, length scales, exposure) or `both`. | `particles` |
| `--threshold` | Gray threshold applied to the colour-masked image before blob detection. Lower values keep fainter particles. | `50` |
| `--color` | Dye colour of the particles; selects the HSV range of the mask (`COLOR_RANGES` in the library). | `red` |
| `--dark` | Concentration data: dark pixels carry the higher concentration (`c = 1 - normalised intensity`). | off |
| `--out-dir DIR` | Output folder, created if needed. | `./miquod_output` |
| `--no-images` | Do not write the intermediate images. | off |
| `--show` | Display the intermediate images of each target with matplotlib (the run pauses until the window is closed). | off |
| `--quiet` | Print only errors and the output location. | off |

Examples:

```bash
python MIQUOD_v1.py
python MIQUOD_v1.py sample.png --roi 24 82 2700 2120 --mode both
python MIQUOD_v1.py sample.png --select-roi --mode concentration --dark
python MIQUOD_v1.py sample.png --roi 0 0 500 500 --roi 600 0 500 500 --color blue --threshold 60 --show
python MIQUOD_v1.py sample.png --roi 0 0 500 500 --quiet --no-images --out-dir results/run1
```

The tool exits with a message (no traceback) when the image cannot be read, a target lies outside the
image, fewer than four particles are detected, the maximum striation thickness does not fit in the
target, or an image has uniform intensity. See [troubleshooting.md](troubleshooting.md).

### Output files

Inside `--out-dir`:

| File | Content |
|---|---|
| `results.json` | Everything below, plus the image path and size, the targets, the settings and the elapsed time. |
| `img{i}_target{j}_1_crop.jpg` ... `_6_particles.jpg` | Particle detection stages of image `i`, target `j`: crop, HSV mask, colour-masked crop, grayscale, binary image given to the blob detector, crop with the detected particles circled. |
| `particles_full_image.jpg` | The whole image with every target and its particles drawn. |
| `concentration_target{j}.npy` | Concentration array of target `j`, shape `(Width, Height)`, indexed `[x][y]`. Load with `numpy.load`. |

`results.json` keys (lists are indexed `[image][target]`; the command line processes one image, so the
image index is always 0):

- `particles`: `particle_positions` (absolute `{X, Y}` = column, row), `blob_rectangles`, `mean_spacing`,
  `transects` (the transect where the maximum striation was found), `max_striation_thickness`,
  `particle_concentration` (quadrat concentrations), `intensity_measures` (`[σ, CoV, M, Cm, Cmax, Cmin, n, N]`),
  `pnn_distribution`, `pnn_parameters` (`xr, xg, dx, dy, k, xs, var_fpp, xi_mean, m`),
  `scale_segregation_indexes` (`[σ_fpp, i_dis, xg]`).
- `concentration`: `intensity_measures` (`[σ, CoV, M, Cm, Cmax, Cmin, n]`), `horizontal_variograms`,
  `vertical_variograms` (`γ(h)` for `h = 0 .. L/2`), `mean_length_scales` (`{X: horizontal, Y: vertical}`),
  `exposure_indexes`, `need_for_inlets`, `concentration_data_files`.

## Desktop application: `miquod_gui.py`

```bash
python miquod_gui.py            # or: python miquod_gui.py image.png
```

The window follows the flow of the Android application:

1. **Image**: *Open image...* loads a file. Its name and size appear below the button.
2. **Target areas**: click and drag on the image to draw a target. Targets can also be typed (X, Y, width,
   height) and added, set to the whole image, removed or cleared. The selected target is highlighted and
   its values are shown in the entry boxes.
3. **Parameters**: data type (particles, concentration or both), particle colour, gray threshold, blob
   area limits and the *dark areas = higher concentration* option.
4. **Process**: runs the analysis in the background; the status line reports progress and errors.
5. **Results**: *Export results (JSON)...* writes the same content as the command line (`results.json` and
   one `.npy` per target for the concentration arrays, next to the JSON file). *Save annotated image...*
   writes the image with the targets and particles drawn.

Tabs on the right:

- **Image**: the image with the targets; after a particle run, the detected particles are drawn on it.
- **Results**: the measures of every target, the settings used and any warning.
- **Detection**: the intermediate images of the particle detection, per target and stage.
- **Variograms**: horizontal and vertical variograms of every target (concentration data).

## Library: `Mixing_QMPD.py`

### One image, one or more targets

```python
import cv2
import Mixing_QMPD as Mf

image = cv2.imread('3colors_unmixed.png')
targets = [Mf.Rectangle(24, 82, 1300, 2120), Mf.Rectangle(1424, 82, 1300, 2120)]

p = Mf.run_particle_analysis(image, targets, threshold_value=50, color='red', out_dir='out', verbose=True)
c = Mf.run_concentration_analysis(image, targets, dark_areas_higher=False, verbose=True)

for j, target in enumerate(targets):
    sigma, cov, m, cm, cmax, cmin, n, big_n = p['intensity_measures'][0][j]
    sigma_fpp, i_dis, xg = p['scale_segregation_indexes'][0][j]
    length = c['mean_length_scales'][0][j]          # .X horizontal, .Y vertical
    exposure = c['exposure_indexes'][0][j]
```

`run_particle_analysis` accepts a custom `detector=Mf.BlobDetector(...)` (see `DEFAULT_DETECTOR_SETTINGS`)
and `collect_stages=True` to get the intermediate images in `detection_stages`.

### Several images, calibration with reference images

The step-by-step functions take lists indexed `[image][target]`. Calibration needs at least two
reference images of known concentration (in %) for every image to calibrate; the reference images are
part of the image list and have an empty reference list themselves.

```python
images = [Mf.BitMap(cv2.imread(name)) for name in ('mixed.png', 'ref_0pct.png', 'ref_100pct.png')]
targets = [[Mf.Rectangle(10, 10, 400, 300)]] * 3           # same target in every image
references = [[Mf.RefImg(1, 0), Mf.RefImg(2, 100)], [], []]  # image 0 is calibrated with images 1 and 2
names = ['mixed', 'ref 0 %', 'ref 100 %']

results = Mf.mixing_dim_concentration_data(images, targets, None, references, names, dark_checkbox=False)
results['intensity_measures'][0][0]   # the reference images (1 and 2) have empty result lists
```

With a single `RefImg` per image, as in `[[Mf.RefImg(0, 1)]]`, no calibration is performed and the
intensities are normalised between the minimum and maximum of each image.

The particle flow in steps:

```python
positions, rectangles = Mf.blob_detection_image(images, 50, targets, color='red')
spacing, transects, max_striation = Mf.initiate_max_str_thickness(images, positions, targets)
results = Mf.mixing_dim_particle_data(targets, names, positions, max_striation)
```

### Saving results

`Mf.to_jsonable(results)` turns the dictionaries into plain lists and numbers for `json.dump`. Remove the
`concentration_data` (and `detection_stages`) entries first, or save them with `numpy.save`: they are large.

## Running without a display

Nothing opens a window unless `--show`, `--select-roi` or `show=True` is used, so the command line and the
library run unattended (for example on a server). Set the environment variable `PYTHONUTF8=1` if the
console cannot print the Greek letters of the labels; `MIQUOD_v1.py` already switches its output to UTF-8.

## Performance

On the sample image (2752 x 2208 px, 5589 particles) the particle path takes about 2 s and the
concentration path about 30 s, most of it in the variograms (one pass over the target per lag, up to
half the target size). Smaller targets are proportionally faster. Memory use is about ten times the
size of the concentration array in double precision.

## Tests

```bash
pip install -r Python/requirements-dev.txt
cd Python
python -m pytest -q
MIQUOD_RUN_SLOW=1 python -m pytest -q      # adds the regression on the sample image
```

The tests compare the vectorised functions with literal transcriptions of the C# loops on random
inputs, exercise multi-target, multi-image and calibration runs on synthetic images, and check the error
messages. The slow test checks the reference values listed in [changes.md](changes.md).
