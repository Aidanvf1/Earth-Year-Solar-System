import maya.cmds as cmds
import math
import random

# Clear scene
cmds.select(all=True)
if cmds.ls(selection=True):
    cmds.delete()

# Initialize Arnold renderer if not already set
if not cmds.objExists('defaultArnoldRenderOptions'):
    try:
        cmds.loadPlugin('mtoa', quiet=True)
    except:
        print("Warning: Arnold plugin (mtoa) could not be loaded. Some features may not work.")

# Set Arnold as the current renderer
try:
    cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')
except:
    print("Warning: Could not set Arnold as renderer. Continuing anyway...")

# Create main group
solar_system = cmds.group(empty=True, name='solar_system')

# Create Arnold Skydome Light (black background but still provides ambient lighting)
skydome = cmds.shadingNode('aiSkyDomeLight', asLight=True, name='skydome_light')
cmds.setAttr(f'{skydome}.intensity', 1.5)
cmds.setAttr(f'{skydome}.color', 0.9, 0.95, 1.0, type='double3')
cmds.setAttr(f'{skydome}.camera', 0)

# Sun with emission (glowing like a star)
sun = cmds.polySphere(r=3, name='sun')[0]
cmds.parent(sun, solar_system)
sun_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name='sun_mat')
cmds.setAttr(f'{sun_shader}.baseColor', 1, 0.8, 0, type='double3')
cmds.setAttr(f'{sun_shader}.emission', 1.0)
cmds.setAttr(f'{sun_shader}.emissionColor', 1, 0.9, 0.6, type='double3')
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

# Store planet objects for camera constraint later
planet_objects = {}

