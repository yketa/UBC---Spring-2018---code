"""
Module cuu calculates or plots displacements and their correlations.

Files are saved according to active_particles.naming.Cuu standard.
"""

import active_particles.naming as naming

from active_particles.init import get_env
from active_particles.dat import Dat, Gsd
from active_particles.maths import relative_positions, wo_mean, g2Dto1D

from active_particles.analysis.neighbours import NeighboursGrid
from active_particles.analysis.correlations import corField2D_scalar_average,\
    corField2D_vector_average_Cnn
from active_particles.analysis.coarse_graining import SquareUniformCG,\
	CoarseGraining

def displacement(point, time, dt, positions, u_traj, dL, box_size,
    neighbours_grid):
    """
    Calculates coarse-grained displacement, density, relative displacement,
    displacement norm and displacement direction.

    Resorts to neighbours grids.

    Parameters
    ----------
    point : array like
		Coordinates of point at which to calculate shear strain and
		displacement vorticity.
	time : int
		Frame at which shear strain will be calculated.
	dt : int
		Length of the interval of time for which the displacements are
		calculated.
	positions : (N, 2) shaped array like
		Array of wrapped particle positions.
	u_traj : active_particles.dat.Dat
		Unwrapped trajectory object.
	dL : float
        Grid boxes separation.
	box_size : float
		Length of the system's square box.
	neighbours_grid : active_particles.analysis.neighbours.NeighboursGrid
		Neighbours grid.

    Returns
    -------
    [density, norm_displacement] : float list
        Concatenated density and displacement.
        NOTE: These are concatenated for dimension reasons.
        NOTE: density = 1 if there are particles, 0 otherwise.
    displacement : float array
        Displacement.
    relative_displacement : float array
        Relative displacement.
    displacement_direction : float array
        Displacement direction.
    """

    wrcut = neighbours_grid.get_neighbours(point)	# particles indexes in a square box of size dL around point
    Nwrcut = len(wrcut)                             # number of neighbouring particles
    if Nwrcut == 0:
        return [0, 0], [0, 0], [0, 0], [0, 0]       # if there is no neighbouring particles

    pos_wrcut = relative_positions(
		np.array(itemgetter(*wrcut)(positions), ndmin=2), point, box_size)	# position at time time (with boundary conditions) with point as the centre of the frame
    pos0_wrcut = u_traj.position(time, *wrcut)								# positions at time time (without periodic boundary conditions)
    pos1_wrcut = u_traj.position(time + dt, *wrcut)							# positions at time time + dt (without periodic boundary conditions)
    dis_wrcut = pos1_wrcut - pos0_wrcut										# displacements of the particles between time and time + dt
    rdis_wrcut = wo_mean(pos1_wrcut) - wo_mean(pos0_wrcut)                  # displacements of the particles between time and time + dt

    coarse_graining = CoarseGraining(SquareUniformCG(dL).factors,
		pos_wrcut)                                              # coarse graining object
    displacement = coarse_graining.average(dis_wrcut)           # coarse-grained displacement
    relative_displacement = coarse_graining.average(rdis_wrcut) # coarse-grained relative displacement
    density = (displacement != 0).any()*1                       # coarse-grained density
    norm_displacement = np.sqrt(np.sum(displacement**2))        # coarse-grained displacement norm
    try:
        displacement_direction = displacement/norm_displacemet  # coarse-grained displacement direction
    except:
        displacement_direction = [0, 0]

    return [density, norm_displacemet], displacement, relative_displacement,\
        displacement_direction

