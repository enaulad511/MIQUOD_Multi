
# Sofware for Mixing Characterization (MIQUOD)

The software comprises among other things two libraries. The first library, **AForge.Imaging**, incorporates the image processing routines and filters, and the other library, **AForge.Video**. MIQUOD is focused on quantifying mixing using machine vision systems and report measures directly related to the reduction in the segregation of concentration, the reduction in the scale of segregation, and the potential of change in mixing performance. The concentration data type is an array of concentrations associated with pixels intensities and the particle tracking data is a matrix of particle positions within a target area. MIQUOD process each type of data separately. The source code is in three languages.

## C# (Version 1.0)
[C#](https://github.com/enaulad511/MIQUOD_Multi/tree/main/C%23) source code is the basic version for concentracion fields and particle detection of white particles o dark particles.
## Python (Version 2.1)
The Python implementation has a library ([Mixing_QMPD.py](Python/Mixing_QMPD.py)), a command-line tool ([MIQUOD_v1.py](Python/MIQUOD_v1.py)) and a desktop application ([miquod_gui.py](Python/miquod_gui.py)). The complete usage (installation, command line, desktop application, library and output files) is in [docs/usage.md](docs/usage.md). 

### Quick start
```bash
python -m venv .venv                      # Windows: py -3.13 -m venv .venv ; .venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -r Python/requirements.txt
cd Python
python MIQUOD_v1.py                       # particle data of the sample image, results in ./miquod_output
python MIQUOD_v1.py image.png --roi X Y W H --color red --mode both
python miquod_gui.py                      # desktop application
```

Each target area has its own particle colour (red, green, blue, yellow or a custom hue), blob area limits and
an option to split touching particles. See [docs/usage.md](docs/usage.md) for every option, the desktop
application and the library API.

### Documentation
- [docs/usage.md](docs/usage.md): installation, command line, desktop application, Windows executable, library, outputs.
- [docs/method.md](docs/method.md): the measures and how they are computed.
- [docs/api.md](docs/api.md): reference of `Mixing_QMPD.py`, data structures and conventions.
- [docs/changes.md](docs/changes.md): what changed in Python 2.1 and the effect on the results.
- [docs/troubleshooting.md](docs/troubleshooting.md): error messages and how to fix them.

## Kotlin (Version 2.0)
[Kotlin](https://github.com/enaulad511/MIQUOD_Multi/tree/main/Kotlin/MIQUOD2/app/src/main/java/com/poc_itesm/miquod2) code are the main *.kt* files for an Android app.

## Authors

- [@enaulad511](https://github.com/enaulad511); [Edisson A. Naula Duchi, PhD](https://www.researchgate.net/profile/Edisson-Naula-Duchi)
- [Héctor Betancourt](https://mx.linkedin.com/in/hbetancourtc)

## Feedback

If you have any feedback or have any questions, please reach out to us at [edisson.naulad@gmail.com](mailto:edisson.naulad@gmail.com)
