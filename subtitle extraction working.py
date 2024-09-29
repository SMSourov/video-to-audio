import sys
import os
import time
import subprocess
import json

# Define a custom class to store audio information
class AudioInfo:
    def __init__(self, type_order, format_name, ffmpeg_track_order, output_filename):
        self.type_order = type_order  # Integer to store the order of the audio stream
        self.format_name = format_name  # String to store the audio format
        self.ffmpeg_track_order = ffmpeg_track_order  # Track order for FFmpeg (type_order - 1)
        self.output_filename = output_filename  # Output filename for extracted audio

def analyze_video(file_path):
    # Get system time in milliseconds to generate unique JSON and output file names
    current_millis = int(round(time.time() * 1000))
    json_file_name = f"{current_millis}.json"
    
    # Command to extract media info using MediaInfo and output it to a JSON file
    mediainfo_command = f"MediaInfo.exe --Output=JSON \"{file_path}\" > \"{json_file_name}\""

    try:
        # Run the command
        result = subprocess.run(mediainfo_command, shell=True)
        
        # Check if the command was successful
        if result.returncode == 0:
            print(f"Media info extracted and saved to {json_file_name}")
        else:
            print(f"Error analyzing the file: {file_path}")
            sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    
    # After extraction, read and process the JSON file
    process_json_file(json_file_name, file_path, current_millis)

class SubtitleInfo:
    def __init__(self, type_order, format_name, ffmpeg_track_order, output_filename):
        self.type_order = type_order  # Integer to store the order of the subtitle stream
        self.format_name = format_name  # String to store the subtitle format
        self.ffmpeg_track_order = ffmpeg_track_order  # FFmpeg track order (track order - 1)
        self.output_filename = output_filename  # Filename for the extracted subtitle

def extract_subtitles(input_file, subtitle_info_list):
    """
    Function to extract multiple subtitle streams from the video file.
    """
    for subtitle_info in subtitle_info_list:
        # Construct FFmpeg command to extract subtitle
        ffmpeg_command = f"ffmpeg -i \"{input_file}\" -map 0:s:{subtitle_info.ffmpeg_track_order} \"{subtitle_info.output_filename}\""
        try:
            print(f"Running FFmpeg command to extract subtitle: {ffmpeg_command}")
            subprocess.run(ffmpeg_command, shell=True)
            print(f"Subtitle extracted to {subtitle_info.output_filename}")
        except Exception as e:
            print(f"Error extracting subtitle: {e}")

