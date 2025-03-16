import os

# Check if the path exists
src_path = "/Users/sanjaybiswas/development/trivia-app/backend/src"
print(f"Does path exist? {os.path.exists(src_path)}")

# List files in the directory
if os.path.exists(src_path):
    print("Files in src directory:")
    for file in os.listdir(src_path):
        print(f"  {file}")
    
    # Check for the config directory specifically
    config_path = os.path.join(src_path, "config")
    print(f"Does config path exist? {os.path.exists(config_path)}")
    
    if os.path.exists(config_path):
        print("Files in config directory:")
        for file in os.listdir(config_path):
            print(f"  {file}")