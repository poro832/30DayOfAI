import os
import shutil

base_dir = r"c:\Users\ldd82\NxtCloud\30DaysOfAI (2)\notion"
folders = {
    "Day1": range(1, 11),
    "Day2": range(11, 23),
    "Day3": range(23, 26)
}

for folder, day_range in folders.items():
    target_dir = os.path.join(base_dir, folder)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created {target_dir}")
    
    for i in day_range:
        filename = f"day{i}.md"
        src = os.path.join(base_dir, filename)
        dst = os.path.join(target_dir, filename)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"Moved {filename} to {folder}")
        else:
            print(f"{filename} not found")
