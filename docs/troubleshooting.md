# Troubleshooting

## Installation

**`ModuleNotFoundError: No module named 'cv2'` (or numpy, matplotlib, PIL)**
The virtual environment is not active or the requirements are not installed. Activate `.venv` and run
`pip install -r Python/requirements.txt`. In PyCharm, select `.venv\Scripts\python.exe` as the project
interpreter.

**`ModuleNotFoundError: No module named 'tkinter'` or `_tkinter`**
The desktop application needs Tk. On Debian/Ubuntu: `sudo apt install python3-tk`. The python.org
installers for Windows and macOS include it; check the *tcl/tk* option when installing Python.

**`pip` cannot find a wheel for opencv-python or numpy**
The pinned versions need Python 3.11 or newer. Create the environment with a supported interpreter
(`py -3.13 -m venv .venv` on Windows).

## Running

**`Could not read the image: ...`** (command line) or
**`ValueError: BitMap received None: the image could not be read`** (library)
`cv2.imread` returned nothing: the path is wrong, relative to another working directory, or the format is
not supported. Use an absolute path. `MIQUOD_v1.py` finds the sample image next to itself whatever the
working directory.

**`ValueError: target area Rectangle(...) lies outside the image (W columns x H rows): columns a-b, rows c-d`**
The target does not fit. `Rectangle` is `(X, Y, Width, Height)` with `X` the column and `Y` the row of the
top-left corner, exactly what `cv2.selectROI` returns. If the values were taken from a version 2.0 script,
remember that 2.0 interpreted `X` as the row; swap `X`/`Y` and `Width`/`Height`
(see [changes.md](changes.md)).

**`Target j (...): only n particles detected; at least 4 are needed`**
or the warning **`no particles detected`**
The colour mask or the threshold leaves nothing to detect. Check the `img*_target*_2_mask.jpg` and
`_5_binary.jpg` images in the output folder (or the *Detection* tab of the application):

- an empty mask: the particles are not in the HSV range of the target's colour. The named colours cover
  hue 0-10 and 170-179 (red), 18-38 (yellow), 50-65 (green) and 85-130 (blue) with saturation and value
  of at least 100. In the application, hover over a particle to read its H, S and V, and right-click it to
  use its hue as the custom colour of the target; on the command line use `--color hue:H`. Lower the
  custom S or V minimum for pale or dim dyes;
- a mask with particles but an empty binary image: lower `--threshold`;
- blobs too large or too small: change the blob area limits (`DEFAULT_DETECTOR_SETTINGS['limit_area']`,
  or the *Blob area* fields of the application).

In the application this is reported as a warning, not an error: the Sequence tab shows the images of the
failed detection and the concentration results of the same run are kept. In the library the exception is
`NotEnoughParticles`, which carries the detected positions and the stage images.

**`the maximum striation thickness (N px) is larger than the target (...); no quadrat fits`**
The particles form one continuous striation across the whole target (every gap between neighbouring
particles is smaller than the mean spacing), so no quadrat of that size fits. Use a larger target, or a
target that contains segregated regions.

**`has a uniform intensity; it cannot be normalised`** or **`the concentration is uniform (σ = 0)`**
All pixels have the same gray value after the median filter, so there is nothing to measure.

**`UserWarning: ... variogram slope at h=1 is zero, the ... mean length scale is infinite`**
The concentration does not change along that direction (perfect stripes). The other direction is still
computed.

**`UnicodeEncodeError: 'charmap' codec can't encode character 'σ'`**
The console cannot print the Greek letters of the labels. `MIQUOD_v1.py` switches its output to UTF-8;
for other scripts set the environment variable `PYTHONUTF8=1` or call
`sys.stdout.reconfigure(encoding='utf-8')`.

**The concentration run is slow**
The variograms need one pass over the target per lag, up to half the target size: about 30 s for a
2700 x 2120 target. Use a smaller target or only the particle mode when the variograms are not needed.

**The run hangs**
`--show`, `--select-roi` and `show=True` open windows and wait for them to be closed. Do not use them in
unattended runs.

## Results

**The numbers differ from a version 2.0 run**
Expected: 2.1 fixes the coordinate convention and the variogram formula. [changes.md](changes.md) lists
the effect of each change and the reference values of the sample image for both versions.

**`M` is 0 for particle data although `CoV` is larger than 1**
The particle-data mixing index is clamped at 0. `CoV > 1` means the sample is more segregated than a
random distribution; see the note on inlets in [method.md](method.md).

**The variograms of the application are empty**
They are only computed for concentration data; choose *Concentration* or *Both* before processing.
