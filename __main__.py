import os
from mygptapp import app, socketio

if __name__ == '__main__':
    extra_files = []
    # recursively loop through all the files in the mygptapp directory and add them to the list of extra files
    skip_paths = ["__pycache__", ".git", ".history", "static"]
    for root, dirs, files in os.walk("mygptapp"):
        for file in files:
            if not any(skip_path in root for skip_path in skip_paths):
                extra_files.append(os.path.join(root, file))
    print("extra_files", extra_files)

    socketio.run(app, port=8000)
