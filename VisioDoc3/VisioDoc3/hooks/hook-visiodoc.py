from PyInstaller.utils.hooks import collect_data_files
import os

# Get the base directory of the main script
# This assumes the hook is in a 'hooks' directory next to the main script
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the icons directory
datas = collect_data_files(os.path.join(basedir, 'icons'), include_py_files=False)

# Add the MANUEL_UTILISATEUR.md file
datas.append((os.path.join(basedir, 'MANUEL_UTILISATEUR.md'), 'docs'))