def displacement_grid(box_size, Ncases, grid_points, time, dt,
	prep_frames, w_traj, u_traj, dL):
    """
    Calculates grids of displacement, density, relative displacement,
    displacement norm and displacement direction grids.

    Resorts to neighbours grids.

    Parameters
	----------
	box_size : float
		Length of the considered system's square box.
	Ncases : int
		Number of boxes in each direction to compute the displacements.
    grid_points : array like of coordinates
		Grid points at which displacements will be evaluated.
	time : int
		Frame at which displacements will be calculated.
	dt : int
		Length of the interval of time for which the displacements are
		calculated.
	prep_frames : int
		Number of preparation frames.
	w_traj : active_particles.dat.Gsd
		Wrapped trajectory object.
	u_traj : active_particles.dat.Dat
		Unwrapped trajectory object.
	dL : float
        Grid boxes separation.
        NOTE: Equal to box_size/Ncases.

    Returns
    -------
    ndgrid : 2D array like
        Concatenated density and displacement norm grids.
        NOTE: These are concatenated for dimension reasons.
    ugrid : 2D array like
        Displacement grid.
    wgrid : 2D array like
        Relative displacement grid.
    egrid : 2D array like
        Displacement direction grid.

    Output
	------
	Prints neighbours grid computation time.
    """

    # NEIGHBOURS GRID

    startTime0 = datetime.now()	# start time for neighbours grid computation

    positions = w_traj.position(prep_frames + time +
		dt*get_env('ENDPOINT', default=False, vartype=bool))       # array of wrapped particle positions
    neighbours_grid = NeighboursGrid(positions, box_size, dL/2)    # neighbours grid

    print("Neighbours grid computation time (time = %e): %s" %
		(time, datetime.now() - startTime0))	# neighbours grid computation time

    # DISPLACEMENT GRIDS CALCULATION

    ndgrid, ugrid, wgrid, egrid = tuple(np.transpose(list(map(
		lambda point: displacement(point, time, dt, positions, u_traj, dL,
        box_size, neighbours_grid),
		grid_points)), (1, 0, 2)))	# displacement variables lists

    correct_grid = lambda grid: np.transpose(
        np.reshape(grid, (Ncases, Ncases, 2)), (1, 0, 2))[::-1]     # get grids with the same orientation as positions
    return tuple(map(correct_grid, [ndgrid, ugrid, wgrid, egrid]))  # displacement variable grid

def plot_correlation(C, C2D, C1D, C1Dcor, C_min, C_max, naming_standard,
    **directional_correlations):
    """

    """

    fig, axs = plt.subplots(2, 2)

    fig.set_size_inches(16, 16)
    fig.subplots_adjust(wspace=0.3)
    fig.subplots_adjust(hspace=0.3)

    fig.suptitle(r'$N=%.2e, \phi=%1.2f, \tilde{v}=%.2e, \tilde{\nu}_r=%.2e$'
        % (parameters['N'], parameters['density'], parameters['vzero'],
		parameters['dr']) + '\n' +
        r'$S_{init}=%.2e, \Delta t=%.2e$' % (init_frame,
		dt*parameters['period_dump']*parameters['time_step']) +
        r'$, S_{max}=%.2e, N_{cases}=%.2e$' % (int_max, Ncases))

    # C2D

    Cmin = np.min(C2D)
    Cmax = np.max(C2D)

    CvNorm = colors.Normalize(vmin=Cmin, vmax=Cmax)
    CscalarMap = cmx.ScalarMappable(norm=CvNorm, cmap=cmap)

    r_max_cases = int(r_max*(Ncases/box_size))
    C2D_display = np.roll(np.roll(C2D, int(Ncases/2), axis=0),
        int(Ncases/2), axis=1)[int(Ncases/2) - r_max_cases:
        int(Ncases/2) + r_max_cases + 1, int(Ncases/2) - r_max_cases:
        int(Ncases/2) + r_max_cases + 1]    # part of variable correlations to display

    axs[0, 0].imshow(C2D_display, cmap=cmap, norm=CvNorm,
        extent=[-r_max, r_max, -r_max, r_max])

    axs[0, 0].set_xlabel(r'$x$')
    axs[0, 0].set_ylabel(r'$y$')
    axs[0, 0].set_title('2D ' + r'$%s$' % C + ' ' +
        (r'$(%s^T/%s^L(\frac{r}{a} = %.3e) = %.3e)$'
        % (C, C, (box_size/Ncases)/a,
        directional_correlations['CT']/directional_correlations['CL'])
        if 'CL' in directional_correlations
        and 'CT' in directional_correlations else ''))

    divider = make_axes_locatable(axs[0, 0])
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cb = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=CvNorm, orientation='vertical')
    cb.set_label(r'$%s$' % C, labelpad=20, rotation=270)

    # Cuu1D shifted

    fplot(axs[1, 0])(C1D[1:, 0], C1D[1:, 1]/Cnn1D[-1, 1])

    axs[1, 0].set_xlabel(r'$r$')
    axs[1, 0].set_ylabel(r'$%s$' % C + r'$/C_{\rho\rho}(r=r_{max})$')
    axs[1, 0].set_title('radial ' + r'$%s$' % C + r'$/C_{\rho\rho}(r=r_{max})$'
        + ' ' + r'$(C_{\rho\rho}(r=r_{max}) = %.3e)$' % Cnn1D[-1, 1])

    axs[1, 0].set_xlim(r_min, r_max)
    axs[1, 0].set_ylim(C_min, C_max)

    # Cnn1D and Cuu1D

    axs[0, 1].set_title('radial ' + r'$C_{\rho\rho}$' + ' and ' + r'$%s$' % C)
    axs[0, 1].set_xlabel(r'$r$')
    axs[0, 1].set_xlim(r_min, r_max)

    axs[0, 1].plot(Cnn1D[1:, 0], Cnn1D[1:, 1], color='#1f77b4')
    axs[0, 1].set_ylabel(r'$C_{\rho\rho}$', color='#1f77b4')
    axs[0, 1].tick_params('y', colors='#1f77b4')

    ax_right = axs[0, 1].twinx()
    ax_right.semilogy(C1D[1:, 0], C1D[1:, 1], color='#ff7f0e')
    ax_right.set_ylabel(r'$%s$' % C, color='#ff7f0e', rotation=270,
        labelpad=10)
    ax_right.tick_params('y', colors='#ff7f0e')
    ax_right.set_ylim(C_min*Cnn1D[-1, 1], C_max*Cnn1D[-1, 1])

    # C1D/Cnn

    fplot(axs[1, 1])(C1Dcor[1:, 0], C1Dcor[1:, 1])

    axs[1, 1].set_xlabel(r'$r$')
    axs[1, 1].set_ylabel(r'$%s$' % C + r'$/C_{\rho\rho}$')
    axs[1, 1].set_title('radial ' + r'$%s$' % C + r'$/C_{\rho\rho}$')

    axs[1, 1].set_xlim(r_min, r_max)
    axs[1, 1].set_ylim(C_min, C_max)

    # SAVING

    if get_env('SAVE', default=False, vartype=bool):	# SAVE mode
        image_name, = naming_standard.image().filename(**attributes)
        fig.savefig(data_dir + '/' + image_name)

