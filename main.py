import sys
import os
import subprocess

def process_directory(directory):
    print(f"Directory '{directory}' is being processed.")
    # Process the directory (this can be extended with more logic)
    
def show_readme():
    readme_path = "videoToAudio/readme.txt"
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as file:
            content = file.read()
            print(content)
    else:
        print(f"Readme file not found at {readme_path}")

def run_check_variables():
    # Command words to be checked (ffmpeg, etc.)
    command_words = ["ffmpeg", "ffprobe", "mkvextract", "mkvmerge", "magick", "mediainfo", "tone"]  # You can customize this list as needed

    # Launch the checkVariables.py script and pass the command words
    result = subprocess.run([sys.executable, "videoToAudio/checkVariables.py"] + command_words)
    if result.returncode != 0:
        print("Missing environment variables or shell commands. Exiting.")
        sys.exit(1)

def verify_file_extension(file_path):
    # Launch the verifyFileExtension.py script with the file path
    result = subprocess.run([sys.executable, "videoToAudio/verifyFileExtension.py", file_path])
    if result.returncode != 0:
        print("File is not a valid video file. Exiting.")
        sys.exit(1)

def analyze_and_convert(file_path):
    # Launch the fileAnalyzeConvert.py script with the file path
    result = subprocess.run([sys.executable, "videoToAudio/fileAnalyzeConvert.py", file_path])
    if result.returncode != 0:
        print("An error occurred during file analysis and conversion.")
        sys.exit(1)


def main():
    if len(sys.argv) == 2:
        path = sys.argv[1]
        if os.path.isfile(path):
            print(f"File '{path}' is being processed.")
            # Run environment variable checks first
            run_check_variables()
            # Then verify the file extension
            verify_file_extension(path)
            # Analyze the file and convert
            analyze_and_convert(path)
        elif os.path.isdir(path):
            process_directory(path)
            run_check_variables()
        else:
            print(f"'{path}' is neither a valid file nor a directory.")
    else:
        show_readme()

if __name__ == "__main__":
    main()
    