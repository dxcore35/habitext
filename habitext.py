import os
import pandas as pd
import numpy as np
from plotnine import *
from datetime import date, datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib import utils
from reportlab.platypus import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

def md_file_list(dir):
    """ Returns list with file names of all markdown files
    in the given directory
    """
    mdlist = []
    for file in [f for f in os.listdir(dir) if f.endswith('.md')]:
        mdlist.append(file)

    return mdlist

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
    return s.partition('- ')[2]

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

def get_yesterday():
    return datetime.now() - timedelta(days=1)

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

def get_tuple_list(log):
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
    tuple_list = get_tuple_list(log)
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
    """ Given a list of markdown files their directory
    returns a list of dataframes for each file
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

def metric_date_sum(df):
    """ Return dataframe with sum of metric by day
    """
    return df.groupby(['Name', 'Date', 'Day', 'Week'])['Metric'].sum().reset_index()

def filter_zero_metric(df):
    """ Return dataframe without observations with a metric value of 0
    """
    return df[df['Metric'] != 0]

def create_heatmap(df, color_low, color_high, color_heatmap_border, font, save_dir):
    """ Create tile plot and return tuple with file path and habit name
    """
    plt = (ggplot(df, aes(x = 'Week', y = 'Day', fill = 'Metric'))
           + geom_tile(aes(width = 0.95, height = 0.95),
                       color = color_heatmap_border, size = 1)
           + scale_x_continuous(breaks = df['Week'].unique())
           + coord_equal()
           + scale_fill_gradient(low = color_low, high = color_high)
           + ggtitle('Heatmap')
           + theme_bw()
           + theme(figure_size = (6, 6), text=element_text(family=font, size = 13)))

    habit_name = get_habit_name(df)
    f = habit_name + '_heatmap' + '.png'
    file = save_dir+f
    ggsave(filename=file, plot=plt, device = 'png', height = 2, width = 2, dpi=300)

    return file

def day_mean_df(df):
    """ Returns dataframe with the mean metric by day
    """
    sum_by_day = metric_date_sum(filter_zero_metric(df))
    mean_by_day = sum_by_day.groupby(['Day'])['Metric'].mean()
    df2 = pd.DataFrame({'Day' : mean_by_day.index,
                        'Mean' : mean_by_day.values})
    return df2

def create_bar_metric_mean(df, color, font, save_dir):
    """ Create bar plot with mean value of metric by day of week
    and return tuple with file path and habit name
    """
    df2 = day_mean_df(df)

    order = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    df2['Day of Week'] = pd.Categorical(df2['Day'],
                                        categories = order,
                                        ordered = True)

    plt = (ggplot(pd.DataFrame(df2), aes(x = 'Day of Week', y = 'Mean'))
           + geom_col(fill = color)
           + ggtitle('Mean time by Day of Week')
           + theme_bw()
           + theme(figure_size = (6, 6), text=element_text(family=font, size = 13)))

    habit_name = get_habit_name(df)
    f = habit_name + '_meanbar' + '.png'
    file = save_dir+f
    ggsave(filename=file, plot=plt, device = 'png', dpi=300)

    return file

def metric_sum_df(df):
    """ Return dataframe with sum of metric by day
    """
    sums_series = df.groupby(['Description'])['Metric'].sum()
    df_sums = pd.DataFrame({'Desc': sums_series.index,
                            'Sum': sums_series.values})
    return df_sums

def create_bar_metric_sum(df, color, font, save_dir):
    """ Create bar plot with total time spent for each description
    and return tuple with file path and habit name
    """
    df_sums = metric_sum_df(df)
    df_sums['Sum'] = df_sums['Sum'] / 60
    df_sums.columns = ['Desc', 'Hours']
    
    df_sums['Desc'] = df_sums['Desc'].str.wrap(8)

    order = df_sums.sort_values(by = ['Hours'])['Desc']
    df_sums['Description'] = pd.Categorical(df_sums['Desc'],
                                            categories=order,
                                            ordered=True)

    plt = (ggplot(pd.DataFrame(df_sums), aes(x = 'Description', y = 'Hours'))
           + geom_col(fill = color)
           + coord_flip()
           + ggtitle('Sum time per Description')
           + theme_bw()
           + theme(figure_size = (6, 6), text=element_text(family=font, size = 13)))

    habit_name = get_habit_name(df)
    f = habit_name + '_sumbar' + '.png'
    file = save_dir+f
    ggsave(filename=file, plot=plt, device = 'png', dpi=300)

    return file

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
                                 'Sum': week_sums_series.values})
    
    return df_week_sums

def create_completion_num_graph(df, color, font, save_dir):
    """ Create bar plot with the number of days per week the
    habit is completed and return tuple with file path and habit name
    """
    df_week_sums = week_sum_df(df)
    
    plt = (ggplot(df_week_sums, aes(x = 'Week', y = 'Sum'))
           + geom_line()
           + coord_cartesian(ylim=[0,7])
           + scale_y_continuous(labels = list(range(0, 7)),
                                breaks = list(range(0, 7)))
           + scale_x_date(breaks = pd.date_range(min(df_week_sums['Week']),
                                                 max(df_week_sums['Week']),
                                                 freq='W-SUN'))
           + ggtitle('Completed Days per Week')
           + theme_bw()
           + theme(figure_size = (6, 6), text=element_text(family=font, size = 13)))
    
    habit_name = get_habit_name(df)
    f = habit_name + '_completion' + '.png'
    file = save_dir+f
    ggsave(filename=file, plot=plt, device = 'png', dpi=300)
    
    return file

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

def create_plots(df, color, color_low, color_high, color_heatmap_border,
                 font, save_dir):
    """ Create each plot and return list with file paths
    """
    plotlist = []

    habit_name = get_habit_name(df)
    goal = df['Goal'][0]

    df_complete_date_sums = get_complete_date_sums(df)

    plotlist.append(
        create_heatmap(df_complete_date_sums, color_low, color_high, 
                       color_heatmap_border, font, save_dir)
    )
    plotlist.append(
        create_completion_num_graph(df_complete_date_sums, color,
                                     font, save_dir)
    )
    plotlist.append(create_bar_metric_mean(df, color, font, save_dir))
    plotlist.append(create_bar_metric_sum(df, color, font, save_dir))

    return ((habit_name, goal, plotlist))

def get_date():
    """ Return date in yyyymmdd format
    """
    return datetime.today().strftime('%Y%m%d')

def get_aspect(image):
    """ Return aspect given an image
    """
    img = utils.ImageReader(image)
    img_width, img_height = img.getSize()
    return img_width / float (img_height)

def add_images(file_list, c):
    """ Adds images in file_list to PDF page
    """
    aspect = [get_aspect(file_list[0]), get_aspect(file_list[1]),
              get_aspect(file_list[2]), get_aspect(file_list[3])]
    
    y_top = 525
    y_middle = 225
    pos = [(30, y_top), (345, y_top), (30, y_middle), (345, y_middle)]

    scale = 200
    
    for idx, file in enumerate(file_list):
        c.drawImage(file, pos[idx][0], pos[idx][1],
                    width=scale * aspect[idx], height=scale)
        
    return c

def add_text(plot_group, c):
    """ Adds habit name and goal to PDF as text
    """
    habit_name = plot_group[0]
    goal = plot_group[1]
    c.setFont('HeiseiMin-W3', 16)
    c.drawString(50, 800, habit_name + ':   ' + goal)
    return c

def create_pdf(plotslist, dir):
    """ Create pdf with images in plotlist
    """
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
    c = canvas.Canvas(dir + get_date() + '_habits.pdf')

    for plot_group in plotslist:
        c = add_text(plot_group, c)
        file_list = plot_group[2]
        c = add_images(file_list, c)

        c.showPage()
    
    c.save()
    
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
    # Directories need to exist
    habit_dir = "/habits/"
    save_dir = "/habits/reports/"
    color_heatmap_border = "black"
    color_low = "white"
    color_high = "green"
    color = "green"
    font = "Noto Sans CJK JP"

    habitlist = md_file_list(habit_dir)

    df_list = get_df_list(habitlist, habit_dir)

    plotslist = []

    for df in df_list:
        plotslist.append(create_plots(df, color, color_low, color_high,
                         color_heatmap_border, font, save_dir))

    create_pdf(plotslist, save_dir)

    delete_lists = [x[2] for x in plotslist]
    for delete_list in delete_lists:
        delete_files(delete_list)
   

if __name__ == '__main__':
    main()