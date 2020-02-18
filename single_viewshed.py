#!/usr/bin/env python3

#%module
#% description: Viewshed for CHIPS project
#% keyword: vector
#% keyword: geometry
#%end

#%option G_OPT_M_COORDS
#% key: coordinates
#%end

#%option
#% key: view_id
#% type: integer
#% required: no
#% multiple: no
#% key_desc: value
#% description: View id
#%end

#%option
#% key: direction
#% type: double
#% required: no
#% multiple: no
#% key_desc: value
#% description: Direction
#%end

#%option G_OPT_F_OUTPUT
#% key: output
#%end

import os
import grass.script as gscript


def compute_direction(main_direction):
    half_angle = 90
    mina = main_direction - half_angle
    maxa = main_direction + half_angle
    if maxa > 360:
        maxa -= 360
    if mina < 0:
        mina += 360
    return mina, maxa


def main(elevation, coords, output, pid, direction, sample):
    limit = 1000
    name = 'viewshed'
    gscript.run_command('g.region', raster=elevation)
    gscript.run_command('g.region', n=coords[1] + limit, s=coords[1] - limit,
                            e=coords[0] + limit, w=coords[0] - limit, align=elevation)
    region = gscript.region()
    mina, maxa = compute_direction(direction)
    gscript.run_command('r.viewshed', input=elevation, output=name,
                        coordinates=coords, observer_elevation=1.75,# target_elevation=3,
                        max_distance=limit, direction_range=[mina, maxa],
                        memory=65000, overwrite=True, quiet=True)
    
    # area
    cells = gscript.parse_command('r.univar', map=name, flags='g', quiet=True)['n']
    res = region['nsres']
    area = float(cells) * res * res
    # ndvi
    results = []
    # non_null_cells|null_cells|min|max|range|mean|mean_of_abs|stddev|variance|coeff_var|sum|sum_abs
    for each in sample:
        results.append(gscript.read_command('r.univar', map=name, zones=each, quiet=True, flags='t', separator='comma').strip().splitlines()[1:])

    with open(output, 'w') as f:
#        f.write("id,view_area,z1,z2,z3,z4\n")
        if pid:
            f.write("%s,%.4f,%.4f,%.4f" % (pid, coords[0], coords[1], area))
        else:
            f.write("%.4f,%.4f,%.4f" % (coords[0], coords[1], area))
        for each in results:
            zones = {}
            for line in each:
                zone, label, non_null_cells, null_cells, minim, maxim, range_, mean, mean_of_abs, stddev, variance, coeff_var,  sum_, sum_abs = line.split(',')
                zones[int(zone)] = int(non_null_cells)
            for zone in range(1, 8):
                if zone in zones:
                    area = zones[zone] * res * res
                    f.write(",%.0f" % area)
                else:
                    f.write(",0")
        f.write("\n")
    #gscript.run_command('g.remove', type='raster', name=[name], flags='f', quiet=True)


if __name__ == '__main__':
    options, flags = gscript.parser()
    pid = options['view_id']
    if not pid:
        pid = None
    coords = options['coordinates'].split(',')
    direction = float(int(options['direction']))
    # coords= 'cycle_track_viewpoints'
    main(elevation='chips_area_dem',
         coords=(float(coords[0]), float(coords[1])),
         output=options['output'],
         pid = pid,
         direction=direction,
         sample=['chips_landuse'])

