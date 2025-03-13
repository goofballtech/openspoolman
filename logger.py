import os
import time

def append_to_rotating_file(file_path: str, text: str, max_size: int = 1_048_576, max_files: int = 5) -> None:
    """
    Appends the given text to a rotating log file.
    If the file exceeds the maximum size, it is renamed with a timestamp, and a new file is created.
    If the maximum number of log files is reached, the oldest file is deleted.
    """
    directory, base_filename = os.path.split(file_path)
    base_filename = os.path.splitext(base_filename)[0]
    os.makedirs(directory, exist_ok=True)
    
    # If the file exists and exceeds the size limit, rename it with a timestamp
    if os.path.exists(file_path) and os.path.getsize(file_path) > max_size:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        archived_file = os.path.join(directory, f"{base_filename}_{timestamp}.log")
        os.rename(file_path, archived_file)
    
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(text + "\n")
    
    # Check if too many log files exist and delete the oldest one
    log_files = sorted([f for f in os.listdir(directory) if f.startswith(base_filename) and f.endswith(".log")])
    if len(log_files) > max_files:
        os.remove(os.path.join(directory, log_files[0]))