"""
Module mpl_tools provides objects to be used in matplotlib plots.
"""

import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.widgets import Slider
import matplotlib.colors as colors
import matplotlib.cm as cmx
import matplotlib as mpl
cmap = plt.cm.jet

from active_particles.maths import Grid

class FittingLine:
    """
    Provided a matplotlib.axes.Axes object, this object:
    > draws a staight line on the corresponding figure, either in a log-log
    (powerlaw fit) or in a lin-log (exponential fit) plot,
    > displays underneath the figure a slider which controls the slope of the
    line, the slider can be hidden / shown by scrolling,
    > enables switching between powerlaw and exponential fit at double click,
    > shows fitting line expression in legend.

    Clicking on the figure updates the position of the line such that it passes
    through the clicked point.

    Instances
    ---------

    FittingLine.ax : matplotlib.axes.Axes object
        Plot Axes object.

    FittingLine.x_fit : string
        x data name in legend.
    FittingLine.y_fit : string
        y data name in legend.
    FittingLine.color : any matplotlib color
        Color of fitting line.
    FittingLine.linestyle : any matplotlib linestyle
        linestyle of fitting line

    FittingLine.x0 : float
        x coordinate of clicked point
    FittingLine.y0 : float
        y coordinate of clicked point
    FittingLine.slope : float
        Slope of fitting line.

    FittingLine.line : matplotlib.lines.Line2D object
        Line2D representing fitting line.

    FittingLine.slider : matplotlib Slider widget
        Slope slider.

    FittingLine.law : string (either 'Powerlaw' or 'Exponential')
        Fitting line law.
    FittingLine.func : function (either Powerlaw or Exponential)
        Fitting line function.
    """

    def __init__(self, ax, slope, slope_min, slope_max, color='black',
        linestyle='--', **kwargs):
        """
        Parameters
        ----------
        ax : matplotlib.axes.Axes object
            Axes object on which to draw fitting line.
        slope : float
            Initial slope of fitting line in log-log plot.
        slope_min : float
            Minimum slope of fitting line for slider.
        slope_max : float
            Maximum slope of fitting line for slider.
        color : any matplotlib color
            Color of fitting line.
        linestyle : any matplotlib line style
            Line style of fitting line.

        Optional keyword arguments
        --------------------------
        x_fit : string
            Custom name of x data for fitting line expression in legend.
        y_fit : string
            Custom name of y data for fitting line expression in legend.
        """

        self.ax = ax                # Axes object
        ax.set_yscale('log')        # setting y-axis on logarithmic scale

        self.x_fit = kwargs['x_fit'] if 'x_fit' in kwargs else\
            ax.get_xlabel().replace('$', '')    # x data name in legend
        self.y_fit = kwargs['y_fit'] if 'y_fit' in kwargs else\
            ax.get_ylabel().replace('$', '')    # y data name in legend
        self.color = color                      # color of fitting line
        self.linestyle = linestyle              # linestyle of fitting line

        self.x0 = np.exp(np.ma.log(self.ax.get_xlim()).mean())  # x coordinate of clicked point
        self.y0 = np.exp(np.ma.log(self.ax.get_ylim()).mean())  # y coordinate of clicked point
        self.slope = slope                                      # slope of fitting line

        self.line, = self.ax.plot([], [], label=' ',
            color=self.color, linestyle=self.linestyle)         # Line2D representing fitting line
        self.x_legend = np.mean(self.ax.get_xlim())             # x coordinate of fitting line legend
        self.y_legend = np.mean(self.ax.get_ylim())             # y coordinate of fitting line legend
        self.legend = plt.legend(handles=[self.line], loc=10,
            bbox_to_anchor=(self.x_legend, self.y_legend),
            bbox_transform=self.ax.transData)                   # fitting line legend
        self.legend_artist = self.ax.add_artist(self.legend)    # fitting line legend artist object
        self.legend_artist.set_picker(10)                       # epsilon tolerance in points to fire pick event
        self.on_legend = False                                  # has the mouse been clicked on fitting line legend

        self.slider_ax = make_axes_locatable(self.ax).append_axes(
            'bottom', size='5%', pad=0.6)               # slider Axes
        self.slider = Slider(self.slider_ax, 'slope', slope_min, slope_max,
            valinit=slope)                              # slider
        self.slider.on_changed(self.update_slope)       # call self.update_slope when slider value is changed

        self.law = 'exponential'    # fitting line law
        self.update_law()           # initialises fitting line function, updates figure and sets legend

        self.cid_click = self.line.figure.canvas.mpl_connect(
            'button_press_event', self.on_click)        # call on click on figure
        self.cid_pick = self.line.figure.canvas.mpl_connect(
            'pick_event', self.on_pick)                 # call on artist pick on figure
        self.cid_release = self.line.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)    # call on release on figure
        self.cid_scroll = self.line.figure.canvas.mpl_connect(
            'scroll_event', self.on_scroll)             # call on scroll

    def on_click(self, event):
        """
        Executes on click.

        Double click switches between powerlaw and exponential laws and updates
        figure.
        Simple click makes fitting line pass through clicked point and updates
        figure.
        """

        if event.inaxes != self.ax:   # if Axes instance mouse is over is different than figure Axes
            return

        elif self.on_legend:    # if fitting line legend is being dragged
            return

        elif event.dblclick:    # if event is a double click
            self.update_law()   # update fitting line law (and update figure)

        else:
            self.x0 = event.xdata   # x coordinate of clicked point
            self.y0 = event.ydata   # y coordinate of clicked point
            self.draw()             # update figure

    def on_pick(self, event):
        """
        Executes on picking.

        Fitting line legend can be moved if dragged.
        """

        if event.artist == self.legend_artist:  # if fitting line legend is clicked
            self.on_legend = True               # fitting line legend has been clicked

    def on_release(self, event):
        """
        Executes on release.

        Moves fitting line legend to release position.
        """

        if not(self.on_legend): return      # if fitting line legend has not been clicked
        self.x_legend = event.xdata         # x coordinate of fitting line legend
        self.y_legend = event.ydata         # y coordinate of fitting line legend
        self.legend.set_bbox_to_anchor(bbox=(self.x_legend, self.y_legend),
            transform=self.ax.transData)    # move legend to release point
        self.line.figure.canvas.draw()      # updates legend
        self.on_legend = False              # fitting line legend has been released

    def on_scroll(self, event):
        """
        Executes on scroll.

        Hide slider if slider is visible, and vice versa.
        """

        self.slider_ax.set_visible(self.slider_ax.get_visible() == False)   # hide or show slider Axes
        self.line.figure.canvas.draw()                                      # updates figure

    def update_slope(self, val):
        """
        Set fitting line slope according to slider value and updates figure.
        """

        self.slope = self.slider.val    # updates slope of fitting line
        self.update_legend()            # updates legend and figure

    def update_law(self):
        """
        Switches between powerlaw and exponential laws and updates figure.
        """

        self.law = ['powerlaw', 'exponential'][self.law == 'powerlaw']  # switches between powerlaw and exponential
        self.func = {'powerlaw': _powerlaw,
            'exponential': _exponential}[self.law]                      # fitting line function
        self.ax.set_xscale(['linear', 'log'][self.law == 'powerlaw'])   # set x-axis scale according to fitting law
        self.update_legend()                                            # updates legend and figure

    def update_legend(self):
        """
        Updates fitting line legend.
        """

        if self.law == 'powerlaw':
            self.line.set_label(r'$%s \propto %s^{%.2e}$' % (self.y_fit,
                self.x_fit, self.slope)) # fitting line label
        elif self.law == 'exponential':
            self.line.set_label(r'$%s \propto e^{%.2e%s}$' % (self.y_fit,
                self.slope, self.x_fit)) # fitting line label

        self.legend.get_texts()[0].set_text(self.line.get_label())  # updates fitting line legend
        self.draw()                                                 # updates figure

    def draw(self):
        """
        Updates figure with desired fitting line.
        """

        self.line.set_data(self.ax.get_xlim(), list(map(
            lambda x: self.func(self.x0, self.y0, self.slope, x),
            self.ax.get_xlim()
            )))                           # line passes through clicked point according to law
        self.line.figure.canvas.draw()    # updates figure

