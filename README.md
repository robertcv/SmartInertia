## SmartInertia

Software to visualize data captured by the SmartInertia flywheel.

### How to run

Install requirements and package:
```bash
pip install -r requirements.txt
pip install .
```

Run module:
```bash
python -m smartinertia
```

### How to manually build

Install build requirements:
```bash
pip install -r requirements-dev.txt
```

To create the exe run:
```bash
pyinstaller --name SmartInertia --paths=src\smartinertia --windowed --onefile --icon=icon.ico smartinertia_gui.py
```

## Release / automatic build
To create a new release and automatically build the .exe just push a tage with the new version to master.
