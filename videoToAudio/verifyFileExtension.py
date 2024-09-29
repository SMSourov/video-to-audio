import sys
import os

def is_video_file(file_path):
    # Define common video file extensions (you can add more if needed)
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v']

    # Get the file extension
    file_extension = os.path.splitext(file_path)[1].lower()

    # Check if the file extension is in the list of video extensions
    if file_extension in video_extensions:
        print(f"The file '{file_path}' is a video file.")
        return True
    else:
        print(f"The file '{file_path}' is not a video file.")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python verifyFileExtension.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Verify if the provided file is a video file
    is_video_file(file_path)

if __name__ == "__main__":
    main()
