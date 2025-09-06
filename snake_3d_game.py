from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import random
import sys

# Window size globals
window_w, window_h = 1000, 800

# Game state
game_state = "MENU"  # MENU, PLAY, COLOR, DIFFICULTY, HOWTo

# Game variables
game_timer = 90.0
score = 0
is_game_over = False
win_message = ""
cheat_mode = False
last_time = 0

# NEW: Lifetime system variables
max_lives = 3
current_lives = 3

# NEW: Key state tracking for smooth controls
keys_pressed = {
    'w': False,
    's': False,
    'a': False,
    'd': False
}

difficulty_mode = "MEDIUM"  # Default mode
difficulty_settings = {
    "EASY": {
        "timer": 120.0,
        "max_speed": 100,
        "acceleration": 80,
        "collectibles_count": 12,
        "bonus_count": 3,
        "static_obstacles_count": 8,
        "color": [0, 1, 0]  # Green
    },
    "MEDIUM": {
        "timer": 90.0,
        "max_speed": 150,
        "acceleration": 120,
        "collectibles_count": 16,
        "bonus_count": 4,
        "static_obstacles_count": 12,
        "color": [1, 1, 0]  # Yellow
    },
    "HARD": {
        "timer": 60.0,
        "max_speed": 200,
        "acceleration": 160,
        "collectibles_count": 20,
        "bonus_count": 5,
        "static_obstacles_count": 16,
        "color": [1, 0, 0]  # Red
    }
}

car_pos = [0, 0, 20]
car_angle = 0
car_speed = 0
max_speed = 150
cheat_max_speed = 300
acceleration = 120
deceleration = 80
car_color = [0, 0, 1]
car_vz = 0.0
gravity = 120.0

camera_distance = 180
camera_height = 80
fovY = 60

# Object lists with depth information for manual sorting
walls = []
collectibles = []
bonus_collectibles = []
static_obstacles = []
moving_obstacles = []
ramps = []
GRID_SIZE = 500
ARENA_SIZE = 350
spin_angle = 0.0
_quad = None

