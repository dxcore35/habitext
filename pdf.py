from reportlab.pdfgen import canvas
from reportlab.lib import utils
from reportlab.platypus import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

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

def create_pdf(plotslist, dir, date):
    """ Create pdf with images in plotlist
    """
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
    c = canvas.Canvas(dir + date + '_habits.pdf')

    for plot_group in plotslist:
        c = add_text(plot_group, c)
        file_list = plot_group[2]
        c = add_images(file_list, c)

        c.showPage()
    
    c.save()