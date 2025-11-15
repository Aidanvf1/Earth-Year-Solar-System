import maya.cmds as cmds
import math
import random

# Clear scene
cmds.select(all=True)
if cmds.ls(selection=True):
    cmds.delete()

# Create main group
solar_system = cmds.group(empty=True, name='solar_system')

# Sun
sun = cmds.polySphere(r=3, name='sun')[0]
cmds.parent(sun, solar_system)
sun_shader = cmds.shadingNode('lambert', asShader=True, name='sun_mat')
cmds.setAttr(f'{sun_shader}.color', 1, 0.8, 0, type='double3')
cmds.select(sun)
cmds.hyperShade(assign=sun_shader)

# Planets data
planets = [
    ('mercury', 0.387, 2439, 88, 0.206, 7.0, 0.03, 1407.6, 94.9, (0.7, 0.7, 0.7)),
    ('venus', 0.723, 6052, 225, 0.007, 3.4, 177.4, 5832.5, 276.3, (0.9, 0.7, 0.4)),
    ('earth', 1.0, 6371, 365, 0.017, 0.0, 23.4, 24.0, 268.9, (0.2, 0.4, 0.8)),
    ('mars', 1.524, 3389, 687, 0.093, 1.9, 25.2, 24.6, 134.6, (0.8, 0.3, 0.2)),
    ('jupiter', 5.203, 69911, 4333, 0.048, 1.3, 3.1, 9.9, 172.1, (0.8, 0.6, 0.4)),
    ('saturn', 9.537, 58232, 10759, 0.054, 2.5, 26.7, 10.7, 106.1, (0.9, 0.8, 0.6)),
    ('uranus', 19.191, 25362, 30687, 0.046, 0.8, 97.8, 17.2, 334.0, (0.5, 0.8, 0.8)),
    ('neptune', 30.069, 24622, 60190, 0.009, 1.8, 28.3, 16.1, 313.6, (0.2, 0.3, 0.9))
]

# Distance and size calculation functions
compression = 0.6
base_scale = 8

def calculate_distance(au):
    return base_scale * (au ** compression)

def calculate_planet_size(radius_km):
    earth_radius_km = 6371
    earth_size_maya = 0.5
    scale_factor = earth_size_maya / earth_radius_km
    size_compression = 0.7
    return (radius_km * scale_factor) * (radius_km / earth_radius_km) ** (size_compression - 1)

# Create planets
for name, real_au, real_radius_km, period_days, eccentricity, inclination, axial_tilt, rotation_hours, start_angle, color in planets:
    semi_major = calculate_distance(real_au)
    size = calculate_planet_size(real_radius_km)
    
    planet = cmds.polySphere(r=size, name=name)[0]
    cmds.parent(planet, solar_system)
    
    # Apply axial tilt
    cmds.rotate(axial_tilt, 0, 0, planet, relative=True)
    
    # Color planet
    shader = cmds.shadingNode('lambert', asShader=True, name=f'{name}_mat')
    cmds.setAttr(f'{shader}.color', color[0], color[1], color[2], type='double3')
    cmds.select(planet)
    cmds.hyperShade(assign=shader)
    
    # Create elliptical orbit curve
    num_points = 100
    orbit_points = []
    for i in range(num_points + 1):
        angle = (i / num_points) * 2 * math.pi
        r = semi_major * (1 - eccentricity**2) / (1 + eccentricity * math.cos(angle))
        x = r * math.cos(angle)
        z = r * math.sin(angle)
        orbit_points.append((x, 0, z))
    
    orbit = cmds.curve(p=orbit_points, degree=3, name=f'{name}_orbit')
    cmds.rotate(inclination, 0, 0, orbit, relative=True)
    cmds.parent(orbit, solar_system)
    
    # Saturn's rings
    if name == 'saturn':
        ring = cmds.polyTorus(r=size * 1.8, sr=size * 0.5, name='saturn_ring')[0]
        cmds.rotate(-15, 0, 0, ring)
        cmds.scale(1, 0.02, 1, ring)
        ring_group = cmds.group(ring, name='saturn_ring_group')
        cmds.pointConstraint(planet, ring_group, maintainOffset=False)
        cmds.parent(ring_group, solar_system)
        
        ring_shader = cmds.shadingNode('lambert', asShader=True, name='saturn_ring_mat')
        cmds.setAttr(f'{ring_shader}.color', 0.85, 0.75, 0.6, type='double3')
        cmds.setAttr(f'{ring_shader}.transparency', 0.2, 0.2, 0.2, type='double3')
        cmds.select(ring)
        cmds.hyperShade(assign=ring_shader)

