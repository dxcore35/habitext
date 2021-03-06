import os
import pandas as pd
import numpy as np
import configparser
from datetime import date, datetime, timedelta
import plots
import pdf

def name_from_metadata(metadata):
    """ Returns habit name given metadata string
    """
    return (
        [i for i in metadata if i.startswith('Name:')][0]
        .split("Name:", 1)[1].strip()
    )
    
def goal_from_metadata(metadata):
    """ Returns habit name given metadata string
    """
    return (
        [i for i in metadata if i.startswith('Goal:')][0]
        .split("Goal:", 1)[1].strip()
    )

def date_line_number(log):
    """ Returns line numbers of dates in log string as a list
    """
    line_nums = []
    
    for index, line in enumerate(log):
        if line[0] == '-':
            line_nums.append(index)

    return line_nums

def get_habit_name(df):
    """ Return the name of the habit for the given dataframe
    """
    return df['Name'][0]

def hhmm_to_mm(time_str):
    """ Given a hh:mm string returns minutes as integer
    """
    h, m = time_str.split(':')
    return int(h) * 60 + int(m)

def text_after_bullet(s):
    """ Return string after '- ' in given string
    """
    t = s.partition('- ')[2]
    if t.endswith(' '):
        print(f'### Trailing Space at {s}')
        t = t.rstrip()
    return t

def get_day_of_week(date):
    """ Return day of week given a date
    """
    return date.strftime('%a')

def get_week_number(date):
    """ Return week number given a date
    """
    return int(date.strftime("%U"))

def get_year(date):
    """ Return year given a date
    """
    return int(date.strftime("%Y"))

def get_first_date(df):
    """ Return first date in dataframe
    """
    return df['Date'][0]

def get_date():
    """ Return date in yyyymmdd format
    """
    return datetime.today().strftime('%Y%m%d')

def get_yesterday():
    return datetime.now() - timedelta(days=1)

def md_file_list(dir):
    """ Returns list with file names of all markdown files
    in the given directory
    """
    mdlist = []
    for file in [f for f in os.listdir(dir) if f.endswith('.md')]:
        mdlist.append(file)

    return mdlist

def day_time_total(date_chunk):
    """ Returns total time in minutes given a date chunk string
    """
    total_time = 0

    for line in date_chunk[1:]:
        if line[0:4] == '    ':
            total_time += hhmm_to_mm(line.strip()[2:])

    return total_time

def chunk_by_date(log):
    """ Returns list of date chunks given log string
    """
    chunk_start_pos = date_line_number(log)
    # Add last line for last chunk
    chunk_start_pos.append(len(log))
    date_chunks_list = []

    for first, second in zip(chunk_start_pos, chunk_start_pos[1:]):
        date_chunks_list.append(log[first:second])

    return date_chunks_list

def get_description_metric(date_chunk):
    """ Return a list of tuples with the description and metric
    """
    time_metric_list = date_chunk[1:]
    description_metric = []
    for description, metric in zip(time_metric_list[0::2],
                                   time_metric_list[1::2]):
        description_metric.append((text_after_bullet(description),
                                   hhmm_to_mm(text_after_bullet(metric))))
        
    return description_metric

def datechunk_to_date(date_chunk):
    return pd.to_datetime(date_chunk[0][2:])

def log_to_tuple_list(log):
    """ Return tuple given log strings
    """
    tuple_list = []
    
    datechunk_list = chunk_by_date(log)

    for date_chunk in datechunk_list:
        date = datechunk_to_date(date_chunk)
        day_of_week = get_day_of_week(date)
        week = get_week_number(date)
        year = get_year(date)
        description_metric = get_description_metric(date_chunk)

        for d_m in description_metric:

            description = d_m[0]
            metric = d_m[1]

            tuple_list.append((date, day_of_week,
                               week, year, description, metric))
    
    return tuple_list

def tuple_list_to_df(tuple_list):
    """ Return dataframe given list of tuples
    """
    df = pd.DataFrame(
        tuple_list, columns = ['Date', 'Day', 'Week',
                               'Year', 'Description', 'Metric']
    )
    
    return df

def df_from_log(log, metadata):
    """ Return dataframe for habit given its log and metadata
    """
    tuple_list = log_to_tuple_list(log)
    df = tuple_list_to_df(tuple_list)
    df['Name'] = name_from_metadata(metadata)
    df['Goal'] = goal_from_metadata(metadata)
    
    return df

