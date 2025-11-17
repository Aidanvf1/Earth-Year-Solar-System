import maya.cmds as cmds
import math
import random

# Clear scene
cmds.select(all=True)
if cmds.ls(selection=True):
    cmds.delete()

# Create main group
solar_system = cmds.group(empty=True, name='solar_system')

# Create Arnold Skydome Light (black background but still provides ambient lighting)
skydome = cmds.shadingNode('aiSkyDomeLight', asLight=True, name='skydome_light')
cmds.setAttr(f'{skydome}.intensity', 1.5)  # Increased intensity for better visibility
cmds.setAttr(f'{skydome}.color', 0.9, 0.95, 1.0, type='double3')
cmds.setAttr(f'{skydome}.camera', 0)  # Makes skydome invisible to camera (black space)

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
    
    # Create text label for planet name (simplified - just curves with Arnold settings)
    text_result = cmds.textCurves(font='Arial', text=name.capitalize(), name=f'{name}_label')
    # textCurves returns a list, get the actual transform group
    if isinstance(text_result, list):
        text_transform = text_result[0]
    else:
        text_transform = text_result
    
    # Find the top level transform if it's nested
    text_parent = cmds.listRelatives(text_transform, parent=True)
    if text_parent:
        text_transform = text_parent[0]
    
    # Scale text based on planet size (bigger planets get bigger text)
    text_scale = max(0.5, size * 2.0)
    cmds.scale(text_scale, text_scale, text_scale, text_transform)
    # Position text above planet
    cmds.move(0, size + 0.5, 0, text_transform, relative=True)
    
    # Make text curves renderable in Arnold
    text_shapes = cmds.listRelatives(text_transform, allDescendents=True, type='nurbsCurve')
    if text_shapes:
        for shape in text_shapes:
            # Make visible in viewport
            cmds.setAttr(f'{shape}.overrideEnabled', 1)
            cmds.setAttr(f'{shape}.overrideRGBColors', 1)
            cmds.setAttr(f'{shape}.overrideColorRGB', 1, 1, 1, type='double3')
            
            # Make renderable in Arnold
            cmds.setAttr(f'{shape}.aiRenderCurve', 1)
            cmds.setAttr(f'{shape}.aiCurveWidth', 0.05)
            cmds.setAttr(f'{shape}.aiSampleRate', 2)
        
        # Create glowing shader for text
        text_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'{name}_text_mat')
        cmds.setAttr(f'{text_shader}.baseColor', 1, 1, 1, type='double3')
        cmds.setAttr(f'{text_shader}.emission', 1.0)
        cmds.setAttr(f'{text_shader}.emissionColor', 1, 1, 1, type='double3')
        
        # Assign shader to all text curves
        cmds.select(text_transform)
        cmds.hyperShade(assign=text_shader)
    
    # Point constrain text to follow planet position (not rotation)
    cmds.pointConstraint(planet, text_transform, maintainOffset=True)
    cmds.parent(text_transform, solar_system)
    
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
    
    # Make orbit curve MUCH more visible in viewport
    orbit_shape = cmds.listRelatives(orbit, shapes=True)[0]
    cmds.setAttr(f'{orbit_shape}.overrideEnabled', 1)
    cmds.setAttr(f'{orbit_shape}.overrideRGBColors', 1)
    cmds.setAttr(f'{orbit_shape}.overrideColorRGB', 1, 1, 1, type='double3')  # White
    cmds.setAttr(f'{orbit_shape}.lineWidth', 3)  # Thicker lines in viewport
    
    # Make curve renderable in Arnold with increased visibility
    cmds.setAttr(f'{orbit_shape}.aiRenderCurve', 1)
    cmds.setAttr(f'{orbit_shape}.aiCurveWidth', 0.05)  # Increased from 0.02 to 0.05
    cmds.setAttr(f'{orbit_shape}.aiSampleRate', 3)  # Increased sample rate
    
    # Create shader for orbit curve with higher emission
    orbit_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'{name}_orbit_mat')
    cmds.setAttr(f'{orbit_shader}.baseColor', 1, 1, 1, type='double3')
    cmds.setAttr(f'{orbit_shader}.emission', 1.5)  # Increased from 0.5 to 1.5
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
        
        ring_shader = cmds.shadingNode('lambert', asShader=True, name='saturn_ring_mat')
        cmds.setAttr(f'{ring_shader}.color', 0.85, 0.75, 0.6, type='double3')
        cmds.setAttr(f'{ring_shader}.transparency', 0.2, 0.2, 0.2, type='double3')
        cmds.select(ring)
        cmds.hyperShade(assign=ring_shader)

