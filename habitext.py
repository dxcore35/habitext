import os
import pandas as pd
from plotnine import *
from datetime import datetime, timedelta
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

def get_habit_name(metadata):
    """ Returns habit name given metadata string
    """
    return (
        [i for i in metadata if i.startswith('Name:')][0]
        .split("Name:", 1)[1].strip()
    )

def date_line_number(log):
    """ Returns line numbers of dates in log string as a list
    """
    line_nums = []
    
    for index, line in enumerate(log):
        if line[0] == '-':
            line_nums.append(index)

    return line_nums

def hhmm_to_mm(time_str):
    """ Given a hh:mm string returns minutes as integer
    """
    h, m = time_str.split(':')
    return int(h) * 60 + int(m)

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

def expand_datechunks(date_chunk):
    """ Returns date, day of week, week number, and metric
    given a date chunk
    """
    date = pd.to_datetime(date_chunk[0][2:])
    day_of_week = get_day_of_week(date)
    week = get_week_number(date)
    year = date.year

    time_metric_list = date_chunk[1:]
    description_metric = []
    for description, metric in zip(time_metric_list[0::2], time_metric_list[1::2]):
        description_metric.append((text_after_bullet(description),
                                   hhmm_to_mm(text_after_bullet(metric))))
    
    return date, day_of_week, week, year, description_metric

def get_tuple_list(metadata, log):
    """ Return tuple given metadata and log strings
    """
    tuple_list = []
    
    habitname = get_habit_name(metadata)
    datechunk_list = chunk_by_date(log)

    for datechunk in datechunk_list:
        date, day_of_week, week, year, description_metric = expand_datechunks(datechunk)

        for d_m in description_metric:

            description = d_m[0]
            metric = d_m[1]

            tuple_list.append((habitname, date, day_of_week,
                               week, year, description, metric))
    
    return tuple_list

def tuple_list_to_df(tuple_list):
    """ Return dataframe given list of tuples
    """
    df = pd.DataFrame(
        tuple_list, columns = ['Name', 'Date', 'Day', 'Week',
                               'Year', 'Description', 'Metric']
    )
    
    return df

def create_DataFrame(filelist, dir):
    """ Given a list of markdown files their directory
    returns a list of dataframes for each file
    """
    df_list = []

    for file in filelist:
        with open(dir+file, encoding='UTF-8') as f:
            lines = [line.rstrip('\n') for line in f]
            
            i = lines.index("# Log")
            metadata = lines[:i]
            log = [x for x in lines[i+1:] if x]
            
            if log:
                tuple_list = get_tuple_list(metadata, log)
                df = tuple_list_to_df(tuple_list)
                df_list.append(df)

    return df_list

def metric_date_sum(df):
    """ Return dataframe with sum of metric by day
    """
    return df.groupby(['Name', 'Date', 'Day', 'Week'])['Metric'].sum().reset_index()

def create_heatmap(df, color_low, color_high, color_heatmap_border, font, save_dir):
    """ Create tile plot and return tuple with file path and habit name
    """
    plt = (ggplot(metric_date_sum(df), aes(x = 'Week', y = 'Day', fill = 'Metric'))
           + geom_tile(aes(width = 0.95, height = 0.95),
                       color = color_heatmap_border, size = 1)
           + scale_x_continuous(breaks = df['Week'].unique())
           + coord_equal()
           + scale_fill_gradient(low = color_low, high = color_high)
           + ggtitle(df['Name'][0])
           + theme_bw()
           + theme(text=element_text(family=font)))

    habit_name = df['Name'][0]
    f = habit_name + '_heatmap' + '.png'
    file = save_dir+f
    ggsave(filename=file, plot=plt, device = 'png', height = 2, width = 2, dpi=300)

    return ((file, habit_name))

def create_bar_metric_mean(df, color, font, save_dir):
    """ Create bar plot with mean value of metric by day of week
    and return tuple with file path and habit name
    """
    sum_by_day = metric_date_sum(df)
    mean_by_day = sum_by_day.groupby(['Day'])['Metric'].mean()
    df2 = pd.DataFrame({'Day' : mean_by_day.index,
                        'Mean' : mean_by_day.values})

    order = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    df2['Day of Week'] = pd.Categorical(df2['Day'],
                                        categories = order,
                                        ordered = True)

    plt = (ggplot(pd.DataFrame(df2), aes(x = 'Day of Week', y = 'Mean'))
           + geom_col(fill = color)
           + ggtitle('Mean time by Day of Week')
           + theme_bw()
           + theme(text=element_text(family=font)))

    habit_name = df['Name'][0]
    f = habit_name + '_meanbar' + '.png'
    file = save_dir+f
    ggsave(filename=file, plot=plt, device = 'png', dpi=300)

    return ((file, habit_name))

