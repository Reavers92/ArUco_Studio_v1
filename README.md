# ArUco Studio

**Create, edit, verify, and export ArUco markers from a modern Python desktop interface.**

<img width="1066" height="749" alt="Screenshot 2026-10-29 212401" src="https://github.com/user-attachments/assets/6a5ac20e-be08-4082-92c6-09a95c670706" />

ArUco Studio is an offline tool for makers, robotics enthusiasts, and computer vision projects. Generate markers from OpenCV's predefined dictionaries, explore their binary patterns with a clickable grid, and save images for printing or use in your own applications.

The interface uses a dark theme and is entirely in English. No camera, ROS installation, account, or online service is required to use the application. Internet access is needed only to download the application and install its dependencies.

## Features

- **17 predefined dictionaries:** 4×4, 5×5, 6×6, and 7×7 families with 50, 100, 250, or 1000 markers, plus `DICT_ARUCO_ORIGINAL`.
- **Dictionary-based generation:** choose a dictionary and marker ID.
- **Interactive matrix editor:** click inner cells to toggle black and white; the one-cell black border stays locked.
- **Blank matrices:** start a custom pattern using the selected dictionary's matrix size.
- **Rotation and undo:** rotate clockwise in 90° steps and undo up to 100 matrix operations.
- **Configurable output:** marker side from 32 to 4096 pixels and white margin from 0 to 1000 pixels per side.
- **Two validation methods:** exact dictionary matching and detection of the exportable image with OpenCV.
- **PNG and SVG export:** save raster or vector images without editor grid lines or labels.
- **JSON projects:** save your matrix and settings, then reopen them later.

## Requirements

Designed for **Windows 10/11** and **Ubuntu 22.04/24.04**, with **Python 3.10–3.12**.

| Dependency | Version range | Purpose |
| --- | --- | --- |
| PySide6 | `>=6.6,<7` | Desktop interface |
| opencv-contrib-python-headless | `>=4.8,<5` | ArUco generation and detection |
| NumPy | `>=1.24,<3` | Binary matrix processing |

The headless OpenCV package is intentional: PySide6 provides the graphical interface, while OpenCV handles marker processing.

## Installation

Download and extract the project, or clone its GitHub repository. Open a terminal in the directory containing `aruco_studio.py` and `requirements.txt`.

