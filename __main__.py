import os
from mygptapp import app

if __name__ == '__main__':
    extra_files = []
    # loop through all the files in the mygptapp directory and add them to the list of extra files
    skip_paths = ["__pycache__", ".git", ".history"]
    for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
        for file in files:
            if not any(skip_path in root for skip_path in skip_paths):
                extra_files.append(os.path.join(root, file))

    app.run(port=8888, debug=False, extra_files=extra_files)
