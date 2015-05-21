import sys
from cx_Freeze import setup, Executable
import pymunk

base = None 
if sys.platform == "win32":
    base = "Win32GUI"
   
exe = Executable(script="pyroller.py", base=base)
 
include_files=["resources/music", "resources/graphics", "resources/sound",
                     "resources/fonts"]
includes=[]
excludes=[]
packages=[]

setup(version="1.0",
         description="A Collection of Casino Games",
         author="PyRollers Collective",
         name="Pyrollers Casino",
         options={"build_exe": {"includes": includes, "include_files": include_files, "packages": packages, "excludes": excludes}},
         executables=[exe])