# Create Asteroid Belt
belt_inner = calculate_distance(2.2)
belt_outer = calculate_distance(3.2)
num_asteroids = 200
random.seed(42)
asteroid_data = []

for i in range(num_asteroids):
    distance = random.uniform(belt_inner, belt_outer)
    start_angle = random.uniform(0, 360)
    asteroid_size = random.uniform(0.03, 0.12)
    asteroid_au = 2.2 + (distance - belt_inner) / (belt_outer - belt_inner) * 1.0
    orbital_period_days = 365.25 * (asteroid_au ** 1.5)
    
    asteroid = cmds.polyCube(w=asteroid_size, h=asteroid_size, d=asteroid_size, name=f'asteroid_{i}')[0]
    cmds.scale(random.uniform(0.5, 2.0), random.uniform(0.5, 2.0), random.uniform(0.5, 2.0), asteroid)
    cmds.rotate(random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360), asteroid)
    
    angle_rad = math.radians(start_angle)
    x = distance * math.cos(angle_rad)
    z = distance * math.sin(angle_rad)
    y = random.uniform(-0.3, 0.3)
    
    cmds.move(x, y, z, asteroid)
    cmds.parent(asteroid, solar_system)
    
    asteroid_shader = cmds.shadingNode('lambert', asShader=True, name=f'asteroid_mat_{i}')
    gray = random.uniform(0.25, 0.5)
    brown = random.uniform(0.6, 0.9)
    cmds.setAttr(f'{asteroid_shader}.color', gray, gray * brown, gray * 0.6, type='double3')
    cmds.select(asteroid)
    cmds.hyperShade(assign=asteroid_shader)
    
    asteroid_data.append({
        'name': asteroid,
        'distance': distance,
        'start_angle': start_angle,
        'y_offset': y,
        'period_days': orbital_period_days
    })

# Set animation range
frames_per_earth_year = 1000
cmds.playbackOptions(min=1, max=frames_per_earth_year)

# Animate planets
for name, real_au, real_radius_km, period_days, eccentricity, inclination, axial_tilt, rotation_hours, start_angle, color in planets:
    semi_major = calculate_distance(real_au)
    rotations_per_earth_year = 365.25 / period_days
    total_rotation = 360 * rotations_per_earth_year
    num_keyframes = 40
    
    for frame_idx in range(num_keyframes + 1):
        frame = 1 + (frame_idx / num_keyframes) * (frames_per_earth_year - 1)
        angle_fraction = frame_idx / num_keyframes
        mean_anomaly = start_angle - (angle_fraction * total_rotation)
        M = math.radians(mean_anomaly)
        
        # Solve Kepler's equation
        E = M
        for iteration in range(5):
            E = E - (E - eccentricity * math.sin(E) - M) / (1 - eccentricity * math.cos(E))
        
        # Calculate true anomaly
        true_anomaly = 2 * math.atan2(
            math.sqrt(1 + eccentricity) * math.sin(E/2),
            math.sqrt(1 - eccentricity) * math.cos(E/2)
        )
        
        # Position calculation
        r = semi_major * (1 - eccentricity**2) / (1 + eccentricity * math.cos(true_anomaly))
        x_flat = r * math.cos(true_anomaly)
        z_flat = r * math.sin(true_anomaly)
        
        # Apply orbital inclination
        inclination_rad = math.radians(inclination)
        x = x_flat
        y = -z_flat * math.sin(inclination_rad)
        z = z_flat * math.cos(inclination_rad)
        
        cmds.currentTime(frame)
        cmds.move(x, y, z, name, worldSpace=True)
        cmds.setKeyframe(name, attribute='translateX')
        cmds.setKeyframe(name, attribute='translateY')
        cmds.setKeyframe(name, attribute='translateZ')
    
    cmds.selectKey(name, attribute='translateX')
    cmds.selectKey(name, attribute='translateY', add=True)
    cmds.selectKey(name, attribute='translateZ', add=True)
    cmds.keyTangent(inTangentType='spline', outTangentType='spline')
    
    # Planetary rotation
    hours_per_earth_year = 365.25 * 24
    rotations_per_year = hours_per_earth_year / rotation_hours
    total_rotation_degrees = 360 * rotations_per_year
    
    cmds.currentTime(1)
    cmds.setAttr(f'{name}.rotateY', 0)
    cmds.setKeyframe(name, attribute='rotateY')
    
    cmds.currentTime(frames_per_earth_year)
    if name == 'venus':
        cmds.setAttr(f'{name}.rotateY', -total_rotation_degrees)
    else:
        cmds.setAttr(f'{name}.rotateY', total_rotation_degrees)
    cmds.setKeyframe(name, attribute='rotateY')
    
    cmds.selectKey(name, attribute='rotateY')
    cmds.keyTangent(inTangentType='linear', outTangentType='linear')

