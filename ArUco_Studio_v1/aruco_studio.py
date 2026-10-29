#!/usr/bin/env python3
"""ArUco Studio — offline generator/editor. English interface and comments."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QSpinBox, QCheckBox, QPushButton, QFileDialog, QMessageBox,
    QFormLayout, QFrame,
)

DICTS = [f'DICT_{n}X{n}_{count}' for n in range(4, 8)
         for count in (50, 100, 250, 1000)] + ['DICT_ARUCO_ORIGINAL']


def dictionary(name):
    return cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, name))


def marker_bits(name, marker_id):
    d = dictionary(name)
    # One cell per pixel allows unambiguous bit extraction.
    img = cv2.aruco.generateImageMarker(d, marker_id, d.markerSize + 2)
    return (img[1:-1, 1:-1] > 0).astype(np.uint8)


def raster(bits, size, margin):
    """Size = marker side including the black border; margin = white space per side, in px."""
    cells = np.pad(bits * 255, 1, constant_values=0).astype(np.uint8)
    img = cv2.resize(cells, (size, size), interpolation=cv2.INTER_NEAREST)
    return np.pad(img, margin, constant_values=255)


def svg_text(bits, size, margin):
    n = len(bits) + 2
    side = size + 2 * margin
    cell = size / n
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{side}" height="{side}" viewBox="0 0 {side} {side}">',
             f'<rect width="{side}" height="{side}" fill="white"/>',
             f'<rect x="{margin}" y="{margin}" width="{size}" height="{size}" fill="black"/>']
    for y, row in enumerate(bits):
        for x, bit in enumerate(row):
            if bit:
                parts.append(f'<rect x="{margin+(x+1)*cell:.8f}" y="{margin+(y+1)*cell:.8f}" width="{cell:.8f}" height="{cell:.8f}" fill="white"/>')
    return '\n'.join(parts + ['</svg>'])


class Canvas(QWidget):
    toggled = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.bits = np.zeros((4, 4), np.uint8)
        self.editable = False
        self.grid = True
        self.setMinimumSize(360, 360)

    def geometry_cells(self):
        side = min(self.width(), self.height()) - 64
        return (self.width()-side)/2, (self.height()-side)/2, side/(len(self.bits)+2)

    def paintEvent(self, event):
        p = QPainter(self)
        x0, y0, c = self.geometry_cells()
        n = len(self.bits) + 2
        p.fillRect(QRectF(x0-20, y0-20, n*c+40, n*c+40), QColor('white'))
        cells = np.pad(self.bits, 1)
        for y in range(n):
            for x in range(n):
                rect = QRectF(x0+x*c, y0+y*c, c, c)
                p.fillRect(rect, QColor('white' if cells[y, x] else 'black'))
                if self.grid:
                    p.setPen(QPen(QColor('#64748b'), 0.7))
                    p.drawRect(rect)

    def mousePressEvent(self, event):
        if not self.editable or event.button() != Qt.LeftButton:
            return
        x0, y0, c = self.geometry_cells()
        x = int(np.floor((event.position().x()-x0)/c)) - 1
        y = int(np.floor((event.position().y()-y0)/c)) - 1
        if 0 <= x < len(self.bits) and 0 <= y < len(self.bits):
            self.toggled.emit(y, x)


class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ArUco Studio • Generator and editor')
        self.resize(1080, 760)
        self.bits = marker_bits(DICTS[0], 0)
        self.history = []
        self.dirty = False
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        panel = QFrame()
        panel.setObjectName('panel')
        panel.setFixedWidth(330)
        left = QVBoxLayout(panel)
        left.setContentsMargins(22, 22, 22, 22)
        title = QLabel('ArUco Studio')
        title.setObjectName('title')
        left.addWidget(title)
        left.addWidget(QLabel('CREATE  /  EDIT  /  EXPORT'))
        form = QFormLayout()
        self.dict_box = QComboBox()
        self.dict_box.addItems(DICTS)
        self.id_box = QSpinBox()
        self.id_box.setRange(0, 49)
        self.size_box = QSpinBox()
        self.size_box.setRange(32, 4096)
        self.size_box.setValue(600)
        self.margin_box = QSpinBox()
        self.margin_box.setRange(0, 1000)
        self.margin_box.setValue(100)
        form.addRow('Dictionary', self.dict_box)
        form.addRow('ID to generate', self.id_box)
        form.addRow('Marker side (px)', self.size_box)
        form.addRow('White margin (px)', self.margin_box)
        left.addLayout(form)
        self.button(left, 'Generate from dictionary', self.generate, True)
        self.manual = QCheckBox('Edit cells manually')
        left.addWidget(self.manual)
        self.button(left, 'Blank matrix', self.blank)
        row = QHBoxLayout()
        self.button(row, 'Rotate 90°', self.rotate)
        self.button(row, 'Undo', self.undo)
        left.addLayout(row)
        self.button(left, 'Verify with OpenCV', self.verify)
        left.addStretch()
        self.button(left, 'Export PNG / SVG', self.export, True)
        self.button(left, 'Save JSON project', self.save_project)
        self.button(left, 'Open JSON project', self.load_project)
        layout.addWidget(panel)
        right = QVBoxLayout()
        heading = QLabel('Interactive preview')
        heading.setObjectName('heading')
        right.addWidget(heading)
        self.description = QLabel()
        self.description.setWordWrap(True)
        right.addWidget(self.description)
        self.canvas = Canvas()
        right.addWidget(self.canvas, 1)
        self.grid = QCheckBox('Show editor grid (not exported)')
        self.grid.setChecked(True)
        right.addWidget(self.grid)
        self.status = QLabel()
        self.status.setObjectName('status')
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        note = QLabel('The black border is locked. The preview fits the available space; exports use the specified pixel size.\nA manually drawn matrix does not automatically receive an ArUco ID.')
        note.setWordWrap(True)
        right.addWidget(note)
        layout.addLayout(right, 1)
        self.dict_box.currentTextChanged.connect(self.dictionary_changed)
        self.id_box.valueChanged.connect(lambda: setattr(self, 'dirty', True))
        self.canvas.toggled.connect(self.toggle)
        self.manual.toggled.connect(self.edit_mode)
        self.grid.toggled.connect(self.grid_changed)
        self.size_box.valueChanged.connect(self.settings_changed)
        self.margin_box.valueChanged.connect(self.settings_changed)
        self.refresh()
        self.dirty = False

    def button(self, layout, text, callback, primary=False):
        b = QPushButton(text)
        if primary:
            b.setObjectName('primary')
        b.clicked.connect(callback)
        layout.addWidget(b)

    def dictionary_changed(self):
        self.id_box.setMaximum(len(dictionary(self.dict_box.currentText()).bytesList)-1)
        self.refresh()
        self.dirty = True

    def settings_changed(self):
        self.dirty = True
        self.refresh()

    def edit_mode(self, enabled):
        self.canvas.editable = enabled
        self.canvas.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)

    def grid_changed(self, enabled):
        self.canvas.grid = enabled
        self.canvas.update()

    def commit(self, bits):
        self.history.append(self.bits.copy())
        self.history = self.history[-100:]
        self.bits = bits.copy()
        self.dirty = True
        self.refresh()

    def generate(self):
        self.commit(marker_bits(self.dict_box.currentText(), self.id_box.value()))

    def blank(self):
        self.commit(np.zeros((dictionary(self.dict_box.currentText()).markerSize,)*2, np.uint8))
        self.manual.setChecked(True)

    def rotate(self):
        self.commit(np.rot90(self.bits, -1).copy())

    def undo(self):
        if self.history:
            self.bits = self.history.pop()
            self.dirty = True
            self.refresh()

    def toggle(self, y, x):
        bits = self.bits.copy()
        bits[y, x] ^= 1
        self.commit(bits)

    def refresh(self):
        self.canvas.bits = self.bits
        self.canvas.update()
        n = len(self.bits)
        total = self.size_box.value()+2*self.margin_box.value()
        self.description.setText(f'Inner matrix {n} × {n}  •  Black border: 1 cell\nExported image: {total} × {total} px')
        d = dictionary(self.dict_box.currentText())
        if d.markerSize == n:
            ok, idx, rot = d.identify(self.bits, 0.0)
        else:
            ok = False
        if ok:
            msg = f'Exact match: {self.dict_box.currentText()}, ID {idx} (rotations allowed).'
        else:
            msg = 'Custom matrix: no exact match in the selected dictionary.'
        if self.margin_box.value() < self.size_box.value()/(n+2):
            msg += '\nSmall margin: leave at least one white cell around the marker for detection.'
        self.status.setText(msg)

    def verify(self):
        img = raster(self.bits, self.size_box.value(), self.margin_box.value())
        detector = cv2.aruco.ArucoDetector(dictionary(self.dict_box.currentText()))
        _, ids, _ = detector.detectMarkers(img)
        msg = ('Marker detected in the exportable image: ID ' + ', '.join(map(str, ids.ravel()))
               if ids is not None else 'No marker detected with the selected dictionary and margin.')
        QMessageBox.information(self, 'Image verification', msg + '\n\nThis synthetic test does not guarantee detection with a real camera.')

    def export(self):
        path, selected = QFileDialog.getSaveFileName(self, 'Export image', 'marker.png', 'PNG (*.png);;SVG (*.svg)')
        if not path:
            return
        suffix = '.svg' if selected.startswith('SVG') else '.png'
        p = Path(path)
        if p.suffix.lower() != suffix:
            p = p.with_suffix(suffix)
            if p.exists() and QMessageBox.question(self, 'Overwrite?', str(p)) != QMessageBox.Yes:
                return
        try:
            if suffix == '.svg':
                p.write_text(svg_text(self.bits, self.size_box.value(), self.margin_box.value()), encoding='utf-8')
            else:
                ok, encoded = cv2.imencode('.png', raster(self.bits, self.size_box.value(), self.margin_box.value()))
                if not ok:
                    raise ValueError('PNG encoding failed')
                p.write_bytes(encoded.tobytes())
            self.statusBar().showMessage(f'Image saved: {p}', 8000)
        except Exception as exc:
            QMessageBox.critical(self, 'Export error', str(exc))

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save project', 'marker.aruco.json', 'Project (*.json)')
        if not path:
            return False
        try:
            payload = dict(format='aruco-studio', version=1, dictionary=self.dict_box.currentText(),
                           source_id=self.id_box.value(), size_px=self.size_box.value(),
                           margin_px=self.margin_box.value(), bits=self.bits.tolist())
            Path(path).write_text(json.dumps(payload, indent=2), encoding='utf-8')
            self.dirty = False
            self.statusBar().showMessage('Project saved', 5000)
            return True
        except Exception as exc:
            QMessageBox.critical(self, 'Save error', str(exc))
            return False

    def may_discard(self):
        if not self.dirty:
            return True
        choice = QMessageBox.question(self, 'Unsaved changes', 'Save the project before continuing?',
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        return self.save_project() if choice == QMessageBox.Save else choice == QMessageBox.Discard

    def load_project(self):
        if not self.may_discard():
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Open project', '', 'Project (*.json)')
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            bits = np.asarray(data['bits'])
            if data.get('format') != 'aruco-studio' or data.get('version') != 1:
                raise ValueError('Unsupported project format')
            if bits.ndim != 2 or bits.shape[0] != bits.shape[1] or not 4 <= len(bits) <= 7 or not np.isin(bits, [0, 1]).all():
                raise ValueError('Invalid matrix: expected 0/1 bits and a side length from 4 to 7')
            if data['dictionary'] not in DICTS:
                raise ValueError('Unknown dictionary')
            for key, low, high in [('size_px', 32, 4096), ('margin_px', 0, 1000),
                                   ('source_id', 0, len(dictionary(data['dictionary']).bytesList)-1)]:
                if type(data[key]) is not int or not low <= data[key] <= high:
                    raise ValueError(f'Invalid parameter: {key}')
            self.dict_box.setCurrentText(data['dictionary'])
            self.id_box.setValue(data['source_id'])
            self.size_box.setValue(data['size_px'])
            self.margin_box.setValue(data['margin_px'])
            self.bits = bits.astype(np.uint8)
            self.history.clear()
            self.refresh()
            self.dirty = False
        except Exception as exc:
            QMessageBox.critical(self, 'Invalid project', str(exc))

    def closeEvent(self, event):
        event.accept() if self.may_discard() else event.ignore()


STYLE = '''
QWidget { background:#101621; color:#dce5f4; font-family:"Segoe UI","DejaVu Sans"; font-size:13px; }
QFrame#panel { background:#192332; border:1px solid #2b3b50; border-radius:16px; }
QFrame#panel QLabel, QFrame#panel QCheckBox { background:transparent; }
QLabel#title { font-size:28px; font-weight:700; color:#ffffff; padding-bottom:8px; }
QLabel#heading { font-size:23px; font-weight:600; }
QLabel#status { background:#1c3040; padding:16px; border-radius:10px; color:#8de3d4; }
QPushButton { background:#26364b; border:1px solid #3a4d65; border-radius:8px; padding:10px; }
QPushButton:hover { background:#354b65; }
QPushButton#primary { background:#2dd4bf; color:#09252c; border:0; font-weight:700; }
QPushButton#primary:hover { background:#6ee7d5; }
QComboBox,QSpinBox { background:#101a28; border:1px solid #40516a; border-radius:5px; padding:7px; }
QCheckBox { padding:6px 0; }
QMessageBox QLabel { min-width:320px; }
'''


def main():
    QApplication.setAttribute(Qt.AA_DontUseNativeDialogs)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    window = Studio()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
