import os
import shutil
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import time

def compress_image(file_path, output_dir):
    try:
        if file_path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
            return None
            
        output_filename = file_path.stem + ".webp"
        output_path = output_dir / output_filename
        
        # Skip if already exists and newer (optional, but good for re-runs)
        # if output_path.exists():
        #     return f"Skipped {output_filename}"

        with Image.open(file_path) as img:
            # Convert to RGB if RGBA and saving as JPEG, but WebP supports RGBA.
            # However, for consistency and size, we stick to default WebP settings.
            img.save(output_path, "WEBP", quality=80, method=6)
            
        return f"Compressed: {file_path.name} -> {output_filename}"
    except Exception as e:
        return f"Error compressing {file_path.name}: {e}"

def process_directory(source_dir_name, target_dir_path):
    source_dir = Path(source_dir_name)
    target_dir = Path(target_dir_path)
    
    # Check if source exists
    if not source_dir.exists():
        print(f"Source directory {source_dir} not found!")
        return

    # Handle the target directory / symlink
    if target_dir.is_symlink() or target_dir.is_file():
        print(f"Removing existing symlink/file: {target_dir}")
        target_dir.unlink()
    elif target_dir.exists():
        print(f"Target directory {target_dir} exists.")
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting compression for {source_dir} -> {target_dir}...")
    start_time = time.time()
    
    files = list(source_dir.glob("*"))
    max_workers = os.cpu_count() or 4
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda f: compress_image(f, target_dir), files))
        
    # Print summary
    success_count = sum(1 for r in results if r and r.startswith("Compressed"))
    error_count = sum(1 for r in results if r and r.startswith("Error"))
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nFinished {source_dir_name} in {duration:.2f} seconds.")
    print(f"Successfully compressed: {success_count} images")
    print(f"Errors: {error_count}")
    
    # Calculate size diff
    source_size = sum(f.stat().st_size for f in source_dir.glob("*") if f.is_file()) / (1024*1024)
    target_size = sum(f.stat().st_size for f in target_dir.glob("*") if f.is_file()) / (1024*1024)
    
    print(f"Original Size: {source_size:.2f} MB")
    print(f"Compressed Size: {target_size:.2f} MB")
    if source_size > 0:
        print(f"Reduction: {source_size - target_size:.2f} MB ({(1 - target_size/source_size)*100:.1f}%)")

def main():
    dirs_to_process = [
        ("imgs_monkey", "fronted/public/imgs_monkey"),
        ("imgs", "fronted/public/imgs")
    ]
    
    for source, target in dirs_to_process:
        process_directory(source, target)
        print("-" * 40)


if __name__ == "__main__":
    main()