# Create planets
for name, real_au, real_radius_km, period_days, eccentricity, inclination, axial_tilt, rotation_hours, start_angle, color in planets:
    semi_major = calculate_distance(real_au)
    size = calculate_planet_size(real_radius_km)
    
    planet = cmds.polySphere(r=size, name=name)[0]
    cmds.parent(planet, solar_system)
    planet_objects[name] = planet
    
    # Apply axial tilt
    cmds.rotate(axial_tilt, 0, 0, planet, relative=True)
    
    # Create realistic planet material (non-glowing)
    shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'{name}_mat')
    cmds.setAttr(f'{shader}.baseColor', color[0], color[1], color[2], type='double3')
    cmds.setAttr(f'{shader}.specular', 0.3)
    cmds.setAttr(f'{shader}.specularRoughness', 0.6)
    cmds.setAttr(f'{shader}.metalness', 0.0)
    cmds.setAttr(f'{shader}.emission', 0.0)  # Explicitly no emission
    # No emission - planets don't glow
    cmds.select(planet)
    cmds.hyperShade(assign=shader)
    
    # Create text label for planet name
    text_result = cmds.textCurves(font='Arial', text=name.capitalize(), name=f'{name}_label')
    if isinstance(text_result, list):
        text_transform = text_result[0]
    else:
        text_transform = text_result
    
    text_parent = cmds.listRelatives(text_transform, parent=True)
    if text_parent:
        text_transform = text_parent[0]
    
    # Scale text appropriately
    text_scale = max(0.3, size * 1.5)
    cmds.scale(text_scale, text_scale, text_scale, text_transform)
    
    # Create locator group for text positioning
    text_locator = cmds.spaceLocator(name=f'{name}_text_locator')[0]
    cmds.parent(text_locator, solar_system)
    
    # Constrain locator to follow planet position
    cmds.pointConstraint(planet, text_locator, maintainOffset=False)
    
    # Parent text to locator and position above
        # Parent text to locator and position above
    cmds.parent(text_transform, text_locator)
    text_offset = size + 0.5
    cmds.setAttr(f'{text_transform}.translateY', text_offset)
    cmds.setAttr(f'{text_transform}.translateX', 0)
    cmds.setAttr(f'{text_transform}.translateZ', 0)
    
    # Setup text rendering with Arnold
    text_shapes = cmds.listRelatives(text_transform, allDescendents=True, type='nurbsCurve')
    if text_shapes:
        for shape in text_shapes:
            cmds.setAttr(f'{shape}.overrideEnabled', 1)
            cmds.setAttr(f'{shape}.overrideRGBColors', 1)
            cmds.setAttr(f'{shape}.overrideColorRGB', 1, 1, 1, type='double3')
            cmds.setAttr(f'{shape}.aiRenderCurve', 1)
            cmds.setAttr(f'{shape}.aiCurveWidth', 0.05)
            cmds.setAttr(f'{shape}.aiSampleRate', 2)
        
        text_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'{name}_text_mat')
        cmds.setAttr(f'{text_shader}.baseColor', 1, 1, 1, type='double3')
        cmds.setAttr(f'{text_shader}.emission', 1.0)
        cmds.setAttr(f'{text_shader}.emissionColor', 1, 1, 1, type='double3')
        
        cmds.select(text_transform)
        cmds.hyperShade(assign=text_shader)
    
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
    
    orbit_shape = cmds.listRelatives(orbit, shapes=True)[0]
    cmds.setAttr(f'{orbit_shape}.overrideEnabled', 1)
    cmds.setAttr(f'{orbit_shape}.overrideRGBColors', 1)
    cmds.setAttr(f'{orbit_shape}.overrideColorRGB', 1, 1, 1, type='double3')
    cmds.setAttr(f'{orbit_shape}.lineWidth', 3)
    cmds.setAttr(f'{orbit_shape}.aiRenderCurve', 1)
    cmds.setAttr(f'{orbit_shape}.aiCurveWidth', 0.05)
    cmds.setAttr(f'{orbit_shape}.aiSampleRate', 3)
    
    orbit_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'{name}_orbit_mat')
    cmds.setAttr(f'{orbit_shader}.baseColor', 1, 1, 1, type='double3')
    cmds.setAttr(f'{orbit_shader}.emission', 1.5)
    cmds.setAttr(f'{orbit_shader}.emissionColor', 1, 1, 1, type='double3')
    cmds.select(orbit)
    cmds.hyperShade(assign=orbit_shader)
    
    # Saturn's rings
    if name == 'saturn':
        ring = cmds.polyTorus(r=size * 1.8, sr=size * 0.5, name='saturn_ring')[0]
        cmds.rotate(-15, 0, 0, ring)
        cmds.scale(1, 0.02, 1, ring)
        ring_group = cmds.group(ring, name='saturn_ring_group')
        cmds.pointConstraint(planet, ring_group, maintainOffset=False)
        cmds.parent(ring_group, solar_system)
        
        ring_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name='saturn_ring_mat')
        cmds.setAttr(f'{ring_shader}.baseColor', 0.85, 0.75, 0.6, type='double3')
        cmds.setAttr(f'{ring_shader}.specular', 0.2)
        cmds.setAttr(f'{ring_shader}.specularRoughness', 0.7)
        cmds.setAttr(f'{ring_shader}.opacity', 0.8, 0.8, 0.8, type='double3')
        cmds.select(ring)
        cmds.hyperShade(assign=ring_shader)

# Set animation range
frames_per_earth_year = 1000
cmds.playbackOptions(min=1, max=frames_per_earth_year)

# Create background stars (increased from 500 to 1800)
num_stars = 1800
star_distance = 120
random.seed(123)

for i in range(num_stars):
    theta = random.uniform(0, 2 * math.pi)
    phi = random.uniform(0, math.pi)
    
    x = star_distance * math.sin(phi) * math.cos(theta)
    y = star_distance * math.sin(phi) * math.sin(theta)
    z = star_distance * math.cos(phi)
    
    star_size = random.uniform(0.05, 0.15) if random.random() < 0.9 else random.uniform(0.15, 0.3)
    
    star = cmds.polySphere(r=star_size, name=f'star_{i}')[0]
    cmds.move(x, y, z, star)
    cmds.parent(star, solar_system)
    
    star_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'star_mat_{i}')
    cmds.setAttr(f'{star_shader}.base', 0)
    cmds.setAttr(f'{star_shader}.emission', random.uniform(1.0, 2.0))
    cmds.setAttr(f'{star_shader}.emissionColor', 1, 1, 1, type='double3')
    
    cmds.select(star)
    cmds.hyperShade(assign=star_shader)

# Create Asteroid Belt between Mars and Jupiter
# Real asteroid belt: 2.2 to 3.2 AU (with safe margins from planetary orbits)
mars_distance = calculate_distance(1.524)
jupiter_distance = calculate_distance(5.203)
asteroid_belt_inner_au = 2.2
asteroid_belt_outer_au = 3.2
asteroid_belt_inner = calculate_distance(asteroid_belt_inner_au)
asteroid_belt_outer = calculate_distance(asteroid_belt_outer_au)
num_asteroids = 300
random.seed(456)

