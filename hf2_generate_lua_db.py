"""
Parses Homefront: The Revolution LuaState.txt dump files and
organizes them into a .csv database for readability and documentation.
"""

import re
import csv
import glob
import os
import sys
import time


# Set up the log file to capture all print output
LOG_FILE_PATH = f'generation_log_{time.strftime("%Y%m%d_%H%M%S")}.txt'
print(f"Log file will be saved to: {LOG_FILE_PATH}")


# Define a class to write to both stdout (console) and a log file
class DualOutput:
    """
    A class that writes output to multiple destinations simultaneously.

    This class allows you to redirect output to one or more streams
    (e.g., console and log file) at once.
    It can be used in cases where you want to both print to the console and
    log the output to a file or other stream.
    """
    def __init__(self, *outputs):
        """
        Initializes the DualOutput instance with multiple output streams.

        Parameters:
            *outputs: A variable number of output streams (e.g., sys.stdout, file objects).
        """
        self.outputs = outputs

    def write(self, message):
        """
        Writes the given message to all specified output streams.

        Parameters:
            message (str): The message to be written to the output streams.
        """
        for output in self.outputs:
            output.write(message)

    def flush(self):
        """
        Flushes all output streams to ensure that all buffered data is written out.

        This is typically called after writing to output streams to
        ensure that the data is immediately visible or written to the disk/file.
        """
        for output in self.outputs:
            output.flush()


# Open the log file in write mode and capture the original stdout
LOG_FILE = open(LOG_FILE_PATH, 'w', encoding='utf-8')  # Open the log file for writing
# Capture the original stdout (console)
original_stdout = sys.stdout
# All prints written to log
print("Starting the logging process...")

# Set up the dual output to write to both the console and the log file
sys.stdout = DualOutput(original_stdout, LOG_FILE)

# Define regex patterns for functions, variables, and properties
# Detect functions by parentheses
function_pattern = re.compile(r"\[\s*\d+]\s+(\w+)\(")
# Detect Booleans as any variable set to 0 or 1
boolean_pattern = re.compile(r"\[\s*\d+]\s+(\w+)\s*=\s*[01]")
# Properties with assignment '='
property_pattern = re.compile(r"\[\s*\d+]\s+(\w+)\s*=")
# General pattern for any name
name_pattern = re.compile(r"\[\s*\d+]\s+(\w+)")
# Detect start of a table
start_table_pattern = re.compile(r"\[\s*\d+]\s+(\w+)\s*=\s*\{")

# Dictionary to store unique names with types and full paths
unique_names = {}

# Stack to keep track of current nested path
path_stack = []

# Find all LuaState*.txt files
input_files = glob.glob('dumps/**/LuaState*.txt', recursive=True)
OUTPUT_FILE_PATH = 'hf2_lua_names_nested.csv'
print("Starting the generation process...")  # And so it begins

# Read existing entries from the CSV to maintain the current order and notation columns
existing_entries = []
header = []
if os.path.isfile(OUTPUT_FILE_PATH):
    with open(OUTPUT_FILE_PATH, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Save the header row (column names)
        existing_entries = [row for row in reader if row]  # Read the full row (name, type, notes)


# Process each file
for input_file_path in input_files:
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                start_table_match = start_table_pattern.search(line)
                if start_table_match:
                    table_name = start_table_match.group(1)
                    path_stack.append(table_name)  # Add new table to the path
                    print(f"Entering table: {table_name}")  # Debug print
                    continue

                if line.strip().endswith("}"):
                    if path_stack:
                        exited_table = path_stack.pop()  # Exit the current table level
                        print(f"Exiting table: {exited_table}")  # Debug print
                    continue

                FULL_PATH = ".".join(path_stack) if path_stack else ""

                function_match = function_pattern.search(line)
                if function_match:
                    name = function_match.group(1)
                    full_key = f"{FULL_PATH}.{name}" if FULL_PATH else name
                    if full_key not in unique_names:
                        unique_names[full_key] = "Function"
                    print(f"Detected function: {full_key}")  # Debug print
                    continue

                boolean_match = boolean_pattern.search(line)
                if boolean_match:
                    name = boolean_match.group(1)
                    full_key = f"{FULL_PATH}.{name}" if FULL_PATH else name
                    if full_key not in unique_names:
                        unique_names[full_key] = "Boolean Variable"
                    print(f"Detected boolean: {full_key}")  # Debug print
                    continue

                property_match = property_pattern.search(line)
                if property_match:
                    name = property_match.group(1)
                    full_key = f"{FULL_PATH}.{name}" if FULL_PATH else name
                    if full_key not in unique_names:
                        unique_names[full_key] = "Property"
                        print(f"Detected property: {full_key}")  # Debug print
                    continue

                name_match = name_pattern.search(line)
                if name_match:
                    name = name_match.group(1)
                    full_key = f"{FULL_PATH}.{name}" if FULL_PATH else name
                    if full_key not in unique_names:
                        unique_names[full_key] = "Unknown"
                        print(f"Detected unknown: {full_key}")  # Debug print

    except FileNotFoundError:
        print(f"Error: File {input_file_path} not found.")
        continue


# Combine new entries (name, type) with the existing entries
print("Combining new entries with existing ones...")  # Debug print before combining
new_entries = [
    (name, type_, "")
    for name, type_ in unique_names.items()
    if name not in [row[0] for row in existing_entries]
]

print(f"New entries: {new_entries}")  # Debug print to show new entries being added

# Combine old and new entries into a single list
combined_entries = existing_entries + new_entries
# Debug print to show the number of combined entries
print(f"Total combined entries: {len(combined_entries)}")

# Sort the combined entries alphabetically by the name (first column)
sorted_entries = sorted(combined_entries, key=lambda x: x[0])
# Debug print to show the first 10 sorted entries
print(f"Sorted entries: {sorted_entries[:10]}...")


# Write everything back to the CSV file, preserving the notation column
NEW_ENTRIES_COUNT = 0
# Debug print to indicate the start of the write process
print(f"Writing to CSV file: {OUTPUT_FILE_PATH}")

with open(OUTPUT_FILE_PATH, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    # Write the header row
    writer.writerow(header)  # Write the header row
    print(f"Header written: {header}")  # Debug print for header

    # Write each sorted row (name, type, context/notes)
    for i, row in enumerate(sorted_entries):
        writer.writerow(row)  # Write each row
        if row not in existing_entries:
            NEW_ENTRIES_COUNT += 1  # Count new entries added
        if i % 100 == 0:  # Print every 100th row to keep track of progress
            print(f"Writing row {i + 1}: {row}")  # Debug print for progress

# Debug print for the total number of new entries
print(f"Finished writing. '{OUTPUT_FILE_PATH}' with {NEW_ENTRIES_COUNT} new entries.")

# After the script has finished, restore stdout to the original console output
sys.stdout = original_stdout

# Close the log file after all operations
LOG_FILE.close()

# Final message to the console
print(f"Process complete. Log saved to '{LOG_FILE_PATH}'.")

# -- Copyright (c) 2024 HeyItsDuke
# -- This file is licensed under the Mozilla Public License, Version 2.0 (MPL-2.0).
# -- Author: HeyItsDuke
# -- Organization: HFModding
# -- I hereby grant HFModding a license to use, modify, and distribute this code under the terms of the MPL-2.0.