def metadata_from_lines(lines):
    """ Return metadata string given lines of a markdown file
    """
    i = lines.index("# Log")
    metadata = lines[:i]
    return metadata

def log_from_lines(lines):
    """ Return log string given lines of a markdown files
    """
    i = lines.index("# Log")
    log = [x for x in lines[i+1:] if x]
    return log

def get_df_list(filelist, dir):
    """ Return list of dataframes with the dataframe for
    each file from the filelist
    """
    df_list = []

    for file in filelist:
        with open(dir+file, encoding='UTF-8') as f:
            lines = [line.rstrip('\n') for line in f]
            
            metadata = metadata_from_lines(lines)
            log = log_from_lines(lines)
            
            if log:
                df_list.append(df_from_log(log, metadata))     

    return df_list

def get_plot_list(df_list, color, color_low, color_high,
                  color_heatmap_border, font, save_dir):
    """ Return list with tuple of form
    (habit_name, goal, plots_file_paths)
    """
    plotslist = []
    for df in df_list:
        plotslist.append(
            (
                get_habit_name(df),
                df['Goal'][0],
                create_plots(df, color, color_low, color_high,
                             color_heatmap_border, font, save_dir)
            )
        )
    return plotslist

def metric_date_sum(df):
    """ Return dataframe with sum of metric by day
    """
    return df.groupby(['Name', 'Date', 'Day', 'Week'])['Metric'].sum().reset_index()

def filter_zero_metric(df):
    """ Return dataframe without observations with a metric value of 0
    """
    return df[df['Metric'] != 0]

def metric_sum_df(df):
    """ Return dataframe with sum of metric by day
    """
    sums_series = df.groupby(['Description'])['Metric'].sum()
    df_sums = pd.DataFrame({'Desc': sums_series.index,
                            'Sum': sums_series.values})
    return df_sums

def add_zeros_before(df, date):
    """ Add empty observations to the dataframe from the Sunday
    of the week before the first date up to the first date
    """
    tuple_list = []

    start_date = date
    end_date = df['Date'][0]

    habitname = get_habit_name(df)
    description = ''
    metric = 0

    daterange = pd.date_range(start_date, end_date - timedelta(days=1))

    for date in daterange:
        day_of_week = get_day_of_week(date)
        week = get_week_number(date)
        year = get_year(date)

        tuple_list.append((habitname, date, day_of_week, week,
                           year, description, metric))

    df2 = pd.DataFrame(tuple_list)
    df2.columns = ['Name', 'Date', 'Day', 'Week', 'Year', 'Description',
                   'Metric']

    df3 = pd.concat([df2, df], ignore_index=True)

    return df3

def fill_dates(df, date_range):
    """ Fill dates in the date_range
    """
    df.set_index('Date', inplace=True)
    df.index = pd.to_datetime(df.index)
    df['existing_date'] = 1
    df = df.reindex(date_range, fill_value = 0)
    df.reset_index(inplace=True)
    df.rename(columns={'index':'Date'}, inplace=True)
    
    return df

def fill_nonexisting_name(df):
    df.loc[df['existing_date'] == 0, 'Name'] = get_habit_name(df)
    return df

def fill_nonexisting_day(df):
    return np.where(df['existing_date'] == 0,
                    df['Date'].apply(get_day_of_week),
                    df['Day'])

def fill_nonexisting_week(df):
    return np.where(df['existing_date'] == 0,
                    df['Date'].apply(get_week_number),
                    df['Week'])

def fill_nonexisting_year(df):
    return np.where(df['existing_date'] == 0,
                    df['Date'].apply(get_year),
                    df['Year'])

def fill_nonexisting_description(df):
    return np.where(df['existing_date'] == 0, '', df['Description'])

def fill_nonexisting_columns(df):
    """ Fill the day name, week, year, and description for dataframes
    with newly added dates
    """
    df = fill_nonexisting_name(df)
    df['Day'] = fill_nonexisting_day(df)
    df['Week'] = fill_nonexisting_week(df)
    df['Year'] = fill_nonexisting_year(df)
    df['Description'] = fill_nonexisting_description(df)
    
    return df

def add_zeros_between(df):
    """ Add dates with metric as 0 for any missing dates in the dataframe
    """
    date_range = pd.date_range(get_first_date(df), get_yesterday())
    df = fill_dates(df, date_range)
    df = fill_nonexisting_columns(df)
    df.drop('existing_date', axis = 1, inplace = True)
    
    return df

