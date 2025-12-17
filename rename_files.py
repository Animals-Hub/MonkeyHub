import os
from pathlib import Path

def rename_files(directory):
    path = Path(directory)
    if not path.exists():
        print(f"Directory {directory} does not exist.")
        return

    print(f"Renaming files in {directory}...")
    count = 0
    for file in path.iterdir():
        if file.is_file():
            if "猪" in file.name:
                new_name = file.name.replace("猪", "猴")
                new_path = path / new_name
                try:
                    file.rename(new_path)
                    print(f"Renamed: {file.name} -> {new_name}")
                    count += 1
                except Exception as e:
                    print(f"Error renaming {file.name}: {e}")
    print(f"Renamed {count} files in {directory}.")

if __name__ == "__main__":
    # Rename in source imgs_monkey
    rename_files("imgs_monkey")
    
    # Rename in target public imgs_monkey (if not symlinked)
    rename_files("fronted/public/imgs_monkey")
