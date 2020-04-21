from invoke import task

from  tempfile import TemporaryDirectory

@task
def build(c):
    with TemporaryDirectory(dir=".", prefix="pyinstaller-build-") as tmpdir:
        cmd = f'pyinstaller pyinstaller/hsnap.py --onefile --workpath="{tmpdir}"'
        print(cmd)
        c.run(cmd)
        cmd = f'pyinstaller pyinstaller/hcmp.py --onefile --workpath="{tmpdir}"'
        print(cmd)
        c.run(cmd)