def insert_missing_dates(df):
    """ Adds 2 weeks of data before the first date and adds any missing dates
    to the dataframe
    """
    first_date = get_first_date(df)
    start_sunday = first_date - timedelta(days=(first_date.weekday() - 6) % 7, weeks=1)
    df = add_zeros_before(df, start_sunday)
    df = add_zeros_between(df)

    return df

def get_complete_date_sums(df):
    """ Return dataframe with missing dates inserted and sums of the metric
    for each date
    """
    df_date_sums = metric_date_sum(df)
    df_complete_date_sums = insert_missing_dates(df_date_sums)
    order = ['Sat', 'Fri', 'Thu', 'Wed', 'Tue', 'Mon', 'Sun']
    df_complete_date_sums['Day'] = pd.Categorical(df_complete_date_sums['Day'],
                                                  categories = order)
    
    return df_complete_date_sums

def week_sum_df(df):
    """ Return dataframe with sum of metric per week
    """
    df['Metric'] = df['Metric'].clip(upper = 1)
    
    df.set_index('Date', inplace=True)
    df.index = pd.to_datetime(df.index)
    week_sums_series = df.resample('W-SUN',
                                   closed = 'left',
                                   label='left')['Metric'].sum()
    df_week_sums = pd.DataFrame({'Week': week_sums_series.index,
                                 'Days': week_sums_series.values})
    df_week_sums['Name'] = get_habit_name(df)
    
    return df_week_sums

def day_mean_df(df):
    """ Returns dataframe with the mean metric by day
    """
    sum_by_day = metric_date_sum(filter_zero_metric(df))
    mean_by_day = sum_by_day.groupby(['Day'])['Metric'].mean()
    df2 = pd.DataFrame({'Day' : mean_by_day.index,
                        'Mean Time' : mean_by_day.values})
    order = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    df2['Day of Week'] = pd.Categorical(df2['Day'],
                                        categories = order,
                                        ordered = True)
    df2['Name'] = get_habit_name(df)
    return df2

def description_sum_df(df):
    df_sums = metric_sum_df(df)
    df_sums['Sum'] = df_sums['Sum'] / 60
    df_sums.columns = ['Desc', 'Hours']
    
    df_sums['Desc'] = df_sums['Desc'].str.wrap(8)

    order = df_sums.sort_values(by = ['Hours'])['Desc']
    df_sums['Description'] = pd.Categorical(df_sums['Desc'],
                                            categories=order,
                                            ordered=True)
    df_sums['Name'] = get_habit_name(df)
    
    return df_sums

def create_plots(df, color, color_low, color_high, color_heatmap_border,
                 font, save_dir):
    """ Create each plot and return list with file paths
    """
    plotlist = []

    df_complete_date_sums = get_complete_date_sums(df)
    habit_name = get_habit_name(df_complete_date_sums)
    plotlist.append(plots.create_heatmap(df_complete_date_sums, habit_name, color_low,
                                   color_high, color_heatmap_border,
                                   font, save_dir))
    
    df_week_sums = week_sum_df(df_complete_date_sums)
    df_day_means = day_mean_df(df)
    df_description_sums = description_sum_df(df)

    plotlist.append(plots.create_completion_num_graph(df_week_sums, habit_name, color,
                                                font, save_dir))
    plotlist.append(plots.create_bar_metric_mean(df_day_means, habit_name, color, font, save_dir))
    plotlist.append(plots.create_bar_metric_sum(df_description_sums, habit_name, color, font, save_dir))

    return plotlist
    
def delete_files(file_list):
    """ Deletes files in file_list
    """
    for file in file_list:
        try:
            os.remove(file)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

def main():
    """Create DataFrame from markdown files, split dataframes
    by habit name, create plots, and add plots to PDF
    """
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Directories need to exist
    habit_dir = config.get('Directories', 'md_dir')
    save_dir = config.get('Directories', 'pdf_save_dir')
    color_heatmap_border = config.get('Plots', 'color_heatmap_border')
    color_low = config.get('Plots', 'color_low')
    color_high = config.get('Plots', 'color_high')
    color = config.get('Plots', 'color')
    font = config.get('Plots', 'font')

    habitlist = md_file_list(habit_dir)

    df_list = get_df_list(habitlist, habit_dir)

    plotslist = get_plot_list(df_list, color, color_low, color_high,
                              color_heatmap_border, font, save_dir)

    pdf.create_pdf(plotslist, save_dir, get_date())

    delete_lists = [x[2] for x in plotslist]
    for delete_list in delete_lists:
        delete_files(delete_list)
   

if __name__ == '__main__':
    main()