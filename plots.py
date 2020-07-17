from plotnine import *
import pandas as pd

def create_heatmap(df, habit_name, color_low, color_high, color_heatmap_border, font, save_dir):
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

    return save_plot(plt, df, habit_name, (2,2), '_heatmap', save_dir)

def create_completion_num_graph(df, habit_name, color, font, save_dir):
    """ Create bar plot with the number of days per week the
    habit is completed and return tuple with file path and habit name
    """
    plt = (ggplot(df, aes(x = 'Week', y = 'Days'))
           + geom_line()
           + coord_cartesian(ylim=[0,7])
           + scale_y_continuous(labels = list(range(0, 7)),
                                breaks = list(range(0, 7)))
           + scale_x_date(breaks = pd.date_range(min(df['Week']),
                                                 max(df['Week']),
                                                 freq='W-SUN'))
           + ggtitle('Completed Days per Week')
           + theme_bw()
           + theme(figure_size = (6, 6), text=element_text(family=font, size = 13)))

    return save_plot(plt, df, habit_name, (6, 6), '_completion', save_dir)

def create_bar_metric_mean(df, habit_name, color, font, save_dir):
    """ Create bar plot with mean value of metric by day of week
    and return tuple with file path and habit name
    """
    plt = (ggplot(df, aes(x = 'Day of Week', y = 'Mean Time'))
           + geom_col(fill = color)
           + ggtitle('Mean time by Day of Week')
           + theme_bw()
           + theme(figure_size = (6, 6), text=element_text(family=font, size = 13)))

    return save_plot(plt, df, habit_name, (6, 6), '_meanbar', save_dir)

def create_bar_metric_sum(df, habit_name, color, font, save_dir):
    """ Create bar plot with total time spent for each description
    and return tuple with file path and habit name
    """
    plt = (ggplot(df, aes(x = 'Description', y = 'Hours'))
           + geom_col(fill = color)
           + coord_flip()
           + ggtitle('Sum time per Description')
           + theme_bw()
           + theme(figure_size = (6, 6), text=element_text(family=font, size = 13)))

    return save_plot(plt, df, habit_name, (6, 6), '_sumbar', save_dir)

def save_plot(plt, df, habit_name, size, suffix, save_dir):
    """ Save given plot and return file path
    """
    f = habit_name + suffix + '.png'
    file = save_dir+f
    ggsave(filename=file, plot=plt, device = 'png',
           width = size[0], height = size[1], dpi=300)
    return file