asteroid_data = []  # Store for animation later

for i in range(num_asteroids):
    distance_au = random.uniform(asteroid_belt_inner_au, asteroid_belt_outer_au)
    distance = calculate_distance(distance_au)
    start_angle = random.uniform(0, 360)
    inclination_variation = random.uniform(-2, 2)
    
    angle_rad = math.radians(start_angle)
    x = distance * math.cos(angle_rad)
    z = distance * math.sin(angle_rad)
    y = random.uniform(-0.2, 0.2)
    
    asteroid_size = random.uniform(0.02, 0.08)
    
    # Create different asteroid shapes for variety
    shape_type = random.randint(1, 4)
    if shape_type == 1:
        # Sphere
        asteroid = cmds.polySphere(r=asteroid_size, name=f'asteroid_{i}')[0]
    elif shape_type == 2:
        # Cube (rocky block)
        asteroid = cmds.polyCube(w=asteroid_size*2, h=asteroid_size*1.8, d=asteroid_size*2.2, name=f'asteroid_{i}')[0]
    elif shape_type == 3:
        # Cone (pointy asteroid)
        asteroid = cmds.polyCone(r=asteroid_size, h=asteroid_size*2.5, name=f'asteroid_{i}')[0]
    else:
        # Cylinder (tumbling rock)
        asteroid = cmds.polyCylinder(r=asteroid_size, h=asteroid_size*2, name=f'asteroid_{i}')[0]
    
    cmds.move(x, y, z, asteroid)
    cmds.parent(asteroid, solar_system)
    
    # Random rotation for variation
    cmds.rotate(random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360), asteroid)
    
    asteroid_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'asteroid_mat_{i}')
    brown_r = random.uniform(0.35, 0.5)
    brown_g = random.uniform(0.25, 0.35)
    brown_b = random.uniform(0.15, 0.25)
    cmds.setAttr(f'{asteroid_shader}.baseColor', brown_r, brown_g, brown_b, type='double3')
    cmds.setAttr(f'{asteroid_shader}.specular', 0.05)
    cmds.setAttr(f'{asteroid_shader}.specularRoughness', 0.95)
    cmds.setAttr(f'{asteroid_shader}.metalness', 0.0)
    # No emission - asteroids don't glow
    cmds.select(asteroid)
    cmds.hyperShade(assign=asteroid_shader)
    
    # Store data for animation
    asteroid_data.append({
        'name': f'asteroid_{i}',
        'distance': distance,
        'distance_au': distance_au,
        'start_angle': start_angle,
        'y_offset': y,
        'inclination': inclination_variation
    })

# Animate asteroids using Kepler's 3rd Law
for asteroid_info in asteroid_data:
    name = asteroid_info['name']
    distance_au = asteroid_info['distance_au']
    distance = asteroid_info['distance']
    start_angle = asteroid_info['start_angle']
    y_offset = asteroid_info['y_offset']
    inclination = asteroid_info['inclination']
    
    # Kepler's 3rd law: T² = a³ (where T is in Earth years, a is in AU)
    period_earth_years = math.sqrt(distance_au ** 3)
    rotations_per_earth_year = 1.0 / period_earth_years
    total_rotation = 360 * rotations_per_earth_year
    
    # Create keyframes for asteroid orbit
    num_keyframes = 20
    for frame_idx in range(num_keyframes + 1):
        frame = 1 + (frame_idx / num_keyframes) * (frames_per_earth_year - 1)
        angle_fraction = frame_idx / num_keyframes
        current_angle = start_angle - (angle_fraction * total_rotation)
        angle_rad = math.radians(current_angle)
        
        x = distance * math.cos(angle_rad)
        z = distance * math.sin(angle_rad)
        
        # Apply slight inclination
        inclination_rad = math.radians(inclination)
        y = y_offset - z * math.sin(inclination_rad)
        z_tilted = z * math.cos(inclination_rad)
        
        cmds.currentTime(frame)
        cmds.move(x, y, z_tilted, name, worldSpace=True)
        cmds.setKeyframe(name, attribute='translateX')
        cmds.setKeyframe(name, attribute='translateY')
        cmds.setKeyframe(name, attribute='translateZ')
    
    cmds.selectKey(name, attribute='translateX')
    cmds.selectKey(name, attribute='translateY', add=True)
    cmds.selectKey(name, attribute='translateZ', add=True)
    cmds.keyTangent(inTangentType='linear', outTangentType='linear')

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
        
        E = M
        for iteration in range(5):
            E = E - (E - eccentricity * math.sin(E) - M) / (1 - eccentricity * math.cos(E))
        
        true_anomaly = 2 * math.atan2(
            math.sqrt(1 + eccentricity) * math.sin(E/2),
            math.sqrt(1 - eccentricity) * math.cos(E/2)
        )
        
        r = semi_major * (1 - eccentricity**2) / (1 + eccentricity * math.cos(true_anomaly))
        x_flat = r * math.cos(true_anomaly)
        z_flat = r * math.sin(true_anomaly)
        
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