_r_min = 1  # default minimum radius for correlations plots
_r_max = 20	# default maximum radius for correlations plots

_Cuu_min = 1e-3 # default minimum displacement correlation for correlation plots
_Cuu_max = 1    # default maximum displacement correlation for correlation plots

_Cww_min = 1e-3 # default minimum relative displacement correlation for correlation plots
_Cww_max = 1    # default maximum relative displacement correlation for correlation plots

_Cdd_min = 1e-1 # default minimum displacement norm correlation for correlation plots
_Cdd_max = 2    # default maximum displacement norm correlation for correlation plots

_Cee_min = 1e-3 # default minimum displacement direction correlation for correlation plots
_Cee_max = 1    # default maximum displacement direction correlation for correlation plots

if __name__ == '__main__':  # executing as script

    # VARIABLE DEFINITIONS

    data_dir = get_env('DATA_DIRECTORY', default=getcwd())	# data directory

    dt = get_env('TIME', default=-1, vartype=int)	# lag time for displacement

    init_frame = get_env('INITIAL_FRAME', default=-1, vartype=int)	# frame to consider as initial
    int_max = get_env('INTERVAL_MAXIMUM', default=1, vartype=int)	# maximum number of intervals of length dt considered in correlations calculations

    parameters_file = get_env('PARAMETERS_FILE',
		default=data_dir + '/' + naming.parameters_file)	# simulation parameters file
    with open(parameters_file, 'rb') as param_file:
	       parameters = pickle.load(param_file)				# parameters hash table

    box_size = get_env('BOX_SIZE', default=parameters['box_size'],
		vartype=float)									# size of the square box to consider
    centre = (get_env('X_ZERO', default=0, vartype=float),
		get_env('Y_ZERO', default=0, vartype=float))	# centre of the box

    prep_frames = ceil(parameters['prep_steps']/parameters['period_dump'])	# number of preparation frames (FIRE energy minimisation)

    Ncases = get_env('N_CASES', default=ceil(np.sqrt(parameters['N'])),
		vartype=int)        # number of boxes in each direction to compute the shear strain and displacement vorticity grid
    dL = box_size/Ncases    # boxes separation

    Nentries = parameters['N_steps']//parameters['period_dump']		# number of time snapshots in unwrapped trajectory file
    init_frame = int(Nentries/2) if init_frame < 0 else init_frame	# initial frame
    Nframes = Nentries - init_frame									# number of frames available for the calculation

    dt = Nframes + dt if dt <= 0 else dt	# length of the interval of time for which displacements are calculated

    attributes = {'density': parameters['density'],
		'vzero': parameters['vzero'], 'dr': parameters['dr'],
		'N': parameters['N'], 'init_frame': init_frame, 'dt': dt,
		'int_max': int_max, 'Ncases': Ncases, 'box_size': box_size,
        'x_zero': centre[0], 'y_zero': centre[1]}		# attributes displayed in filenames
    naming_Cnn = naming.Cnn()                           # Cnn naming object
    Cnn_filename, = naming_Cnn.filename(**attributes)   # Cnn filename
    naming_Cuu = naming.Cuu()                           # Cuu naming object
    Cuu_filename, = naming_Cuu.filename(**attributes)   # Cuu filename
    naming_Cww = naming.Cww()                           # Cww naming object
    Cww_filename, = naming_Cww.filename(**attributes)   # Cww filename
    naming_Cdd = naming.Cdd()                           # Cdd naming object
    Cdd_filename, = naming_Cdd.filename(**attributes)   # Cdd filename
    naming_Cee = naming.Cee()                           # Cee naming object
    Cee_filename, = naming_Cee.filename(**attributes)   # Cee filename

    # MODE SELECTION

    if get_env('COMPUTE', default=False, vartype=bool):	# COMPUTE mode

        startTime = datetime.now()

		# VARIABLE DEFINITIONS

        wrap_file_name = get_env('WRAPPED_FILE',
			default=data_dir + '/' + naming.wrapped_trajectory_file)	# wrapped trajectory file (.gsd)
        unwrap_file_name = get_env('UNWRAPPED_FILE',
			default=data_dir + '/' + naming.unwrapped_trajectory_file)	# unwrapped trajectory file (.dat)

        grid_points = np.array([(x, y) for x in\
			relative_positions(np.linspace(- box_size*(1 - 1./Ncases)/2,
			box_size*(1 - 1./Ncases)/2, Ncases, endpoint=True) + centre[0],
			0, parameters['box_size'])\
			for y in\
			relative_positions(np.linspace(- box_size*(1 - 1./Ncases)/2,
			box_size*(1 - 1./Ncases)/2, Ncases, endpoint=True) + centre[1],
			0, parameters['box_size'])\
			])	# grid points at which displacements will be evaluated

        times = np.array(list(OrderedDict.fromkeys(map(
			lambda x: int(x),
			np.linspace(init_frame, Nentries - dt - 1, int_max)
			))))	# frames at which shear strain will be calculated

        # DISPLACEMENT CORRELATIONS

        with gsd.pygsd.GSDFile(open(wrap_file_name, 'rb')) as wrap_file,\
			open(unwrap_file_name, 'rb') as unwrap_file:	# opens wrapped and unwrapped trajectory files

            w_traj = Gsd(wrap_file);						# wrapped trajectory object
            u_traj = Dat(unwrap_file, parameters['N'])		# unwrapped trajectory object
            NDgrid, Ugrid, Wgrid, Egrid = tuple(np.transpose(list(map(
                lambda time: displacement_grid(parameters['box_size'], Ncases,
                grid_points, time, dt, prep_frames, w_traj, u_traj, dL)
                , times)), (1, 0, 2, 3, 4)))                # lists of displacement variables

        Ngrid = NDgrid[:, :, :, 0]  # list of density grids
        Dgrid = NDgrid[:, :, :, 1]  # list of displacement norm grids

        Cnn2D, Cdd2D = tuple(map(corField2D_scalar_average, [Ngrid, Dgrid]))    # density and displacement norm correlation grids
        (Cuu2D, CuuL, CuuT), (Cww2D, CwwL, CwwT), (Cee2D, CeeL, CeeT) = tuple(
            map(lambda Grid: corField2D_vector_average_Cnn(Grid, Cnn2D),
            [Ugrid, Wgrid, Egrid]))                                             # displacement, relative displacement and displacement direction correlation grids

        Cnn1D = g2Dto1D(Cnn2D, box_size)        # 1D density correlation
        (Cuu1D, Cuu1Dcor), (Cww1D, Cww1Dcor), (Cdd1D, Cdd1Dcor),\
            (Cee1D, Cee1Dcor) = tuple(map(
            lambda C2D:
            tuple(map(lambda C: g2Dto1D(C, box_size),
            [C2D, np.divide(C2D, Cnn, out=np.zeros(C2D.shape), where=Cnn!=0)]
            )), [Cuu2D, Cww2D, Cdd2D, Cee2D]))  # 1D displacement variables correlations

        # SAVING

        with open(data_dir + '/' + Cnn_filename, 'wb') as Cnn_dump_file,\
            open(data_dir + '/' + Cuu_filename, 'wb') as Cuu_dump_file,\
            open(data_dir + '/' + Cww_filename, 'wb') as Cww_dump_file,\
            open(data_dir + '/' + Cdd_filename, 'wb') as Cdd_dump_file,\
            open(data_dir + '/' + Cee_filename, 'wb') as Cee_dump_file:
            pickle.dump([Cnn2D, Cnn1D], Cnn_dump_file)
            pickle.dump([Cuu2D, Cuu1D, Cuu1Dcor, CuuL, CuuT], Cuu_dump_file)
            pickle.dump([Cww2D, Cww1D, Cww1Dcor, CwwL, CwwT], Cww_dump_file)
            pickle.dump([Cdd2D, Cdd1D, Cdd1Dcor], Cdd_dump_file)
            pickle.dump([Cee2D, Cee1D, Cee1Dcor, CeeL, CeeT], Cee_dump_file)

        # EXECUTION TIME

        print("Execution time: %s" % (datetime.now() - startTime))

    if get_env('PLOT', default=False, vartype=bool):	# PLOT mode

		# DATA

        with open(data_dir + '/' + Cnn_filename, 'rb') as Cnn_dump_file,\
            open(data_dir + '/' + Cuu_filename, 'rb') as Cuu_dump_file,\
            open(data_dir + '/' + Cww_filename, 'rb') as Cww_dump_file,\
            open(data_dir + '/' + Cdd_filename, 'rb') as Cdd_dump_file,\
            open(data_dir + '/' + Cee_filename, 'rb') as Cee_dump_file:
            Cnn2D, Cnn1D = pickle.load(Cnn_dump_file)
            Cuu2D, Cuu1D, Cuu1Dcor, CuuL, CuuT = pickle.load(Cuu_dump_file)
            Cww2D, Cww1D, Cww1Dcor, CwwL, CwwT = pickle.load(Cww_dump_file)
            Cdd2D, Cdd1D, Cdd1Dcor = pickle.load(Cdd_dump_file)
            Cee2D, Cee1D, Cee1Dcor, CeeL, CeeT = pickle.load(Cee_dump_file)

    if get_env('PLOT', default=False, vartype=bool) or\
		get_env('SHOW', default=False, vartype=bool):	# PLOT or SHOW mode

		# PLOT

        plot_axis = get_env('AXIS', default='LOGLOG')   # plot scales
        fplot = lambda ax: ax.loglog if plot_axis == 'LOGLOG'\
            else ax.semilogy if plot_axis == 'LINLOG'\
            else ax.semilogx if plot_axis == 'LOGLIN'\
            else ax.plot

        r_min = get_env('R_MIN', default=_r_min, vartype=float) # minimum radius for correlations plots
        r_max = get_env('R_MAX', default=_r_max, vartype=float)	# maximum radius for correlations plots
        r_max = box_size/2 if r_max < 0 else r_max	# half size of the box showed for 2D correlation

        Cuu_min = get_env('CUU_MIN', default=_Cuu_min, vartype=float)   # minimum displacement correlation for correlation plots
        Cuu_max = get_env('CUU_MAX', default=_Cuu_max, vartype=float)   # maximum displacement correlation for correlation plots

        Cww_min = get_env('CWW_MIN', default=_Cww_min, vartype=float)   # minimum relative displacement correlation for correlation plots
        Cww_max = get_env('CWW_MAX', default=_Cww_max, vartype=float)   # maximum relative displacement correlation for correlation plots

        Cdd_min = get_env('CDD_MIN', default=_Cdd_min, vartype=float)   # minimum displacement norm correlation for correlation plots
        Cdd_max = get_env('CDD_MAX', default=_Cdd_max, vartype=float)   # maximum displacement norm correlation for correlation plots

        Cee_min = get_env('CEE_MIN', default=_Cee_min, vartype=float)   # minimum displacement direction correlation for correlation plots
        Cee_max = get_env('CEE_MAX', default=_Cee_max, vartype=float)   # maximum displacement direction correlation for correlation plots

        plot_correlation('C_{uu}', Cuu2D, Cuu1D, Cuu1Dcor, Cuu_min, Cuu_max,
            naming_Cuu, CL=CuuL, CT=CuuT)
        plot_correlation('C_{\delta u \delta u}', Cww2D, Cww1D, Cww1Dcor,
            Cww_min, Cww_max, naming_Cww, CL=CwwL, CT=CwwT)
        plot_correlation('C_{|u||u|}', Cdd2D, Cdd1D, Cdd1Dcor, Cdd_min,
            Cdd_max, naming_Cdd)
        plot_correlation('C_{\hat{u}\hat{u}}', Cee2D, Cee1D, Cee1Dcor, Cee_min,
            Cee_max, naming_Cee, CL=CeeL, CT=CeeT)

        if get_env('SHOW', default=False, vartype=bool):	# SHOW mode
            plt.show()