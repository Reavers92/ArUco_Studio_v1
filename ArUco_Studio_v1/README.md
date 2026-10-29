# ArUco Studio 1.0 — English edition

Offline Python desktop application with a PySide6 interface. Designed for Windows 10/11 and Ubuntu 22.04/24.04 with Python 3.10–3.12. Internet access is only needed to install dependencies.

## Installation and launch

Open a terminal in the extracted folder.

Windows:
```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python aruco_studio.py
```

Ubuntu:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python aruco_studio.py
```

If Ubuntu reports missing venv or Qt/xcb components:
```bash
sudo apt install python3-venv libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-xinerama0
```

Use a separate virtual environment to avoid conflicts with OpenCV installations used by ROS. The headless OpenCV package includes ArUco; PySide6 provides the graphical interface.

## Usage

1. Select a dictionary. 4×4, 5×5, 6×6 and 7×7 describe the inner matrix, excluding its border. The suffix 50/100/250/1000 specifies the number of available IDs. ARUCO_ORIGINAL (5×5) is also available.
2. Select an ID and click **Generate from dictionary**. Changing the selection does not replace the drawing until you click Generate.
3. Set the marker side in pixels, including its black border, and the white margin per side. A 600 px marker with a 100 px margin produces an 800×800 image.
4. Enable **Edit cells manually**, then click inner cells to toggle them. **Blank matrix** creates a black matrix matching the selected dictionary size. The black border stays locked at one cell. Clockwise rotation and undo for up to 100 operations are available.
5. The status area reports exact matches with IDs in the selected dictionary, including rotated matches. **Verify with OpenCV** also runs detection on the exportable raster image using the actual margin.
6. Export a lossless PNG or vector SVG. Grid lines and labels are not exported. Save a JSON project to resume editing later; it stores the matrix, dictionary and export settings.

## Manual matrices and IDs

An ID is the index of a marker within a particular dictionary. It cannot be assigned freely to an arbitrary drawing. The ID field controls the Generate button; after manual edits, refer to the exact-match status for the actual ID, if any.

An arbitrary matrix may not be detectable. This version exports its image and project, but does NOT generate a custom dictionary for the robot. Using custom patterns in tracking requires a shared dictionary in the generator and detector, with checks for code distances and rotational ambiguity. Uniform or symmetric matrices may be unsuitable.

A slightly modified image may still be detected through error correction. Exact matching and image detection are therefore separate checks.

Use the same dictionary in your camera application. Leave a white margin of at least one cell. Avoid JPEG compression, blur and interpolated resizing. Where possible, use a marker side in pixels divisible by the total number of cells (inner size + 2).

For distance or pose estimation, measure the physical side of the square including its black border but EXCLUDING the white margin, then configure that measurement in the detector. Pixels alone do not define the printed size in centimetres. Print the SVG at your desired physical size and verify it with a ruler.

## Compatibility and checks

Existing version 1 JSON projects remain compatible. Only interface text, messages, comments and documentation were translated. Qt file dialogs are used to keep their controls in English independently of the operating system language.

The original version was checked for offscreen GUI startup, cell editing, undo, rotation, and detection of the first and last IDs in all 17 dictionaries. JSON save/load and SVG syntax were also checked. The English edition was checked for GUI startup and layout. These checks do not replace testing with a real printer and camera.

API reference: https://docs.opencv.org/4.x/d5/d0b/classcv_1_1aruco_1_1Dictionary.html
