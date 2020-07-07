# habitext

Habitext is a habit tracking tool that generates PDF reports from habit data in markdown files.

# Habit Format

Habits are in the following format in a directory.

#### **`habit1.md`**
```md
# Metadata

Name: Habit1

# Log

- MMMM-DD-YY
  - Note1
    - HH:MM
- MMMM-DD-YY
  - Note2
    - HH:MM
  - Note3
    - HH:MM
  - Note4
    - HH:MM
```

# Usage

## Local
1. Install python 3 and pip
2. Install required packages
```bash
pip install pandas plotnine reportlab
```
3. Clone and update settings
```bash
git clone https://github.com/ryushida/habitext.git
cd habitext
# Update directory and font settings in habitext.py
```
4. Run script
```bash
python habitext.py
```

## Docker

1. Install Docker
2. Clone and update settings
```bash
git clone https://github.com/ryushida/habitext.git
cd habitext
# Update directory and font settings in habitext.py
```
3. Build Docker Container
```bash
docker build -t habitext .
```
3. Run script in Docker Container

```bash
# Replace C:\Directory\of\habits with local directory where you store the .md files
docker run -it -v C:\Directory\of\habits:/habits/ habitext
```

You may need to set the timezone for the container. One way is by replacing the 'TZ database name' in the following command. Get your timezone from the 'TZ database name' column in the [list of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
```bash
docker run -it -v C:\Files\Repos\habits:/habits/ -e "TZ='TZ database name'" habitext
```