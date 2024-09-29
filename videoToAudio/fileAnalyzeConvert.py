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

                # Process audio streams
                if audio_count is None or audio_count < 1:
                    print("No audio tracks found in the video file.")
                elif audio_count == 1:
                    # Only one audio track, assume type_order = 1
                    for track in track_info:
                        if track.get("@type") == "Audio":
                            audio_format = track.get("Format", "Unknown Format").lower()
                            output_filename = f"{current_millis}.{audio_format}"
                            audio_info = AudioInfo(1, audio_format, 0, output_filename)  # ffmpeg track order is 0
                            audio_info_list.append(audio_info)
                            break  # Stop after processing the first (and only) audio track
                else:
                    # Multiple audio tracks, process with the current logic
                    track_counter = 0
                    for track in track_info:
                        if track.get("@type") != "Audio":
                            continue  # Skip non-audio tracks
                        
                        # Extract the format and convert it to lowercase
                        audio_format = track.get("Format", "Unknown Format").lower()

                        # Extract type_order from "@typeorder" or use the current track counter
                        type_order = track.get("@typeorder", track_counter)

                        # FFmpeg track order is track_counter since "@typeorder" might not always be present
                        ffmpeg_track_order = track_counter

                        # Generate output filename for this audio track
                        output_filename = f"{current_millis}_track{ffmpeg_track_order}.{audio_format}"

                        # Store this info in the custom datatype
                        audio_info = AudioInfo(type_order, audio_format, ffmpeg_track_order, output_filename)
                        audio_info_list.append(audio_info)

                        # Increment track_counter
                        track_counter += 1

                # Process subtitle streams
                if text_count is None or text_count < 1:
                    print("No subtitle tracks found in the video file.")
                else:
                    track_counter = 0
                    for track in track_info:
                        if track.get("@type") != "Text":
                            continue  # Skip non-subtitle tracks
                        
                        # Extract the format and convert it to lowercase
                        subtitle_format = track.get("Format", "Unknown Format").lower()

                        # Fix for format values: Replace "UTF8"/"UTF-8" with "SRT", and "S_TEXT/WEBVTT" with "VTT"
                        if subtitle_format in ["utf8", "utf-8"]:
                            subtitle_format = "srt"
                        elif subtitle_format == "s_text/webvtt":
                            subtitle_format = "vtt"

                        # Extract type_order and ffmpeg_track_order
                        type_order = track.get("@typeorder", track_counter)
                        ffmpeg_track_order = track_counter

                        # Generate the output filename for this subtitle track
                        output_filename = f"{current_millis}_track{ffmpeg_track_order}.{subtitle_format}"

                        # Store subtitle info in the custom datatype
                        subtitle_info = SubtitleInfo(type_order, subtitle_format, ffmpeg_track_order, output_filename)
                        subtitle_info_list.append(subtitle_info)

                        # Increment track_counter
                        track_counter += 1

                # After processing all tracks, print audio and subtitle information and extract streams
                if audio_info_list:
                    print("\nAudio Streams Information:")
                    for audio in audio_info_list:
                        print(f"Audio Stream {audio.type_order}: Format - {audio.format_name}, FFmpeg Track Order: {audio.ffmpeg_track_order}, Output: {audio.output_filename}")
                    extract_audio(original_file, audio_info_list)

                    # Convert Audio to MP3 here
                    convert_audio_to_mp3(audio_info_list)

                if subtitle_info_list:
                    print("\nSubtitle Streams Information:")
                    for subtitle in subtitle_info_list:
                        print(f"Subtitle Stream {subtitle.type_order}: Format - {subtitle.format_name}, FFmpeg Track Order: {subtitle.ffmpeg_track_order}, Output: {subtitle.output_filename}")
                    extract_subtitles(original_file, subtitle_info_list)

                    # Convert SRT to LRC here
                    convert_srt_to_lrc(subtitle_info_list)
            else:
                print("Track information not found in JSON.")

    except FileNotFoundError:
        print(f"JSON file {json_file_name} not found.")
    except json.JSONDecodeError:
        print("Error decoding the JSON file.")

def convert_srt_to_lrc(subtitle_info_list):
    """
    Function to convert SRT subtitle files to LRC format.
    """
    srt_files = [subtitle for subtitle in subtitle_info_list if subtitle.format_name == "srt"]

    # If no SRT files found, exit the function
    if not srt_files:
        print("No SRT subtitle files found for conversion.")
        return

    for i, subtitle in enumerate(srt_files):
        # Get the filename without extension
        srt_filename_without_ext = os.path.splitext(subtitle.output_filename)[0]
        
        # Handle multiple SRT files by appending a number to the output filename
        if len(srt_files) > 1:
            lrc_output_filename = f"{srt_filename_without_ext}_{i + 1}.lrc"
        else:
            lrc_output_filename = f"{srt_filename_without_ext}.lrc"
        
        # FFmpeg command to convert the file
        ffmpeg_command = ["ffmpeg", "-i", f"{srt_filename_without_ext}.srt", lrc_output_filename]
        
        print(f"Converting {srt_filename_without_ext}.srt to {lrc_output_filename}")
        
        # Run the ffmpeg command using subprocess
        try:
            subprocess.run(ffmpeg_command, check=True)
            print(f"Successfully converted to {lrc_output_filename}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to convert {srt_filename_without_ext}.srt to LRC. Error: {e}")

def convert_audio_to_mp3(audio_info_list):
    """
    Function to convert extracted audio files to MP3 format.
    
    Parameters:
    - audio_info_list (list): A list of AudioInfo objects containing details about the extracted audio files.
    """
    audio_counter = 0
    for audio_info in audio_info_list:
        if audio_info.format_name.lower() == "mp3":
            print(f"Audio {audio_info.output_filename} is already in MP3 format. Skipping conversion.")
            continue

        # Extract the filename without the extension
        audio_file_no_ext = os.path.splitext(audio_info.output_filename)[0]

        # Generate output filename for the MP3 file
        if audio_counter == 0:
            output_mp3_file = f"{audio_file_no_ext}.mp3"
        else:
            output_mp3_file = f"{audio_file_no_ext}_{audio_counter}.mp3"

        # Build the FFmpeg command
        command = ['ffmpeg', '-i', audio_info.output_filename, output_mp3_file]

        # Execute the FFmpeg command
        try:
            print(f"Converting {audio_info.output_filename} to MP3...")
            subprocess.run(command, check=True)
            print(f"Conversion complete: {output_mp3_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error during audio conversion: {e}")
        
        # Increment audio counter for handling multiple files
        audio_counter += 1


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