def create_bar_metric_sum(df, color, font, save_dir):
    """ Create bar plot with total time spent for each description
    and return tuple with file path and habit name
    """
    sums_series = df.groupby(['Description'])['Metric'].sum()
    df_sums = pd.DataFrame({'Desc': sums_series.index,
                            'Sum': sums_series.values})

    order = df_sums.sort_values(by = ['Sum'])['Desc']
    df_sums['Description'] = pd.Categorical(df_sums['Desc'],
                                            categories=order,
                                            ordered=True)

    plt = (ggplot(pd.DataFrame(df_sums), aes(x = 'Description', y = 'Sum'))
           + geom_col(fill = color)
           + coord_flip()
           + ggtitle('Sum time per Description')
           + theme_bw()
           + theme(text=element_text(family=font)))

    habit_name = df['Name'][0]
    f = habit_name + '_sumbar' + '.png'
    file = save_dir+f
    ggsave(filename=file, plot=plt, device = 'png', dpi=300)

    return ((file, habit_name))

def create_plots(df, color, color_low, color_high, color_heatmap_border,
                 font, save_dir):
    """ Create each plot and return list with file paths
    """
    plotlist = []

    plotlist.append(
        create_heatmap(df, color_low, color_high, 
                       color_heatmap_border, font, save_dir)
    )
    plotlist.append(create_bar_metric_mean(df, color, font, save_dir))
    plotlist.append(create_bar_metric_sum(df, color, font, save_dir))

    return plotlist

def get_date():
    """ Return date in yyyymmdd format
    """
    return datetime.today().strftime('%Y%m%d')

def delete_files(file_list):
    """ Deletes files in file_list
    """
    for file in file_list:
        try:
            os.remove(file)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))
            
def get_aspect(image):
    """ Return aspect given an image
    """
    img = utils.ImageReader(image)
    img_width, img_height = img.getSize()
    return img_width / float (img_height)
    

def create_pdf(plotslist, dir):
    """ Create pdf with images in plotlist
    """
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
    c = canvas.Canvas(dir + get_date() + '_habits.pdf')

    for plot_group in plotslist:
        file_list = [x[0] for x in plot_group]
        habit_name = plot_group[0][1]

        c.setFont('HeiseiMin-W3', 16)
        c.drawString(260, 800, habit_name)

        aspect0 = get_aspect(file_list[0])
        aspect1 = get_aspect(file_list[1])
        aspect2 = get_aspect(file_list[2])

        x_left = 20
        x_right = 290
        y_top = 525
        y_middle = 225

        scale = 200

        c.drawImage(file_list[0],
                    x_left,
                    y_top,
                    width = scale * aspect0,
                    height = scale)

        c.drawImage(file_list[1],
                    x_right,
                    y_top,
                    width = scale * aspect1,
                    height = scale)

        c.drawImage(file_list[2],
                    x_left,
                    y_middle,
                    width = scale * aspect2,
                    height = scale)

        c.showPage()
    
    c.save()

def add_dates_before(df, date):
    """ Add empty observations to the dataframe from the Sunday
    of the week before the first date up to the first date
    """
    tuple_list = []

    start_date = date
    end_date = df['Date'][0]

    habitname = df['Name'][0]
    description = ''
    metric = 0

    daterange = pd.date_range(start_date, end_date - timedelta(days=1))

    for date in daterange:
        day_of_week = get_day_of_week(date)
        week = get_week_number(date)
        year = date.year

        tuple_list.append((habitname, date, day_of_week, week,
                           year, description, metric))

    df2 = pd.DataFrame(tuple_list)
    df2.columns = ['Name', 'Date', 'Day', 'Week', 'Year', 'Description', 'Metric']

    df3 = pd.concat([df2, df], ignore_index=True)

    return df3

def insert_missing_dates(df):
    """ Adds 2 weeks of data with metric 0 to dataframe
    """
    first_date = df['Date'][0]
    start_sunday = first_date - timedelta(days=(first_date.weekday() - 6) % 7, weeks=1)
    df = add_dates_before(df, start_sunday)

    return df

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

    df_list = create_DataFrame(habitlist, habit_dir)

    plotslist = []

    for df in df_list:
        df2 = insert_missing_dates(df)
        plotslist.append(
            create_plots(df2, color, color_low, color_high,
                         color_heatmap_border, font, save_dir)
        )

    create_pdf(plotslist, save_dir)

    delete_list = []
    for l in plotslist:
        for t in l:
            delete_list.append(t[0])
    delete_files(delete_list)
   

if __name__ == '__main__':
    main()