def process_json_file(json_file_name, original_file, current_millis):
    """
    Function to process the JSON file and extract audio, cover image, and subtitle information.
    """
    # List to store audio and subtitle information
    audio_info_list = []
    subtitle_info_list = []

    # Read and load the JSON file
    try:
        with open(json_file_name, 'r') as json_file:
            data = json.load(json_file)

            # Navigate to "media" -> "track"
            media_info = data.get("media", {})
            track_info = media_info.get("track", [])
            
            # Ensure "track" is a list and process each track
            if isinstance(track_info, list):
                first_element_processed = False
                audio_count = None
                text_count = None
                cover_image_found = False

                for track in track_info:
                    # First element: capture metadata information
                    if not first_element_processed:
                        first_element_processed = True
                        # Extract "AudioCount" and "TextCount" and convert to int if they're strings
                        audio_count = track.get("AudioCount")
                        text_count = track.get("TextCount")
                        if audio_count is not None:
                            try:
                                audio_count = int(audio_count)
                            except ValueError:
                                audio_count = 0  # Set to 0 if conversion fails
                            print(f"AudioCount: {audio_count}")
                        if text_count is not None:
                            try:
                                text_count = int(text_count)
                            except ValueError:
                                text_count = 0  # Set to 0 if conversion fails
                            print(f"TextCount: {text_count}")
                        
                        # Check if "Cover" exists and is "Yes"
                        cover = track.get("Cover")
                        if cover == "Yes":
                            cover_image_found = True
                            cover_image_filename = f"{current_millis}_cover.jpg"
                            print(f"Cover: {cover}, Cover Image Filename: {cover_image_filename}")

                        # Check if "extra" exists in "track"
                        extra_info = track.get("extra")
                        if extra_info:
                            artist = extra_info.get("ARTIST", "Unknown")
                            date = extra_info.get("DATE", "Unknown")
                            purl = extra_info.get("PURL", "Unknown")
                            
                            print(f"ARTIST: {artist}")
                            print(f"DATE: {date}")
                            print(f"PURL: {purl}")

                # Extract the cover image if it exists
                if cover_image_found:
                    extract_cover_image(original_file, cover_image_filename)

                # Process audio streams (not shown here, handled elsewhere)

                # Process subtitle streams
                if text_count is None or text_count < 1:
                    print("No subtitle tracks found in the video file.")
                else:
                    # Array to hold the output filenames for subtitles
                    subtitle_filenames = []
                    track_counter = 0

                    for track in track_info:
                        if track.get("@type") != "Text":
                            continue  # Skip non-subtitle tracks
                        
                        # Extract the format and convert it to lowercase
                        subtitle_format = track.get("Format", "Unknown Format").lower()

                        # Extract type_order and ffmpeg_track_order
                        type_order = track.get("@typeorder", track_counter)
                        ffmpeg_track_order = track_counter

                        # Generate the output filename for this subtitle track
                        output_filename = f"{current_millis}_track{ffmpeg_track_order}.{subtitle_format}"
                        subtitle_filenames.append(output_filename)

                        # Store subtitle info in the custom datatype
                        subtitle_info = SubtitleInfo(type_order, subtitle_format, ffmpeg_track_order, output_filename)
                        subtitle_info_list.append(subtitle_info)

                        # Increment track_counter
                        track_counter += 1

                    # Extract all subtitle streams using FFmpeg
                    if subtitle_info_list:
                        print("\nSubtitle Streams Information:")
                        for subtitle in subtitle_info_list:
                            print(f"Subtitle Stream {subtitle.type_order}: Format - {subtitle.format_name}, FFmpeg Track Order: {subtitle.ffmpeg_track_order}, Output: {subtitle.output_filename}")
                        extract_subtitles(original_file, subtitle_info_list)
                    else:
                        print("No subtitle streams found.")

    except FileNotFoundError:
        print(f"JSON file {json_file_name} not found.")
    except json.JSONDecodeError:
        print("Error decoding the JSON file.")

def extract_audio(input_file, audio_info_list):
    """
    Function to extract multiple audio streams from the video file
    """
    for audio_info in audio_info_list:
        # Construct FFmpeg command to extract audio
        ffmpeg_command = f"ffmpeg -i \"{input_file}\" -map 0:a:{audio_info.ffmpeg_track_order} \"{audio_info.output_filename}\""
        try:
            print(f"Running FFmpeg command: {ffmpeg_command}")
            subprocess.run(ffmpeg_command, shell=True)
            print(f"Audio extracted to {audio_info.output_filename}")
        except Exception as e:
            print(f"Error extracting audio: {e}")

def extract_cover_image(input_file, output_image):
    # Construct FFmpeg command to extract the cover image (assumed to be the first video stream with image data)
    # ffmpeg_command = f"ffmpeg -i \"{input_file}\" -map 0:v -c copy -f image2 \"{output_image}\""
    ffmpeg_command = f"ffmpeg -i \"{input_file}\" -map 0:v -map -0:V -c:v copy \"{output_image}\""
    try:
        print(f"Running FFmpeg command to extract cover image: {ffmpeg_command}")
        subprocess.run(ffmpeg_command, shell=True)
        print(f"Cover image extracted to {output_image}")
    except Exception as e:
        print(f"Error extracting cover image: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python fileAnalyzeConvert.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Verify if the provided file exists
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    # Analyze the video file and extract media info
    analyze_video(file_path)

if __name__ == "__main__":
    main()
