# NEBULA EYE

A cinematic, real-time ASCII eye visualizer built with Python, Pygame, Pillow, and NumPy. It transforms a close-up eye photo into a moving character-art scene with chromatic highlights, drifting particles, scanlines, and a pupil-centered cyan/violet energy pulse.

![Platform](https://img.shields.io/badge/platform-Windows-0078D4)
![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Live ASCII rendering:** Converts the eye image into a shaded grid of characters.
- **Cinematic camera movement:** Reveals the image, zooms toward the iris, and transitions into a stylized portal phase.
- **Pupil-centered energy effects:** Adds a bright core, expanding cyan and violet rings, sparks, and a soft afterglow.
- **Chromatic color treatment:** Warm iris highlights and cool neon accents give the scene its sci-fi look.
- **Atmospheric particles and scanlines:** Adds motion and texture to the background.
- **Interactive controls:** Pause, restart, toggle fullscreen, resize the window, or exit.

## Preview

Add a screenshot or short GIF of the running animation here when you have one, for example:

```md
![NEBULA EYE preview](docs/preview.gif)
```

## Requirements

- Windows 10 or Windows 11
- Python 3.13 (the commands below use the Windows Python launcher, `py`)
- A close-up eye image saved as `eye.jpg` in the project folder

## Quick start

1. Download or clone this repository.
2. Make sure `nebula_eye.py` and `eye.jpg` are in the same directory.
3. Open PowerShell in that directory.
4. Install the dependencies:

   ```powershell
   py -3.13 -m pip install -r requirements.txt
   ```

5. Start the visualizer:

   ```powershell
   py -3.13 nebula_eye.py
   ```

You can also run `setup.ps1` from PowerShell to install the dependencies.

## Controls

| Key | Action |
| --- | --- |
| `SPACE` | Pause or resume |
| `R` | Restart the animation |
| `F` | Toggle fullscreen |
| `ESC` | Exit |

## Project structure

```text
nebula-eye/
├── nebula_eye.py    # Animation and rendering
├── eye.jpg          # Source eye photograph
├── requirements.txt # Python dependencies
├── setup.ps1        # Windows dependency setup
├── .gitignore
├── LICENSE
└── README.md
```

## Troubleshooting

### The app says it cannot find `eye.jpg`

Keep `eye.jpg` in the same folder as `nebula_eye.py`. Check that Windows has not silently added another extension such as `eye.jpg.jpg`.

### A module is missing

Run:

```powershell
py -3.13 -m pip install -r requirements.txt
```

If the Python launcher cannot find version 3.13, install Python 3.13 and enable the Python launcher during setup.

### The animation is slow

Close other GPU/CPU-heavy apps and try a smaller window. The ASCII grid is configured in `nebula_eye.py`; lowering `GRID_COLS` can improve performance.

## Development

The main implementation is in `nebula_eye.py`. The pupil location is configured with `PUPIL_CENTER`, using normalized image coordinates from 0 to 1. Adjust it if the source image changes.

To run a syntax check:

```powershell
py -3.13 -m py_compile nebula_eye.py
```

## License

This project is released under the MIT License. See [LICENSE](LICENSE).

---

Made with Python and an unreasonable amount of attention to a glowing eyeball.