# Create Moon
earth_size = calculate_planet_size(6371)
moon_radius = earth_size * 0.2725
moon_distance = 0.8
moon_orbital_period = 27.3
moon_inclination = 5.1

moon = cmds.polySphere(r=moon_radius, name='moon')[0]
cmds.parent(moon, solar_system)

moon_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name='moon_mat')
cmds.setAttr(f'{moon_shader}.baseColor', 0.8, 0.8, 0.75, type='double3')
cmds.setAttr(f'{moon_shader}.specular', 0.2)
cmds.setAttr(f'{moon_shader}.specularRoughness', 0.8)
cmds.setAttr(f'{moon_shader}.emission', 0.0)  # Explicitly no emission
cmds.select(moon)
cmds.hyperShade(assign=moon_shader)

moon_text_result = cmds.textCurves(font='Arial', text='Moon', name='moon_label')
if isinstance(moon_text_result, list):
    moon_text_transform = moon_text_result[0]
else:
    moon_text_transform = moon_text_result

moon_text_parent = cmds.listRelatives(moon_text_transform, parent=True)
if moon_text_parent:
    moon_text_transform = moon_text_parent[0]

moon_text_scale = 0.25
cmds.scale(moon_text_scale, moon_text_scale, moon_text_scale, moon_text_transform)

# Create locator for moon text
moon_text_locator = cmds.spaceLocator(name='moon_text_locator')[0]
cmds.parent(moon_text_locator, solar_system)
cmds.pointConstraint('moon', moon_text_locator, maintainOffset=False)

# Parent moon text to locator
cmds.parent(moon_text_transform, moon_text_locator)
cmds.setAttr(f'{moon_text_transform}.translateY', moon_radius + 0.2)
cmds.setAttr(f'{moon_text_transform}.translateX', 0)
cmds.setAttr(f'{moon_text_transform}.translateZ', 0)

moon_text_shapes = cmds.listRelatives(moon_text_transform, allDescendents=True, type='nurbsCurve')
if moon_text_shapes:
    for shape in moon_text_shapes:
        cmds.setAttr(f'{shape}.overrideEnabled', 1)
        cmds.setAttr(f'{shape}.overrideRGBColors', 1)
        cmds.setAttr(f'{shape}.overrideColorRGB', 1, 1, 1, type='double3')
        cmds.setAttr(f'{shape}.aiRenderCurve', 1)
        cmds.setAttr(f'{shape}.aiCurveWidth', 0.03)
        cmds.setAttr(f'{shape}.aiSampleRate', 2)
    
    moon_text_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name='moon_text_mat')
    cmds.setAttr(f'{moon_text_shader}.baseColor', 1, 1, 1, type='double3')
    cmds.setAttr(f'{moon_text_shader}.emission', 1.0)
    cmds.setAttr(f'{moon_text_shader}.emissionColor', 1, 1, 1, type='double3')
    
    cmds.select(moon_text_transform)
    cmds.hyperShade(assign=moon_text_shader)

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

# Create camera that follows Earth from behind on its orbit
camera_result = cmds.camera(name='earth_orbit_camera')
camera_transform = camera_result[0]
camera_shape = camera_result[1]
cmds.parent(camera_transform, solar_system)

camera_distance_behind = 25.0
camera_height_offset = 5.0
num_camera_keyframes = 50