# Animate asteroids
for ast_data in asteroid_data:
    name = ast_data['name']
    distance = ast_data['distance']
    start_angle = ast_data['start_angle']
    y_offset = ast_data['y_offset']
    period_days = ast_data['period_days']
    
    orbits_per_earth_year = 365.25 / period_days
    total_rotation = 360 * orbits_per_earth_year
    num_keyframes = 20
    
    for frame_idx in range(num_keyframes + 1):
        frame = 1 + (frame_idx / num_keyframes) * (frames_per_earth_year - 1)
        angle_fraction = frame_idx / num_keyframes
        current_angle = start_angle - (angle_fraction * total_rotation)
        angle_rad = math.radians(current_angle)
        
        x = distance * math.cos(angle_rad)
        z = distance * math.sin(angle_rad)
        y = y_offset
        
        cmds.currentTime(frame)
        cmds.move(x, y, z, name, worldSpace=True)
        cmds.setKeyframe(name, attribute='translateX')
        cmds.setKeyframe(name, attribute='translateY')
        cmds.setKeyframe(name, attribute='translateZ')
    
    cmds.selectKey(name, attribute='translateX')
    cmds.selectKey(name, attribute='translateY', add=True)
    cmds.selectKey(name, attribute='translateZ', add=True)
    cmds.keyTangent(inTangentType='spline', outTangentType='spline')

# Create Moon
earth_size = calculate_planet_size(6371)
moon_radius = earth_size * 0.2725
moon_distance = 0.8
moon_orbital_period = 27.3
moon_inclination = 5.1

moon = cmds.polySphere(r=moon_radius, name='moon')[0]
cmds.parent(moon, solar_system)

moon_shader = cmds.shadingNode('lambert', asShader=True, name='moon_mat')
cmds.setAttr(f'{moon_shader}.color', 0.8, 0.8, 0.75, type='double3')
cmds.select(moon)
cmds.hyperShade(assign=moon_shader)

# Animate Moon
orbits_per_year = 365.25 / moon_orbital_period
total_moon_rotation = 360 * orbits_per_year
num_moon_keyframes = int(frames_per_earth_year / 10)

for i in range(num_moon_keyframes + 1):
    frame = 1 + int((i / num_moon_keyframes) * (frames_per_earth_year - 1))
    cmds.currentTime(frame)
    
    earth_pos = cmds.xform('earth', query=True, worldSpace=True, translation=True)
    angle = -(i / num_moon_keyframes) * total_moon_rotation
    angle_rad = math.radians(angle)
    
    local_x = moon_distance * math.cos(angle_rad)
    local_z = moon_distance * math.sin(angle_rad)
    
    inclination_rad = math.radians(moon_inclination)
    local_y = local_z * math.sin(inclination_rad)
    local_z_tilted = local_z * math.cos(inclination_rad)
    
    moon_x = earth_pos[0] + local_x
    moon_y = earth_pos[1] + local_y
    moon_z = earth_pos[2] + local_z_tilted
    
    cmds.setKeyframe('moon', attribute='translateX', time=frame, value=moon_x)
    cmds.setKeyframe('moon', attribute='translateY', time=frame, value=moon_y)
    cmds.setKeyframe('moon', attribute='translateZ', time=frame, value=moon_z)

cmds.selectKey('moon', attribute='translateX')
cmds.selectKey('moon', attribute='translateY', add=True)
cmds.selectKey('moon', attribute='translateZ', add=True)
cmds.keyTangent(inTangentType='spline', outTangentType='spline')

# Finalize
cmds.select(solar_system)
cmds.viewFit()
cmds.currentTime(1)

print("\nBirthday Solar System Created!")
print("June 20, 2004 - Astronomical positions from NASA JPL Horizons")
print("1000 frames = 1 Earth year")
print("\nFeatures:")
print("- Elliptical orbits with Kepler's laws")
print("- Real axial tilts and rotation periods")
print("- Counter-clockwise orbital motion")
print("- Saturn's rings")
print("- 200 orbiting asteroids")
print("- Moon with 5.1° inclination")