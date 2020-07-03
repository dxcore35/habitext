import os
import pandas as pd
from plotnine import *
from datetime import datetime
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

def expand_datechunks(date_chunk):
    """ Returns date, day of week, week number, and metric
    given a date chunk
    """
    date = pd.to_datetime(date_chunk[0][2:])
    day_of_week = date.strftime('%a')
    week = int(date.strftime("%U"))
    metric = day_time_total(date_chunk)

    return date, day_of_week, week, metric

def create_DataFrame(filelist, dir):
    """Given a list of markdown files their directory
    returns a DataFrame with all of the data
    """
    tuple_list = []

    for file in filelist:
        with open(dir+file, encoding='UTF-8') as f:
            lines = [line.rstrip('\n') for line in f]
            
            i = lines.index("# Log")
            metadata = lines[:i]
            log = [x for x in lines[i+1:] if x]

            habitname = get_habit_name(metadata)
            datechunk_list = chunk_by_date(log)

            for datechunk in datechunk_list:
                date, day_of_week, week, metric = expand_datechunks(datechunk)

                tuple_list.append((habitname,
                                   date,
                                   day_of_week,
                                   week,
                                   metric))

    df = pd.DataFrame(tuple_list)
    df.columns = ['Name', 'Date', 'Day', 'Week', 'Metric']
    
    return df

def split_DataFrame(df):
    """ Splits dataframe by habit name into list of dataframes
    """
    dfList = []

    habits = df['Name'].unique()

    for habit in habits:
        dfList.append(df[df['Name'] == habit].reset_index())

    return dfList

def create_heatmap(df, color_low, color_high, font):
    """ Returns tile plot created from the given dataframe
    """
    plt = (ggplot(df, aes(x = 'Week', y = 'Day', fill = 'Metric'))
        + geom_tile()
        + scale_fill_gradient(low = color_low, high = color_high)
        + ggtitle(df['Name'][0])
        + theme(text=element_text(family=font)))

    return plt

def create_bar_metric(df):
    """ Returns bar plot with mean value of metric
    by day of week
    """
    mean_by_day = df.groupby(['Day'])['Metric'].mean()
    df2 = pd.DataFrame({'Day' : mean_by_day.index,
                        'Mean' : mean_by_day.values})

    order = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    df2['Day of Week'] = pd.Categorical(df2['Day'],
                                        categories = order,
                                        ordered = True)

    plt = (ggplot(pd.DataFrame(df2), aes(x = 'Day of Week', y = 'Mean'))
        + geom_col()
        + ggtitle('Mean time by Day of Week')
        + theme_bw())

    return plt

def get_date():
    """ Return date in yyyymmdd format
    """
    return datetime.today().strftime('%Y%m%d')

def create_pdf(plotlist, dir):
    """ Create pdf with images in plotlist
    """
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
    c = canvas.Canvas(dir + get_date() + '_habits.pdf')

    for plot in plotlist:
        img = utils.ImageReader(plot[0])
        img_width, img_height = img.getSize()
        aspect = img_height / float (img_width)
        x_pos = 1
        y_pos = 300
        scale = 500
        c.setFont('HeiseiMin-W3', 16)
        c.drawString(250, 800, plot[1])
        c.drawImage(plot[0],
                    x_pos,
                    y_pos,
                    width = scale,
                    height = scale * aspect)
        c.showPage()
    
    c.save()
    
def main():
    """Create DataFrame from markdown files, split dataframes
    by habit name, create plots, and add plots to PDF
    """
    # Directories need to exist
    habit_dir = "C:/Files/Repos/habits/"
    save_dir = "C:/Files/Repos/habits/reports/"
    color_low = "white"
    color_high = "green"
    font = "MS Gothic"

    habitlist = md_file_list(habit_dir)

    df = create_DataFrame(habitlist, habit_dir)
    dfList = split_DataFrame(df)

    plotlist = []

    for df in dfList:
        plt = create_heatmap(df, color_low, color_high, font)
        habit_name = df['Name'][0]
        file = habit_name + '_heatmap' + '.png'
        ggsave(filename=save_dir+file, plot=plt, device = 'png', dpi=300)
        plotlist.append((save_dir+file, habit_name))

        plt = create_bar_metric(df)
        habit_name = df['Name'][0]
        file = habit_name + '_bar' + '.png'
        ggsave(filename=save_dir+file, plot=plt, device = 'png', dpi=300)
        plotlist.append((save_dir+file, habit_name))

    create_pdf(plotlist, save_dir)
   

if __name__ == '__main__':
    main()