# Calculate camera positions following Earth's orbit from behind
for i in range(num_camera_keyframes + 1):
    frame = 1 + int((i / num_camera_keyframes) * (frames_per_earth_year - 1))
    cmds.currentTime(frame)
    
    earth_pos = cmds.xform('earth', query=True, worldSpace=True, translation=True)
    
    # Calculate velocity direction (tangent to orbit)
    # Get next position to determine direction
    next_i = (i + 1) % (num_camera_keyframes + 1)
    next_frame = 1 + int((next_i / num_camera_keyframes) * (frames_per_earth_year - 1))
    cmds.currentTime(next_frame)
    earth_next_pos = cmds.xform('earth', query=True, worldSpace=True, translation=True)
    cmds.currentTime(frame)
    
    # Direction vector (where Earth is going)
    dx = earth_next_pos[0] - earth_pos[0]
    dz = earth_next_pos[2] - earth_pos[2]
    
    # Normalize
    length = math.sqrt(dx*dx + dz*dz)
    if length > 0:
        dx /= length
        dz /= length
    
    # Position camera behind Earth (opposite to velocity direction)
    cam_x = earth_pos[0] - dx * camera_distance_behind
    cam_y = earth_pos[1] + camera_height_offset
    cam_z = earth_pos[2] - dz * camera_distance_behind
    
    cmds.setKeyframe(camera_transform, attribute='translateX', time=frame, value=cam_x)
    cmds.setKeyframe(camera_transform, attribute='translateY', time=frame, value=cam_y)
    cmds.setKeyframe(camera_transform, attribute='translateZ', time=frame, value=cam_z)

cmds.selectKey(camera_transform, attribute='translateX')
cmds.selectKey(camera_transform, attribute='translateY', add=True)
cmds.selectKey(camera_transform, attribute='translateZ', add=True)
cmds.keyTangent(inTangentType='spline', outTangentType='spline')

# Aim camera at Earth
cmds.aimConstraint('earth', camera_transform, 
                   maintainOffset=False,
                   aimVector=[0, 0, -1],
                   upVector=[0, 1, 0],
                   worldUpType='scene')

# Now create aim constraints for all text labels to face the camera
for name, _, _, _, _, _, _, _, _, _ in planets:
    text_locator = f'{name}_text_locator'
    if cmds.objExists(text_locator):
        # Get the text transform (child of locator)
        text_children = cmds.listRelatives(text_locator, children=True, type='transform')
        if text_children:
            for text_child in text_children:
                # Aim the text at camera
                cmds.aimConstraint(camera_transform, text_child,
                                  maintainOffset=False,
                                  aimVector=[0, 0, 1],
                                  upVector=[0, 1, 0],
                                  worldUpType='scene')

# Moon text also faces camera
if cmds.objExists('moon_text_locator'):
    moon_text_children = cmds.listRelatives('moon_text_locator', children=True, type='transform')
    if moon_text_children:
        for text_child in moon_text_children:
            cmds.aimConstraint(camera_transform, text_child,
                              maintainOffset=False,
                              aimVector=[0, 0, 1],
                              upVector=[0, 1, 0],
                              worldUpType='scene')

cmds.lookThru(camera_transform)

# Finalize
cmds.select(solar_system)
cmds.currentTime(1)

print("\nEnhanced Birthday Solar System Created!")
print("June 20, 2004 - Astronomical positions from NASA JPL Horizons")
print("1000 frames = 1 Earth year")
print("\nFeatures:")
print("- Arnold Skydome Light with black space background (intensity 1.5)")
print("- 1800 pure white background stars (distance 120)")
print("- Glowing sun with emission shader")
print("- ENHANCED orbit curves - 3x thicker lines, brighter glow (emission 1.5)")
print("- Planet name labels (Arnold renderable curves) - ALWAYS FACE CAMERA")
print("- Labels positioned DIRECTLY ABOVE planets")
print("- Realistic planet materials with aiStandardSurface (non-glowing)")
print("- Elliptical orbits with Kepler's laws")
print("- Real axial tilts and rotation periods")
print("- Counter-clockwise orbital motion")
print("- Saturn's rings with realistic material")
print("- Moon with 5.1° inclination and label")
print("- 300 asteroids in asteroid belt (2.2-3.2 AU) orbiting with Kepler's laws")
print("- Camera FOLLOWS Earth from behind along its orbit (not spinning around)")
print("\nIMPORTANT: Make sure Arnold renderer is set as your renderer for orbits and text to appear in renders!")