class GridCircle:
    """
    Provided a 2D grid, this object:
    > plots the grid with a circle which centre and radius are adjustable,
    > plots values of the grid along the circle alongside the grid.
    """

    def __init__(self, grid, extent=(-1, 1, -1, 1), circle_centre=(0, 0),
        points_theta=100, show_slider=True):
        """
        Parameters
        ----------
        grid : 2D array-like
            Grid to plot values from.
        extent : scalars (left, right, bottom, top)
            Values of space variables at corners. (default: (-1, 1, -1, 1))
        circle_centre : scalars (x, y)
            Location of the centre of the circle to draw on top of grid.
        points_theta : int
            Number of points to consider in the interval [0, 2\\pi] when
            computing values along circle.
        show_slider : bool
            Display circle radius slider.
        """

        self.extent = np.array(extent)
        self.grid = Grid(grid, extent=self.extent)

        self.circle_centre = np.array(circle_centre)
        self.radius = 0 # radius of the circle
        self.points_theta = points_theta
        self.theta = np.linspace(0, 2*np.pi, points_theta)  # points used for calculations

        self.show_slider = show_slider

        self.fig, (self.ax_grid, self.ax_plot) = plt.subplots(1, 2) # matplotlib.figure.Figure object and matplotlib.axes.Axes objects for grid and value plot

        # COLORMAP

        self.min = np.min(self.grid.grid)
        self.max = np.max(self.grid.grid)

        self.norm = colors.Normalize(vmin=self.min, vmax=self.max)      # normalises data
        self.scalarmap = cmx.ScalarMappable(norm=self.norm, cmap=cmap)  # scalar map for grid values

        # GRID

        self.ax_grid.imshow(self.grid.grid, cmap=cmap, norm=self.norm,
            extent=self.extent) # grid

        self.colormap_ax = make_axes_locatable(self.ax_grid).append_axes(
            'right', size='5%', pad=0.05)           # color map axes
        self.colormap = mpl.colorbar.ColorbarBase(self.colormap_ax, cmap=cmap,
            norm=self.norm, orientation='vertical')    # color map

        self.circle = plt.Circle(self.circle_centre, self.radius,
            color='black', fill=False) # circle on grid
        self.ax_grid.add_artist(self.circle)

        self.ax_grid.figure.canvas.mpl_connect('button_press_event',
            self.update_grid)   # call self.update_grid() on button press event

        # PLOT

        self.ax_plot.set_ylim([self.min, self.max]) # setting y-axis limit of plot as grid extrema
        self.ax_plot.set_xlim([0, 2*np.pi])         # angle on the cirlce

        self.line, = self.ax_plot.plot(np.linspace(0, 2*np.pi,
        self.points_theta), [0]*self.points_theta)  # plot of values along circle

        # SLIDER

        if self.show_slider:

            self.slider_ax = make_axes_locatable(self.ax_plot).append_axes(
                'bottom', size='5%', pad=0.5)                       # slider axes
            self.slider = Slider(self.slider_ax, 'radius', 0,
                np.min(np.abs(self.extent)), valinit=self.radius)   # slider

            self.slider.on_changed(self.update_slider)  # call self.update_slider() on slider update

        # DRAW

        self.draw() # updates circle and plot

    def get_fig_ax_cmap(self):
        """
        Returns
        -------
        fig : matplotlib.pyplot.figure object
            Figure.
        (ax_grid, ax_plot) : matplotlib.axes.Axes tuple
            Grid and plot axes.
        colormap : matplotlib.colorbar.ColorbarBase object
            Color map.
        """

        return self.fig, (self.ax_grid, self.ax_plot), self.colormap

    def update_grid(self, event):
        """
        Executes on click on figure.

        Updates radius of cirlce on figure.
        """

        if event.inaxes != self.circle.axes: return # if Axes instance mouse is over is different than circle's figure Axes

        self.radius = np.sqrt(np.sum((np.array([event.xdata, event.ydata])
            - self.circle_centre)**2))      # radius set to distance between centre of circle and clicked point
        self.slider.set_val(self.radius)    # updates slider value

        self.draw() # updates figure

    def update_slider(self, event):
        """
        Executes on slider change.

        Updates radius of circle on figure.
        """

        self.radius = self.slider.val   # radius set to slider value

        self.draw() # updates figure

    def draw(self):
        """
        Updates figure.
        """

        self.line.set_ydata(list(map(
            lambda angle: self.grid.get_value_polar(self.radius, angle,
            centre=self.circle_centre), self.theta)))   # values of the grid along the circle

        self.circle.set_radius(self.radius) # adjusting circle radius

        self.ax_grid.figure.canvas.draw()   # updating grid
        self.ax_plot.figure.canvas.draw()   # updating plot

def _powerlaw(x0, y0, slope, x):
    """
    From point (x0, y0) and parameter slope, returns y = f(x) such that:
    > f(x) = a * (x ** slope)
    > f(x0) = y0

    Parameters
    ----------
    x0, y0, slope, x : float

    Returns
    -------
    y = f(x) : float
    """

    return y0 * ((x/x0) ** slope)

def _exponential(x0, y0, slope, x):
    """
    From point (x0, y0) and parameter slope, returns y = f(x) such that:
    > f(x) = a * exp(x * slope)
    > f(x0) = y0

    Parameters
    ----------
    x0, y0, slope, x : float

    Returns
    -------
    y = f(x) : float
    """

    return y0 * np.exp((x - x0) * slope)
