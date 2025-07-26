import pandas as pd
from gtts import gTTS
from pydub import AudioSegment
import os

# Load the data from the CSV file
file_path = 'speed_test_interpolated.csv'
data = pd.read_csv(file_path)

# Check the column for car speed
speed_column = 'car_speed'

# Initialize an empty AudioSegment for concatenation
combined_audio = AudioSegment.silent(duration=1000)  # 1 second silence as a buffer

# Analyze data to determine where warnings are needed
over_speed_entries = data[data[speed_column] > 50]

# Generate a single warning message for all instances where the speed exceeds 50 km/h
if not over_speed_entries.empty:
    for index, row in over_speed_entries.iterrows():
        warning_message = f"Warning! Vehicle with license plate {row['license_number']} is exceeding the speed limit at {row[speed_column]} km/h."
        
        # Generate voice-over using gTTS and save to a temporary file
        temp_file = f"temp_warning_{index}.mp3"
        tts = gTTS(text=warning_message, lang='en')
        tts.save(temp_file)
        
        # Load the audio from the temporary file and append to the combined audio
        audio_segment = AudioSegment.from_file(temp_file, format="mp3")
        combined_audio += audio_segment + AudioSegment.silent(duration=500)  # 0.5 second pause between warnings
        
        # Remove the temporary file
        os.remove(temp_file)
        
        print(f"Added warning for row {index}: {warning_message}")

# Save the combined audio to a single MP3 file
combined_audio.export("combined_warnings.mp3", format="mp3")
print("Combined voice-over generation complete.")