# Button/GUI definitions for menu
menu_buttons = [
    {"label": "Play", "rect": [window_w // 2 - 150, window_h // 2 + 140, 300, 60], "action": "PLAY"},
    {"label": "Change Car Colour", "rect": [window_w // 2 - 150, window_h // 2 + 60, 300, 60], "action": "COLOR"},
    {"label": "Difficulty Mode", "rect": [window_w // 2 - 150, window_h // 2 - 20, 300, 60], "action": "DIFFICULTY"},
    {"label": "How to Play", "rect": [window_w // 2 - 150, window_h // 2 - 100, 300, 60], "action": "HOWTO"},
    {"label": "Exit", "rect": [window_w // 2 - 150, window_h // 2 - 180, 300, 60], "action": "EXIT"},
]
color_options = [
    {"label": "Red", "color": [1, 0, 0], "rect": [window_w // 2 - 200, window_h // 2 - 40, 80, 80]},
    {"label": "Blue", "color": [0, 0, 1], "rect": [window_w // 2 - 80, window_h // 2 - 40, 80, 80]},
    {"label": "White", "color": [1, 1, 1], "rect": [window_w // 2 + 40, window_h // 2 - 40, 80, 80]},
    {"label": "Yellow", "color": [1, 1, 0], "rect": [window_w // 2 + 160, window_h // 2 - 40, 80, 80]},
]
difficulty_buttons = [
    {"label": "Easy", "mode": "EASY", "rect": [window_w // 2 - 150, window_h // 2 + 40, 120, 60]},
    {"label": "Medium", "mode": "MEDIUM", "rect": [window_w // 2 - 60, window_h // 2 + 40, 120, 60]},
    {"label": "Hard", "mode": "HARD", "rect": [window_w // 2 + 30, window_h // 2 + 40, 120, 60]},
    {"label": "Back", "mode": None, "rect": [window_w // 2 - 60, window_h // 2 - 80, 120, 60]}
]


def apply_difficulty_settings():
    global game_timer, max_speed, acceleration
    settings = difficulty_settings[difficulty_mode]
    game_timer = settings["timer"]
    max_speed = settings["max_speed"]
    acceleration = settings["acceleration"]


def get_delta_time():
    global last_time
    current_time = time.time()
    if last_time == 0:
        last_time = current_time
        return 0.016
    delta = current_time - last_time
    last_time = current_time
    return min(delta, 0.05)


def calculate_camera_distance(pos):
    """Calculate distance from camera for depth sorting"""
    camera_x = car_pos[0] - camera_distance * math.cos(math.radians(car_angle))
    camera_y = car_pos[1] - camera_distance * math.sin(math.radians(car_angle))
    camera_z = car_pos[2] + camera_height

    dx = pos[0] - camera_x
    dy = pos[1] - camera_y
    dz = pos[2] - camera_z

    return math.sqrt(dx * dx + dy * dy + dz * dz)


def generate_random_position(min_distance_from_center=50, max_distance_from_center=300, height=15):
    """Generate a random position that's not too close to the center (car spawn)"""
    while True:
        x = random.uniform(-max_distance_from_center, max_distance_from_center)
        y = random.uniform(-max_distance_from_center, max_distance_from_center)

        # Make sure it's not too close to center and within arena bounds
        distance_from_center = math.sqrt(x * x + y * y)
        if (distance_from_center >= min_distance_from_center and
                abs(x) < ARENA_SIZE - 30 and abs(y) < ARENA_SIZE - 30):
            return [x, y, height]


def check_position_conflicts(new_pos, existing_objects, min_distance=60):
    """Check if a new position conflicts with existing objects"""
    for obj in existing_objects:
        distance = math.sqrt((new_pos[0] - obj['pos'][0]) ** 2 + (new_pos[1] - obj['pos'][1]) ** 2)
        if distance < min_distance:
            return True
    return False


def generate_random_collectibles(count):
    """Generate random collectible positions"""
    collectibles_list = []
    all_objects = walls[:]  # Start with walls to avoid conflicts

    for _ in range(count):
        attempts = 0
        while attempts < 50:  # Prevent infinite loop
            pos = generate_random_position(min_distance_from_center=60, max_distance_from_center=280, height=15)
            if not check_position_conflicts(pos, all_objects, min_distance=50):
                collectible = {'pos': pos[:], 'size': [15, 15, 15]}
                collectibles_list.append(collectible)
                all_objects.append(collectible)
                break
            attempts += 1

    return collectibles_list


def generate_random_bonus_collectibles(count, existing_objects):
    """Generate random bonus collectible positions"""
    bonus_list = []
    all_objects = existing_objects[:]

    for _ in range(count):
        attempts = 0
        while attempts < 50:
            pos = generate_random_position(min_distance_from_center=80, max_distance_from_center=320, height=20)
            if not check_position_conflicts(pos, all_objects, min_distance=70):
                bonus = {'pos': pos[:], 'size': [20, 20, 30]}
                bonus_list.append(bonus)
                all_objects.append(bonus)
                break
            attempts += 1

    return bonus_list


def generate_random_static_obstacles(count, existing_objects):
    """Generate random static obstacle positions with various shapes and sizes"""
    obstacles_list = []
    all_objects = existing_objects[:]

    obstacle_types = [
        {'size': [25, 25, 40], 'color': [0.9, 0.1, 0.1]},  # Bright Red tall block
        {'size': [40, 20, 25], 'color': [0.1, 0.9, 0.1]},  # Bright Green wide block
        {'size': [20, 40, 25], 'color': [0.1, 0.1, 0.9]},  # Bright Blue long block
        {'size': [30, 30, 50], 'color': [0.9, 0.9, 0.1]},  # Bright Yellow tall block
        {'size': [35, 15, 20], 'color': [0.9, 0.1, 0.9]},  # Bright Magenta barrier
        {'size': [25, 30, 35], 'color': [0.1, 0.9, 0.9]},  # Cyan block
        {'size': [45, 25, 20], 'color': [1.0, 0.5, 0.0]},  # Orange block
        {'size': [20, 20, 60], 'color': [0.5, 0.0, 0.5]},  # Purple tall tower
    ]

    for i in range(count):
        attempts = 0
        while attempts < 50:
            pos = generate_random_position(min_distance_from_center=70, max_distance_from_center=300, height=25)
            # Select random obstacle type
            obstacle_type = random.choice(obstacle_types)

            if not check_position_conflicts(pos, all_objects, min_distance=65):
                obstacle = {
                    'pos': pos[:],
                    'size': obstacle_type['size'][:],
                    'color': obstacle_type['color'][:]
                }
                obstacles_list.append(obstacle)
                all_objects.append(obstacle)
                break
            attempts += 1

    return obstacles_list


def reset_game():
    global game_timer, score, is_game_over, win_message, cheat_mode
    global car_pos, car_angle, car_speed
    global walls, collectibles, bonus_collectibles, static_obstacles, moving_obstacles, ramps
    global current_lives  # NEW: Reset lives

    apply_difficulty_settings()
    score = 0
    is_game_over = False
    win_message = ""
    cheat_mode = False
    car_pos = [0, 0, 20]
    car_angle = 0
    car_speed = 0
    current_lives = max_lives  # NEW: Reset lives to maximum

    # Generate arena walls (these stay the same)
    walls = []
    wall_height = 50
    wall_thickness = 20
    for i in range(-9, 10):
        walls.append(
            {'pos': [i * 40, ARENA_SIZE, wall_height / 2], 'size': [wall_thickness, wall_thickness, wall_height]})
    for i in range(-9, 10):
        walls.append(
            {'pos': [i * 40, -ARENA_SIZE, wall_height / 2], 'size': [wall_thickness, wall_thickness, wall_height]})
    for i in range(-8, 9):
        walls.append(
            {'pos': [-ARENA_SIZE, i * 40, wall_height / 2], 'size': [wall_thickness, wall_thickness, wall_height]})
    for i in range(-8, 9):
        walls.append(
            {'pos': [ARENA_SIZE, i * 40, wall_height / 2], 'size': [wall_thickness, wall_thickness, wall_height]})

    # Add some fixed internal walls for structure
    internal_walls = [
        {'pos': [150, 150, 25], 'size': [30, 30, 50]},
        {'pos': [-150, -150, 25], 'size': [30, 30, 50]},
        {'pos': [150, -150, 25], 'size': [30, 30, 50]},
        {'pos': [-150, 150, 25], 'size': [30, 30, 50]},
    ]
    walls.extend(internal_walls)

    # Get difficulty settings
    settings = difficulty_settings[difficulty_mode]
    collectible_count = settings["collectibles_count"]
    bonus_count = settings["bonus_count"]
    obstacle_count = settings["static_obstacles_count"]

    # Generate random collectibles
    collectibles = generate_random_collectibles(collectible_count)

    # Generate random bonus collectibles (avoid conflicts with regular collectibles)
    all_existing = walls + collectibles
    bonus_collectibles = generate_random_bonus_collectibles(bonus_count, all_existing)

    # Generate random static obstacles (avoid conflicts with all existing objects)
    all_existing = walls + collectibles + bonus_collectibles
    static_obstacles = generate_random_static_obstacles(obstacle_count, all_existing)

    # Generate ramps (keep these in fixed positions for now)
    ramps = []
    ramp_positions = [
        [160, 160, 15], [-160, -160, 15]
    ]
    for pos in ramp_positions:
        ramps.append({'pos': pos[:], 'size': [30, 30, 30]})

    moving_obstacles = []  # Keep empty for now

    # Update global variables
    globals().update({
        'walls': walls,
        'collectibles': collectibles,
        'bonus_collectibles': bonus_collectibles,
        'static_obstacles': static_obstacles,
        'moving_obstacles': moving_obstacles,
        'ramps': ramps
    })


def check_collision(obj1_pos, obj1_size, obj2_pos, obj2_size):
    obj1_min_x = obj1_pos[0] - obj1_size[0] / 2
    obj1_max_x = obj1_pos[0] + obj1_size[0] / 2
    obj1_min_y = obj1_pos[1] - obj1_size[1] / 2
    obj1_max_y = obj1_pos[1] + obj1_size[1] / 2
    obj1_min_z = obj1_pos[2] - obj1_size[2] / 2
    obj1_max_z = obj1_pos[2] + obj1_size[2] / 2
    obj2_min_x = obj2_pos[0] - obj2_size[0] / 2
    obj2_max_x = obj2_pos[0] + obj2_size[0] / 2
    obj2_min_y = obj2_pos[1] - obj2_size[1] / 2
    obj2_max_y = obj2_pos[1] + obj2_size[1] / 2
    obj2_min_z = obj2_pos[2] - obj2_size[2] / 2
    obj2_max_z = obj2_pos[2] + obj2_size[2] / 2
    x_overlap = obj1_max_x >= obj2_min_x and obj1_min_x <= obj2_max_x
    y_overlap = obj1_max_y >= obj2_min_y and obj1_min_y <= obj2_max_y
    z_overlap = obj1_max_z >= obj2_min_z and obj1_min_z <= obj2_max_z
    return x_overlap and y_overlap and z_overlap


def draw_car():
    glPushMatrix()
    glTranslatef(car_pos[0], car_pos[1], car_pos[2])
    glRotatef(car_angle, 0, 0, 1)

    # --- Cheat mode color override ---
    if cheat_mode:
        glColor3f(0.8, 0.5, 1.0)  # Purple when cheat mode ON
    else:
        glColor3f(car_color[0], car_color[1], car_color[2])  # Normal chosen color

    glutSolidCube(35)

    # Rest of the car unchanged...
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.2)
    glTranslatef(-20, 0, 8)
    glScalef(0.2, 1.5, 0.3)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.8, 0.8, 0.8)
    glTranslatef(0, 0, 20)
    glRotatef(90, 1, 0, 0)
    if _quad is not None:
        gluCylinder(_quad, 1, 1, 15, 4, 1)
    glPopMatrix()
    glColor3f(0.1, 0.1, 0.1)
    for (x, y) in [(12, 18), (12, -18), (-12, 18), (-12, -18)]:
        glPushMatrix()
        glTranslatef(x, y, -8)
        glutSolidCube(8)
        glPopMatrix()
    glPopMatrix()


def draw_arena():
    glBegin(GL_QUADS)
    glColor3f(0.1, 0.6, 0.1)
    glVertex3f(-GRID_SIZE, -GRID_SIZE, 0)
    glVertex3f(GRID_SIZE, -GRID_SIZE, 0)
    glVertex3f(GRID_SIZE, GRID_SIZE, 0)
    glVertex3f(-GRID_SIZE, GRID_SIZE, 0)
    glEnd()


def get_all_objects_with_depth():
    """Get all objects sorted by distance from camera (furthest first for proper rendering)"""
    all_objects = []

    # Add walls
    for wall in walls:
        all_objects.append({
            'type': 'wall',
            'obj': wall,
            'distance': calculate_camera_distance(wall['pos'])
        })

    # Add collectibles
    for collectible in collectibles:
        all_objects.append({
            'type': 'collectible',
            'obj': collectible,
            'distance': calculate_camera_distance(collectible['pos'])
        })

    # Add bonus collectibles
    for bonus in bonus_collectibles:
        all_objects.append({
            'type': 'bonus',
            'obj': bonus,
            'distance': calculate_camera_distance(bonus['pos'])
        })

    # Add static obstacles
    for obstacle in static_obstacles:
        all_objects.append({
            'type': 'obstacle',
            'obj': obstacle,
            'distance': calculate_camera_distance(obstacle['pos'])
        })

    # Add ramps
    for ramp in ramps:
        all_objects.append({
            'type': 'ramp',
            'obj': ramp,
            'distance': calculate_camera_distance(ramp['pos'])
        })

    # Sort by distance (furthest first)
    all_objects.sort(key=lambda x: x['distance'], reverse=True)

    return all_objects


def draw_objects():
    # Get all objects sorted by depth
    sorted_objects = get_all_objects_with_depth()

    # Draw objects from back to front for proper depth appearance
    for item in sorted_objects:
        obj_type = item['type']
        obj = item['obj']

        glPushMatrix()

        if obj_type == 'wall':
            glColor3f(0.6, 0.3, 0.1)
            glTranslatef(obj['pos'][0], obj['pos'][1], obj['pos'][2])
            glScalef(obj['size'][0] / 50, obj['size'][1] / 50, obj['size'][2] / 50)
            glutSolidCube(50)

        elif obj_type == 'collectible':
            glColor3f(1, 1, 0)
            glTranslatef(obj['pos'][0], obj['pos'][1], obj['pos'][2])
            glRotatef(spin_angle, 0, 0, 1)
            glutSolidCube(obj['size'][0])

        elif obj_type == 'bonus':
            glColor3f(1, 0.8, 0)
            glTranslatef(obj['pos'][0], obj['pos'][1], obj['pos'][2])
            glRotatef(spin_angle * 2, 0, 0, 1)
            glRotatef(90, 1, 0, 0)
            if _quad is not None:
                gluCylinder(_quad, 10, 10, obj['size'][2], 8, 1)

        elif obj_type == 'obstacle':
            glColor3f(obj['color'][0], obj['color'][1], obj['color'][2])
            glTranslatef(obj['pos'][0], obj['pos'][1], obj['pos'][2])
            glScalef(obj['size'][0] / 50, obj['size'][1] / 50, obj['size'][2] / 50)
            glutSolidCube(50)

        elif obj_type == 'ramp':
            glColor3f(0, 0.8, 0.8)
            glTranslatef(obj['pos'][0], obj['pos'][1], obj['pos'][2])
            glRotatef(spin_angle * 0.5, 1, 1, 0)
            glScalef(obj['size'][0] / 50, obj['size'][1] / 50, obj['size'][2] / 50)
            glutSolidCube(50)

        glPopMatrix()


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# NEW: Function to draw heart symbols for lives
def draw_heart(x, y, size=10):
    """Draw a simple heart shape using triangles"""
    glColor3f(1, 0, 0)  # Red color for hearts

    # Simple heart approximation using triangles
    glBegin(GL_TRIANGLES)
    # Top left curve
    glVertex2f(x - size / 2, y + size / 3)
    glVertex2f(x - size / 4, y + size / 2)
    glVertex2f(x, y)

    # Top right curve
    glVertex2f(x, y)
    glVertex2f(x + size / 4, y + size / 2)
    glVertex2f(x + size / 2, y + size / 3)

    # Bottom point
    glVertex2f(x - size / 2, y + size / 3)
    glVertex2f(x, y)
    glVertex2f(x + size / 2, y + size / 3)
    glEnd()


def draw_hud():
    draw_text(10, window_h - 30, f"Score: {score}")
    draw_text(10, window_h - 50, f"Time: {int(game_timer)}")
    draw_text(10, window_h - 70, f"Speed: {int(abs(car_speed))}")
    draw_text(10, window_h - 90, f"Items: {len(collectibles)}")
    draw_text(10, window_h - 110, f"Bonus: {len(bonus_collectibles)}")
    draw_text(10, window_h - 130, f"Obstacles: {len(static_obstacles)}")
    difficulty_color = difficulty_settings[difficulty_mode]["color"]
    glColor3f(difficulty_color[0], difficulty_color[1], difficulty_color[2])
    draw_text(10, window_h - 150, f"Mode: {difficulty_mode}")
    glColor3f(1, 1, 1)

    # NEW: Display lives with simple square indicators
    lives_display = f"{current_lives}/{max_lives}"
    draw_text(10, window_h - 170, f"Lives: {lives_display}")

    # Alternative visual representation with asterisks
    lives_visual = ""
    for i in range(max_lives):
        if i < current_lives:
            lives_visual += "* "  # Asterisk for remaining life
        else:
            lives_visual += "- "  # Dash for lost life
    draw_text(100, window_h - 170, f"[{lives_visual.strip()}]")

    glColor3f(1, 1, 1)  # Reset color to white

    if cheat_mode:
        draw_text(10, window_h - 200, "CHEAT MODE: SUPER SPEED!", GLUT_BITMAP_HELVETICA_12)
        glColor3f(1, 0, 1)
        draw_text(10, window_h - 220, "Press SPACE to toggle", GLUT_BITMAP_HELVETICA_10)
    if is_game_over:
        draw_text(window_w // 2 - 120, window_h // 2 + 10, win_message, GLUT_BITMAP_HELVETICA_18)
        draw_text(window_w // 2 - 60, window_h // 2 - 20, "Press 'R' to restart", GLUT_BITMAP_HELVETICA_12)


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = window_w / float(window_h)
    gluPerspective(fovY, aspect, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    camera_x = car_pos[0] - camera_distance * math.cos(math.radians(car_angle))
    camera_y = car_pos[1] - camera_distance * math.sin(math.radians(car_angle))
    camera_z = car_pos[2] + camera_height
    gluLookAt(camera_x, camera_y, camera_z, car_pos[0], car_pos[1], car_pos[2], 0, 0, 1)


def keyboardListener(key, x, y):
    """Handle key press events"""
    global cheat_mode, game_state

    # Handle key decoding
    if hasattr(key, "decode"):
        k = key.decode('utf-8').lower()
    else:
        k = chr(key).lower() if isinstance(key, int) else str(key).lower()

    # ESC returns to menu at any time
    if ord(k) == 27:  # ESC key
        game_state = "MENU"
        glutPostRedisplay()
        return

    if game_state != "PLAY":
        return

    # Handle special keys that don't need continuous pressing
    if k == ' ':  # Space bar for cheat mode toggle
        cheat_mode = not cheat_mode
        return

    if k == 'r':  # Reset game
        reset_game()
        return

    # Track movement keys being pressed
    if k in keys_pressed:
        keys_pressed[k] = True


def keyboardUpListener(key, x, y):
    """Handle key release events - NEW FUNCTION"""
    # Handle key decoding
    if hasattr(key, "decode"):
        k = key.decode('utf-8').lower()
    else:
        k = chr(key).lower() if isinstance(key, int) else str(key).lower()

    if game_state != "PLAY":
        return

    # Track movement keys being released
    if k in keys_pressed:
        keys_pressed[k] = False


def process_movement_keys(delta_time):
    """Process continuous key presses for smooth movement - NEW FUNCTION"""
    global car_speed, car_angle

    if game_state != "PLAY":
        return

    current_max_speed = cheat_max_speed if cheat_mode else max_speed
    turning_speed = 120.0  # degrees per second

    # Handle forward/backward movement
    if keys_pressed['w']:
        car_speed = min(car_speed + acceleration * delta_time, current_max_speed)
    elif keys_pressed['s']:
        car_speed = max(car_speed - acceleration * delta_time, -current_max_speed * 0.6)

    # Handle turning (only when moving fast enough)
    if abs(car_speed) > 5:
        if keys_pressed['a']:
            if car_speed > 0:  # forward
                car_angle += turning_speed * delta_time
            else:  # reverse
                car_angle -= turning_speed * delta_time
        elif keys_pressed['d']:
            if car_speed > 0:  # forward
                car_angle -= turning_speed * delta_time
            else:  # reverse
                car_angle += turning_speed * delta_time


def specialKeyListener(key, x, y):
    global camera_distance, camera_height
    if game_state != "PLAY":
        return
    if key == GLUT_KEY_LEFT:
        camera_distance += 10
    elif key == GLUT_KEY_RIGHT:
        camera_distance = max(10, camera_distance - 10)
    elif key == GLUT_KEY_UP:
        camera_height += 10
    elif key == GLUT_KEY_DOWN:
        camera_height = max(10, camera_height - 10)


def update_moving_obstacles(delta_time):
    pass


def idle():
    global car_pos, car_speed, car_angle, game_timer, score, is_game_over, win_message
    global spin_angle, car_vz, current_lives  # NEW: Added current_lives
    if game_state != "PLAY":
        glutPostRedisplay()
        return
    if is_game_over:
        glutPostRedisplay()
        return
    delta_time = get_delta_time()

    # NEW: Process movement keys continuously
    process_movement_keys(delta_time)

    spin_angle = (spin_angle + 120.0 * delta_time) % 360.0
    game_timer -= delta_time

    # Apply natural deceleration when no keys are pressed
    if not keys_pressed['w'] and not keys_pressed['s']:
        if car_speed > 0:
            car_speed = max(0, car_speed - deceleration * delta_time)
        elif car_speed < 0:
            car_speed = min(0, car_speed + deceleration * delta_time)

    prev_pos = car_pos[:]
    car_pos[0] += car_speed * math.cos(math.radians(car_angle)) * delta_time
    car_pos[1] += car_speed * math.sin(math.radians(car_angle)) * delta_time
    car_pos[2] += car_vz * delta_time
    car_vz -= gravity * delta_time
    if car_pos[2] <= 20:
        car_pos[2] = 20
        car_vz = 0
    car_size = [35, 35, 35]

    # NEW: Modified wall collision handling with lifetime system
    for wall in walls:
        if check_collision(car_pos, car_size, wall['pos'], wall['size']):
            if cheat_mode:
                car_pos[0], car_pos[1] = prev_pos[0], prev_pos[1]
                continue

            # NEW: Lifetime system for wall hits
            current_lives -= 1
            car_pos[0], car_pos[1] = prev_pos[0], prev_pos[1]  # Reset position
            car_speed = 0  # Stop the car

            if current_lives <= 0:
                is_game_over = True
                win_message = "GAME OVER - No Lives Left!"
                return
            else:
                # Brief pause/feedback for losing a life could be added here
                pass

    # NEW: Modified static obstacle collision handling with lifetime system
    for obstacle in static_obstacles:
        if check_collision(car_pos, car_size, obstacle['pos'], obstacle['size']):
            if cheat_mode:
                car_pos[0], car_pos[1] = prev_pos[0], prev_pos[1]
                continue

            # NEW: Lifetime system for obstacle hits
            current_lives -= 1
            car_pos[0], car_pos[1] = prev_pos[0], prev_pos[1]  # Reset position
            car_speed = 0  # Stop the car

            if current_lives <= 0:
                is_game_over = True
                win_message = "GAME OVER - No Lives Left!"
                return
            else:
                # Brief pause/feedback for losing a life could be added here
                pass

    # Check collectible collisions
    for collectible in collectibles[:]:
        if check_collision(car_pos, car_size, collectible['pos'], collectible['size']):
            collectibles.remove(collectible)
            score += 10

    # Check bonus collectible collisions
    for bonus in bonus_collectibles[:]:
        if check_collision(car_pos, car_size, bonus['pos'], bonus['size']):
            bonus_collectibles.remove(bonus)
            score += 50

    # Check ramp collisions
    for ramp in ramps:
        if check_collision(car_pos, car_size, ramp['pos'], ramp['size']):
            if car_pos[2] <= 21 and car_vz == 0:
                car_vz = 120.0

    # Check win/lose conditions
    if game_timer <= 0:
        is_game_over = True
        win_message = "TIME'S UP - Game Over!"
    elif len(collectibles) == 0 and len(bonus_collectibles) == 0:
        is_game_over = True
        win_message = f"YOU WIN! Final Score: {score}"
    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, window_w, window_h)
    if game_state == "MENU":
        draw_menu()
    elif game_state == "COLOR":
        draw_enhanced_color_menu()
    elif game_state == "DIFFICULTY":
        draw_enhanced_difficulty_menu()
    elif game_state == "HOWTO":
        draw_howto_screen()
    elif game_state == "PLAY":
        setupCamera()
        draw_arena()
        draw_objects()
        draw_car()
        draw_hud()
    glutSwapBuffers()


def draw_menu():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw the game title with larger font and better positioning
    glColor3f(1, 1, 1)  # White color for title
    title_text = "Car In Maze Box"
    # Calculate approximate text width for centering (rough estimation)
    title_width = len(title_text) * 12  # Approximate character width for HELVETICA_18
    title_x = (window_w - title_width) // 2
    draw_text(title_x + 15, window_h // 2 + 250, title_text, GLUT_BITMAP_TIMES_ROMAN_24)

    # Draw menu buttons with centered text
    for btn in menu_buttons:
        x, y, w, h = btn["rect"]

        # Draw button background
        glColor3f(0.4, 0.4, 0.9)
        glBegin(GL_QUADS)
        glVertex3f(x, y, 0)
        glVertex3f(x + w, y, 0)
        glVertex3f(x + w, y + h, 0)
        glVertex3f(x, y + h, 0)
        glEnd()

        # Draw centered button text
        glColor3f(1, 1, 1)
        # Calculate text width for better centering
        text_width = len(btn["label"]) * 10  # Approximate character width for HELVETICA_18
        text_x = x + (w - text_width) // 2
        text_y = y + h // 2 - 5  # Slight adjustment for vertical centering
        draw_text(text_x, text_y, btn["label"], GLUT_BITMAP_HELVETICA_18)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_enhanced_color_menu():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Title
    title_text = "Select Car Colour"
    title_width = len(title_text) * 10
    title_x = (window_w - title_width) // 2
    draw_text(title_x + 15, window_h // 2 + 130, title_text, GLUT_BITMAP_TIMES_ROMAN_24)

    # Current car preview (cube)
    glPushMatrix()
    glTranslatef(window_w // 2, window_h // 2 + 60, 0)
    glScalef(20, 20, 20)
    glColor3f(car_color[0], car_color[1], car_color[2])
    glutSolidCube(1)
    glPopMatrix()

    # Indicator box showing current color
    glColor3f(car_color[0], car_color[1], car_color[2])
    ind_x, ind_y, ind_w, ind_h = window_w // 2 + 45, window_h // 2 + 80, 100, 20
    glBegin(GL_QUADS)
    glVertex3f(ind_x, ind_y, 0)
    glVertex3f(ind_x + ind_w, ind_y, 0)
    glVertex3f(ind_x + ind_w, ind_y + ind_h, 0)
    glVertex3f(ind_x, ind_y + ind_h, 0)
    glEnd()

    # Label for indicator
    glColor3f(1, 1, 1)
    draw_text(window_w // 2 - 70, window_h // 2 + 85, "Current Colour -->", GLUT_BITMAP_HELVETICA_12)

    # Color option buttons
    for opt in color_options:
        x, y, w, h = opt["rect"]

        # Draw color button
        glColor3f(opt["color"][0], opt["color"][1], opt["color"][2])
        glBegin(GL_QUADS)
        glVertex3f(x, y, 0)
        glVertex3f(x + w, y, 0)
        glVertex3f(x + w, y + h, 0)
        glVertex3f(x, y + h, 0)
        glEnd()

        # Draw centered text with color forced right before rendering
        text_width = len(opt["label"]) * 7  # Approximate width for HELVETICA_12
        text_x = x + (w - text_width) // 2
        text_y = y + h // 2 - 3  # Vertical centering

        # Set text color and draw immediately
        if opt["label"] == "White":
            # Force black text for white button
            glColor3f(0.0, 0.0, 0.0)
        elif opt["label"] == "Yellow":
            # Force black text for yellow button
            glColor3f(0.0, 0.0, 0.0)
        else:
            # White text for red and blue buttons
            glColor3f(1.0, 1.0, 1.0)

        # Draw the text with the color set above
        glRasterPos2f(text_x, text_y)
        for char in opt["label"]:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))

    # Back button
    bx, by, bw, bh = window_w // 2 - 45, window_h // 2 - 130, 120, 50
    glColor3f(0.7, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex3f(bx, by, 0)
    glVertex3f(bx + bw, by, 0)
    glVertex3f(bx + bw, by + bh, 0)
    glVertex3f(bx, by + bh, 0)
    glEnd()

    # Centered "Back" text
    glColor3f(1, 1, 1)
    back_text_width = len("Back") * 10
    back_text_x = bx + (bw - back_text_width) // 2
    back_text_y = by + bh // 2 - 5
    draw_text(back_text_x, back_text_y, "Back", GLUT_BITMAP_HELVETICA_18)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_enhanced_difficulty_menu():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Title
    title_text = "Select Difficulty"
    title_width = len(title_text) * 10
    title_x = (window_w - title_width) // 2
    draw_text(title_x + 10, window_h // 2 + 140, title_text, GLUT_BITMAP_TIMES_ROMAN_24)

    # Fixed difficulty buttons with proper spacing
    fixed_buttons = [
        {"label": "Easy", "mode": "EASY", "rect": [window_w // 2 - 200, window_h // 2 + 40, 120, 60]},
        {"label": "Medium", "mode": "MEDIUM", "rect": [window_w // 2 - 60, window_h // 2 + 40, 120, 60]},
        {"label": "Hard", "mode": "HARD", "rect": [window_w // 2 + 80, window_h // 2 + 40, 120, 60]},
        {"label": "Back", "mode": None, "rect": [window_w // 2 - 60, window_h // 2 - 80, 120, 60]}
    ]

    # Difficulty buttons
    for btn in fixed_buttons:
        x, y, w, h = btn["rect"]

        # Button color (highlighted if current difficulty)
        if btn["mode"] == difficulty_mode:
            glColor3f(0.2, 0.8, 0.2)  # Green for selected
        else:
            glColor3f(0.4, 0.4, 0.9)  # Blue for unselected

        # Draw button background
        glBegin(GL_QUADS)
        glVertex3f(x, y, 0)
        glVertex3f(x + w, y, 0)
        glVertex3f(x + w, y + h, 0)
        glVertex3f(x, y + h, 0)
        glEnd()

        # Draw centered text
        glColor3f(1, 1, 1)
        text_width = len(btn["label"]) * 10  # Approximate width for HELVETICA_18
        text_x = x + (w - text_width) // 2
        text_y = y + h // 2 - 5  # Vertical centering
        draw_text(text_x, text_y, btn["label"], GLUT_BITMAP_HELVETICA_18)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_howto_screen():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    title = "How to Play"
    title_x = (window_w - len(title) * 12) // 2
    draw_text(title_x, window_h - 100, title, GLUT_BITMAP_TIMES_ROMAN_24)

    instructions = [
        "W - Move Forward",
        "S - Move Backward",
        "A - Turn Left",
        "D - Turn Right",
        "SPACE - Toggle Cheat Mode (Super Speed)",
        "R - Restart Game",
        "Arrow Keys - Adjust Camera View",
        "You have 3 lives per game",  # NEW: Added lifetime info
        "Hitting walls or obstacles costs 1 life",  # NEW: Added lifetime info
        "Collect yellow cubes (+10 points)",
        "Collect gold cylinders (+50 points)",
        "Hit cyan ramps to jump!",
        "ESC - Return to Menu"
    ]

    y = window_h - 200
    for line in instructions:
        draw_text(250, y, line, GLUT_BITMAP_HELVETICA_18)
        y -= 30

    # Back button
    bx, by, bw, bh = window_w // 2 - 60, 50, 120, 50
    glColor3f(0.4, 0.4, 0.9)
    glBegin(GL_QUADS)
    glVertex3f(bx, by, 0)
    glVertex3f(bx + bw, by, 0)
    glVertex3f(bx + bw, by + bh, 0)
    glVertex3f(bx, by + bh, 0)
    glEnd()
    draw_text(bx + 30, by + 20, "Back", GLUT_BITMAP_HELVETICA_18)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def mouseListener(button, state, x, y):
    global game_state, car_color, difficulty_mode
    if state != GLUT_DOWN:
        return
    mx, my = x, window_h - y  # OpenGL's origin is bottom-left, mouse is top-left
    if game_state == "MENU":
        for btn in menu_buttons:
            bx, by, bw, bh = btn["rect"]
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                if btn["action"] == "PLAY":
                    reset_game()
                    game_state = "PLAY"
                elif btn["action"] == "COLOR":
                    game_state = "COLOR"
                elif btn["action"] == "DIFFICULTY":
                    game_state = "DIFFICULTY"
                elif btn["action"] == "HOWTO":
                    game_state = "HOWTO"
                elif btn["action"] == "EXIT":
                    if hasattr(sys.modules['OpenGL.GLUT'], 'glutLeaveMainLoop'):
                        glutLeaveMainLoop()
                    else:
                        sys.exit(0)
                glutPostRedisplay()
                return
    elif game_state == "COLOR":
        for opt in color_options:
            bx, by, bw, bh = opt["rect"]
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                car_color[:] = opt["color"][:]
                glutPostRedisplay()
                return
        bx, by, bw, bh = window_w // 2 - 60, window_h // 2 - 130, 120, 50
        if bx <= mx <= bx + bw and by <= my <= by + bh:
            game_state = "MENU"
            glutPostRedisplay()
            return
    elif game_state == "DIFFICULTY":
        for btn in difficulty_buttons:
            bx, by, bw, bh = btn["rect"]
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                if btn["mode"] is not None:
                    difficulty_mode = btn["mode"]
                else:
                    game_state = "MENU"
                glutPostRedisplay()
                return
    elif game_state == "HOWTO":
        bx, by, bw, bh = window_w // 2 - 60, 50, 120, 50
        if bx <= mx <= bx + bw and by <= my <= by + bh:
            game_state = "MENU"
            glutPostRedisplay()
            return


def main():
    global _quad
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_w, window_h)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"3D Car in Maze Box")
    # Removed only glEnable(GL_DEPTH_TEST) for template compliance
    glClearColor(0.05, 0.05, 0.2, 1.0)  # Keep the dark blue background
    _quad = gluNewQuadric()
    reset_game()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)  # NEW: Add key release handler
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()