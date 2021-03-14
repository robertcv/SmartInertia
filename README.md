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

### How to build

Install build requirements:
```bash
pip install -r requirements-dev.txt
```

To create the exe run:
```bash
pyinstaller smartinertia_gui.py --name SmartInertia -w --onefile
```
