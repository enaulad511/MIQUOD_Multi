# MIQUOD: Mixing Quantification from Images

MIQUOD quantifies mixing from images taken with machine-vision systems and reports measures of the
three dimensions of mixing:

- **reduction in the segregation of concentration**: standard deviation, coefficient of variation and
  mixing index of the concentration field;
- **reduction in the scale of segregation**: variograms and mean length scales (concentration data),
  maximum striation thickness and the point-particle (PNN) scale of segregation (particle data);
- **rate of change of segregation**: exposure.

Two kinds of data are processed separately. *Concentration data* is an array of concentrations derived
from the pixel intensities of a target area. *Particle data* is the set of particle positions detected in
a target area. The method is described in [docs/method.md](docs/method.md).

The same algorithm exists in three languages:

| Directory | Version | Description |
|---|---|---|
| [`C#/`](C%23/) | 1.0 | Original Windows application (WinForms, AForge). Reference implementation of the formulas. |
| [`Python/`](Python/) | 2.1 | Library (`Mixing_QMPD.py`), command-line tool (`MIQUOD_v1.py`) and desktop app (`miquod_gui.py`). |
| [`Kotlin/`](Kotlin/) | 2.0 | Android application (OpenCV). |

## Python quick start

Requirements: Python 3.11 or newer. The pinned dependencies are numpy, OpenCV, matplotlib and Pillow.

```powershell
# Windows (PowerShell)
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r Python\requirements.txt
cd Python
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r Python/requirements.txt
cd Python
```

Then:

```bash
python MIQUOD_v1.py                      # particle data of the sample image, results in ./miquod_output
python MIQUOD_v1.py --help               # all options
python miquod_gui.py                     # desktop application
```

### Command line

```bash
python MIQUOD_v1.py IMAGE --roi X Y WIDTH HEIGHT [--roi ...] --mode particles|concentration|both
                    [--threshold 0-255] [--color red|blue|green|yellow] [--dark]
                    [--out-dir DIR] [--no-images] [--show] [--select-roi] [--quiet]
```

`--roi` is the target area in the order printed by `cv2.selectROI`: `X` and `Y` are the column and row of
the top-left corner, then the width and height in pixels. `--select-roi` lets you draw the targets with the
mouse. The results go to `--out-dir` as `results.json`, the intermediate images of the particle detection
and the concentration arrays (`.npy`). See [docs/usage.md](docs/usage.md).

### Desktop application

`python miquod_gui.py [IMAGE]` opens a window with the same steps as the Android app: open the image, draw
the target areas, choose the data type and parameters, process, and read or export the results. The
*Detection* tab shows the intermediate images of the particle detection and the *Variograms* tab plots
the variograms of the concentration data.

### Library

```python
import cv2
import Mixing_QMPD as Mf

image = cv2.imread('3colors_unmixed.png')
target = Mf.Rectangle(24, 82, 2700, 2120)           # X=column, Y=row, width, height

particles = Mf.run_particle_analysis(image, [target], threshold_value=50, color='red')
print(particles['intensity_measures'][0][0])        # [σ, CoV, M, Cm, Cmax, Cmin, n, N]
print(particles['scale_segregation_indexes'][0][0]) # [σ_fpp, i_dis, xg]

concentration = Mf.run_concentration_analysis(image, [target])
print(concentration['intensity_measures'][0][0])    # [σ, CoV, M, Cm, Cmax, Cmin, n]
print(concentration['mean_length_scales'][0][0])    # Coordinate(X=horizontal, Y=vertical)
```

The step-by-step functions of the original flow (`blob_detection_image`, `initiate_max_str_thickness`,
`mixing_dim_particle_data`, `mixing_dim_concentration_data`, ...) are still available and support
several images, several targets per image and calibration with reference images. They are documented in
[docs/api.md](docs/api.md).

### Tests

```bash
pip install -r Python/requirements-dev.txt
cd Python
python -m pytest -q                       # fast tests on synthetic data
MIQUOD_RUN_SLOW=1 python -m pytest -q     # also the regression on the sample image
```

## Documentation

- [docs/usage.md](docs/usage.md): installation, command line, desktop application, library, outputs.
- [docs/method.md](docs/method.md): the measures and how they are computed.
- [docs/api.md](docs/api.md): reference of `Mixing_QMPD.py`, data structures and conventions.
- [docs/changes.md](docs/changes.md): what changed in Python 2.1 and the effect on the results.
- [docs/troubleshooting.md](docs/troubleshooting.md): error messages and how to fix them.

## C# (version 1.0)

The [C#](C%23/) source is the original application for concentration fields and the detection of white
or dark particles. It uses the **AForge.Imaging** and **AForge.Video** libraries. Only the two form
sources are kept in this repository.

## Kotlin (version 2.0)

The [Kotlin](Kotlin/MIQUOD2/app/src/main/java/com/poc_itesm/miquod2) sources are the main `.kt` files of
the Android application, which follows the same flow (image, targets, parameters, results).

## Citation

See [CITATION.cff](CITATION.cff).

## Authors

- [@enaulad511](https://github.com/enaulad511); [Edisson A. Naula Duchi, PhD](https://www.researchgate.net/profile/Edisson-Naula-Duchi)
- [Héctor Betancourt](https://mx.linkedin.com/in/hbetancourtc)

## Feedback

If you have any feedback or questions, please reach out at
[edisson.naulad@gmail.com](mailto:edisson.naulad@gmail.com).
