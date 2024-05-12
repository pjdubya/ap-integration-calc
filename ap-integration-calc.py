import argparse
import csv
import os
import re
from datetime import datetime, timedelta

def parse_time(line):
    # Define the pattern to extract the date and time segment
    pattern = r'\[Frames rejection\] (\d{4}-\d{2}-\d{2}).*?-\d+\.\d{2}.*?_(\d+\.\d{2})s?_'

    # Find all matches of the pattern in the line
    matches = re.findall(pattern, line)
    # Initialize per-day time dictionary
    per_day_time = {}
    # Iterate through matches and update the per-day time dictionary
    for match in matches:
        # Subtract 12 hours from the datetime to get the correc date when the acquisition was done (avoids date change at midnight)
        date = datetime.strptime(match[0], "%Y-%m-%d")
        date -= timedelta(hours=12)  # Subtract 12 hours
        date = date.strftime("%Y-%m-%d")
        time_seconds = float(match[1])
        # Update per-day time dictionary
        key = (date, time_seconds)
        if key in per_day_time:
            per_day_time[key][0] += 1
            per_day_time[key][1] += time_seconds
        else:
            per_day_time[key] = [1, time_seconds]
    return per_day_time

def write_to_csv(sorted_per_day_time_accepted, logfile):
    directory, filename = os.path.split(logfile)
    filename_without_extension = os.path.splitext(filename)[0]
    csv_file = os.path.join(directory, f"{filename_without_extension}.csv")
    #field_names = ['date', 'filter', 'number', 'duration']
    field_names = ['date', 'number', 'duration']

    print("\nWriting image acquisition details to CSV file: ", csv_file)
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        for (date, time_seconds), (count, total_seconds) in sorted_per_day_time_accepted:
            writer.writerow({
                'date': date,
                # omitting filter for now
                # 'filter': '',
                'number': count,
                'duration': '{:.0f}'.format(time_seconds)
            })

def main(logfile):
    accepted_time_total = 0
    rejected_time_total = 0
    per_day_time_accepted = {}
    per_day_time_rejected = {}

    with open(logfile, 'r') as file:
        # Read each line in the file
        for line in file:
            # Check if the line contains "[Frames rejection]"
            if "[Frames rejection]" in line:
                # Check if the line ends with "accepted" or "rejected"
                if line.strip().endswith("accepted"):
                    # Parse time from the line
                    per_day_time_line = parse_time(line)
                    # Update total accepted time and per-day time dictionary
                    for (date, time_seconds), (count, total_seconds) in per_day_time_line.items():
                        accepted_time_total += total_seconds
                        if (date, time_seconds) in per_day_time_accepted:
                            per_day_time_accepted[(date, time_seconds)][0] += count
                            per_day_time_accepted[(date, time_seconds)][1] += total_seconds
                        else:
                            per_day_time_accepted[(date, time_seconds)] = [count, total_seconds]
                elif line.strip().endswith("rejected"):
                    # Parse time from the line
                    per_day_time_line = parse_time(line)
                    # Update total rejected time and per-day time dictionary
                    for (date, time_seconds), (count, total_seconds) in per_day_time_line.items():
                        rejected_time_total += total_seconds
                        if (date, time_seconds) in per_day_time_rejected:
                            per_day_time_rejected[(date, time_seconds)][0] += count
                            per_day_time_rejected[(date, time_seconds)][1] += total_seconds
                        else:
                            per_day_time_rejected[(date, time_seconds)] = [count, total_seconds]

    # Display total accepted time
    print("Total accepted time:", format_time(accepted_time_total))

    # Display total rejected time
    print("Total rejected time:", format_time(rejected_time_total))

    # Display time per day for accepted frames
    print("\nTime per day per exposure duration for accepted frames:")
    sorted_per_day_time_accepted = sorted(per_day_time_accepted.items(), key=lambda x: (x[0][0], x[0][1]))
    for (date, time_seconds), (count, total_seconds) in sorted_per_day_time_accepted:
        print("Date:", date, "| Exposure:", time_seconds, "s",  "| Subs:", str(count).rjust(3), "| Total time:", format_time(total_seconds))

    write_to_csv(sorted_per_day_time_accepted, logfile)

def format_time(seconds):
    if seconds >= 3600:
        return "{:.2f} hours".format(seconds / 3600)
    elif seconds >= 60:
        return "{:.2f} minutes".format(seconds / 60)
    else:
        return "{:.2f} seconds".format(seconds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse log file for accepted and rejected frames rejection times.')
    parser.add_argument('--logfile', help='Path to the log file', required=True)
    args = parser.parse_args()
    main(args.logfile)