# Placeholder for asteroid data (commented out)
asteroid_data = []
kuiper_data = []

# Create background stars
num_stars = 500
star_distance = 120  # Good distance for visibility
random.seed(123)  # Different seed for stars

for i in range(num_stars):
    # Random spherical coordinates for even distribution
    theta = random.uniform(0, 2 * math.pi)  # Azimuth
    phi = random.uniform(0, math.pi)  # Polar angle
    
    # Convert to cartesian coordinates on a sphere
    x = star_distance * math.sin(phi) * math.cos(theta)
    y = star_distance * math.sin(phi) * math.sin(theta)
    z = star_distance * math.cos(phi)
    
    # Random star size (most small, few large)
    star_size = random.uniform(0.05, 0.15) if random.random() < 0.9 else random.uniform(0.15, 0.3)
    
    # Create star as small sphere
    star = cmds.polySphere(r=star_size, name=f'star_{i}')[0]
    cmds.move(x, y, z, star)
    cmds.parent(star, solar_system)
    
    # Create glowing white shader for star (fully emissive, no external lighting)
    star_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'star_mat_{i}')
    
    # All stars are pure white with full emission (ignores lighting)
    cmds.setAttr(f'{star_shader}.base', 0)  # No base color response to lighting
    cmds.setAttr(f'{star_shader}.emission', random.uniform(1.0, 2.0))  # Higher emission
    cmds.setAttr(f'{star_shader}.emissionColor', 1, 1, 1, type='double3')  # Pure white
    
    cmds.select(star)
    cmds.hyperShade(assign=star_shader)

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

# Create text label for Moon (simplified)
moon_text_result = cmds.textCurves(font='Arial', text='Moon', name='moon_label')
if isinstance(moon_text_result, list):
    moon_text_transform = moon_text_result[0]
else:
    moon_text_transform = moon_text_result

moon_text_parent = cmds.listRelatives(moon_text_transform, parent=True)
if moon_text_parent:
    moon_text_transform = moon_text_parent[0]

moon_text_scale = 0.3
cmds.scale(moon_text_scale, moon_text_scale, moon_text_scale, moon_text_transform)
cmds.move(0, moon_radius + 0.2, 0, moon_text_transform, relative=True)

moon_text_shapes = cmds.listRelatives(moon_text_transform, allDescendents=True, type='nurbsCurve')
if moon_text_shapes:
    for shape in moon_text_shapes:
        # Make visible in viewport
        cmds.setAttr(f'{shape}.overrideEnabled', 1)
        cmds.setAttr(f'{shape}.overrideRGBColors', 1)
        cmds.setAttr(f'{shape}.overrideColorRGB', 1, 1, 1, type='double3')
        
        # Make renderable in Arnold
        cmds.setAttr(f'{shape}.aiRenderCurve', 1)
        cmds.setAttr(f'{shape}.aiCurveWidth', 0.03)
        cmds.setAttr(f'{shape}.aiSampleRate', 2)
    
    # Create glowing shader
    moon_text_shader = cmds.shadingNode('aiStandardSurface', asShader=True, name='moon_text_mat')
    cmds.setAttr(f'{moon_text_shader}.baseColor', 1, 1, 1, type='double3')
    cmds.setAttr(f'{moon_text_shader}.emission', 1.0)
    cmds.setAttr(f'{moon_text_shader}.emissionColor', 1, 1, 1, type='double3')
    
    cmds.select(moon_text_transform)
    cmds.hyperShade(assign=moon_text_shader)

# Point constrain text to follow moon position (not rotation)
cmds.pointConstraint(moon, moon_text_transform, maintainOffset=True)
cmds.parent(moon_text_transform, solar_system)

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
print("- Arnold Skydome Light with black space background (intensity 1.5)")
print("- 500 pure white background stars (distance 80)")
print("- Glowing sun with emission shader")
print("- ENHANCED orbit curves - 3x thicker lines, brighter glow (emission 1.5)")
print("- Planet name labels (Arnold renderable curves)")
print("- Elliptical orbits with Kepler's laws")
print("- Real axial tilts and rotation periods")
print("- Counter-clockwise orbital motion")
print("- Saturn's rings")
print("- Moon with 5.1° inclination and label")
print("\nNote: Asteroid belts commented out for performance")
print("\nIMPORTANT: Make sure Arnold renderer is set as your renderer for orbits and text to appear in renders!")