### Windows

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python aruco_studio.py
```

### Ubuntu

```bash
sudo apt install python3-venv
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python aruco_studio.py
```

If the application reports missing Qt/xcb or graphics libraries on Ubuntu:

```bash
sudo apt install libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-xinerama0
```

Use a dedicated virtual environment, particularly on systems that already use OpenCV for ROS or other computer vision applications.

## Quick start

1. Select a **Dictionary**, such as `DICT_4X4_50`.
2. Choose an **ID to generate**, such as `0`.
3. Click **Generate from dictionary**.
4. Set **Marker side (px)** and **White margin (px)**.
5. Click **Verify with OpenCV** to test detection of the generated image.
6. Click **Export PNG / SVG** and choose the desired file format.

For example, a marker side of **600 px** with a **100 px** margin produces an **800 × 800 px** image.

> Changing the dictionary or ID selection does not replace the current drawing. Click **Generate from dictionary** to apply that selection, or **Blank matrix** to start a new editable pattern.

## How it works

### Dictionaries and IDs

An ArUco marker contains a binary inner matrix surrounded by a black border. In a dictionary name such as `DICT_4X4_50`:

- `4X4` describes the inner matrix, excluding the border.
- `50` is the number of available markers, with IDs from `0` to `49`.

The application obtains the selected marker from OpenCV, extracts its inner cells, and displays them in the editor. The camera application that reads the marker must use the same dictionary.

### Manual editing

Enable **Edit cells manually**, then left-click any inner cell to switch its color. Use **Blank matrix** to start from an all-black inner matrix, **Rotate 90°** to rotate clockwise, or **Undo** to restore the previous matrix.

The black border cannot be edited. **Show editor grid (not exported)** only changes the editor display.

**A manually drawn pattern does not automatically acquire the ID selected in the interface.** That field specifies which marker to generate; the exact-match status reports whether the current drawing actually corresponds to a marker in the selected dictionary, allowing for rotation.

This version does not create or export custom OpenCV dictionaries. Arbitrary patterns can be saved as images and JSON projects, but may not be recognizable as ArUco markers.

### Validation

The application provides two different checks:

| Check | What it does |
| --- | --- |
| Exact-match status | Compares the current inner matrix with the selected dictionary, allowing rotations and requiring an exact match. |
| Verify with OpenCV | Runs marker detection on the raster image that would be exported, using the selected size and margin. |

These results can differ: the detector may recognize a slightly modified pattern through error correction, even when it is no longer an exact dictionary match.

Verification uses a synthetic image. It does not guarantee detection after printing or under real camera conditions.

### Image size and export

**Marker side (px)** includes the inner matrix and black border. **White margin (px)** adds white space to each side:

```text
Output side = marker side + 2 × white margin
```

The preview automatically fits the window; it is not a pixel-for-pixel representation of the export or its configured margin. Refer to the displayed output dimensions and verification result when checking your settings.

- **PNG:** lossless raster image, rendered with nearest-neighbor scaling to preserve hard black-and-white edges.
- **SVG:** vector image built from rectangles, suitable for scaling and printing.

Both formats include the configured white margin and exclude interface labels and editor grid lines.

### Saving and reopening projects

Use **Save JSON project** to store an editable project, then **Open JSON project** to restore it.

A project stores:

- Format identifier and version.
- Selected dictionary and generation ID (`source_id`).
- Marker side and white margin in pixels.
- Current inner matrix as `0` and `1` values, where `0` is black and `1` is white.

The stored `source_id` is the generation selector value, not proof that an edited matrix matches that ID. Undo history is not saved and is cleared when a project is opened.

## Printing and camera use

- Use the same dictionary in ArUco Studio and your detector.
- Leave a white margin of at least one cell around the marker. The app warns when the configured margin is smaller.
- Prefer PNG or SVG; avoid JPEG compression and blurred or smoothed resizing.
- For evenly sized raster cells, choose a marker side divisible by the total number of cells: **inner matrix size + 2**. A 4×4 marker has six cells per side including its border, so 600 px gives 100 px per cell.
- Pixel dimensions do not define a physical size in centimeters. Set the print size explicitly and check the result with a ruler.
- For distance or pose estimation, configure the detector with the measured physical marker side **including the black border and excluding the white margin**.

ArUco Studio generates marker assets. It does not provide live camera tracking, camera calibration, or distance estimation.

## Project structure

```text
aruco_studio.py    Desktop application, matrix editor, validation, and export
requirements.txt  Python dependencies
README.md         Installation and usage guide
```

The application is implemented in one Python file. Marker generation and detection use OpenCV; matrix manipulation uses NumPy; rendering and interaction use PySide6.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `No module named PySide6` or `cv2` | Install `requirements.txt` using the same virtual environment interpreter used to launch the app. |
| OpenCV has no `aruco` attribute | Use the dependencies in a clean virtual environment and avoid mixing multiple OpenCV packages. |
| Qt/xcb startup error on Ubuntu | Install the system libraries listed in the Ubuntu instructions and run from a graphical desktop session. |
| No marker detected | Check the selected dictionary, increase the white margin, and generate an unmodified dictionary marker as a baseline. |
| ID selection does not change the preview | Click **Generate from dictionary** after choosing the ID. |
| Edited marker no longer matches its ID | Manual edits change the encoded pattern. Use the exact-match status to identify the current matrix. |
| Printed size is incorrect | Check print scaling and measure the marker itself, excluding the white margin. |

## Contributing

Bug reports and improvement suggestions are welcome through the repository's issue tracker. For reproducible reports, include your operating system, Python version, dependency versions, selected dictionary and ID, and the steps that trigger the issue.
