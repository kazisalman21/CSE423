from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18

import math
import random
import time

# Window dimensions
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 800

# Player properties
player_position = [0.0, 0.0, 0.0]
player_gun_angle = 90
player_speed = 5.0

enemy_radius = 30.0
enemy_speed = 0.05

GRID_SIZE = 500
MAX_BULLETS_MISSED = 10
INITIAL_LIVES = 5
score = 0
lives_remaining = INITIAL_LIVES
bullets_missed = 0
game_over = False

bullets = []
enemies = []

camera_distance = 500
camera_radius = 500
camera_angle = math.pi / 2
first_person_view = False
free_camera_mode = False
cheat_mode_active = False

def initialize_game():
    global bullets, lives_remaining, bullets_missed, score, player_gun_angle
    global first_person_view, free_camera_mode, cheat_mode_active, game_over
    global player_position

    bullets.clear()
    lives_remaining = INITIAL_LIVES
    bullets_missed = 0
    score = 0
    player_gun_angle = 90
    player_position = [0.0, 0.0, 0.0]

    first_person_view = False
    free_camera_mode = False
    cheat_mode_active = False
    game_over = False

    initialize_enemies()
    print("Game initialized. Lives:", lives_remaining)


def initialize_enemies():
    global enemies
    enemies = [create_enemy() for _ in range(5)]


def create_enemy():
    edge = random.choice(["top", "bottom", "left", "right"])
    margin = 100

    if edge == "top":
        x = random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
        y = GRID_SIZE - margin
    elif edge == "bottom":
        x = random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
        y = -GRID_SIZE + margin
    elif edge == "left":
        x = -GRID_SIZE + margin
        y = random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
    else:  # right
        x = GRID_SIZE - margin
        y = random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)

    return {"x": x, "y": y, "z": 20}

def draw_game_environment():
    grid_size = 100
    for i in range(-GRID_SIZE, GRID_SIZE, grid_size):
        for j in range(-GRID_SIZE, GRID_SIZE, grid_size):
            i_index = (i + GRID_SIZE) // grid_size
            j_index = (j + GRID_SIZE) // grid_size

            if (i_index + j_index) % 2 == 0:
                glColor3f(1.0, 1.0, 1.0)  # White
            else:
                glColor3f(0.6, 0.0, 0.9)  # Purple

            glBegin(GL_QUADS)
            glVertex3f(i, j, 0)
            glVertex3f(i + grid_size, j, 0)
            glVertex3f(i + grid_size, j + grid_size, 0)
            glVertex3f(i, j + grid_size, 0)
            glEnd()

    # Draw walls
    wall_thickness = 20
    wall_height = 100

    walls = [
        (GRID_SIZE, 0, wall_thickness, GRID_SIZE * 2, wall_height, (0, 0, 1)),  # Right wall (blue)
        (-GRID_SIZE, 0, wall_thickness, GRID_SIZE * 2, wall_height, (0, 1, 0)),  # Left wall (green)
        (0, GRID_SIZE, GRID_SIZE * 2, wall_thickness, wall_height, (1, 1, 1)),  # Top wall (white)
        (0, -GRID_SIZE, GRID_SIZE * 2, wall_thickness, wall_height, (0, 1, 1)),  # Bottom wall (cyan)
    ]

    for x, y, size_x, size_y, size_z, color in walls:
        draw_wall(x, y, size_x, size_y, size_z, color)


def draw_wall(x, y, size_x, size_y, size_z, color):
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(x, y, size_z / 2)
    glScalef(size_x, size_y, size_z)
    glutSolidCube(1)
    glPopMatrix()


def draw_player():
    glPushMatrix()
    glTranslatef(*player_position)
    glRotatef(player_gun_angle - 90, 0, 0, 1)  # Adjust for gun direction

    if game_over:
        glRotatef(90, 1, 0, 0)  # Player falls down when game over

    render_player_model(0, 0, 0)
    glPopMatrix()


def render_player_model(x, y, z):
    # Head
    glPushMatrix()
    glColor3f(0, 0, 0)  # Black
    glTranslatef(x, y, z + 100)
    gluSphere(gluNewQuadric(), 25, 10, 10)
    glPopMatrix()

    # Body
    glPushMatrix()
    glColor3f(0.33, 0.42, 0.18)  # Greenish
    glTranslatef(x, y, z + 50)
    glScalef(1, 1, 2)
    glutSolidCube(30)
    glPopMatrix()

    # Arms
    glPushMatrix()
    glColor3f(1, 0.6, 0.55)  # Skin tone
    glTranslatef(x + 20, y, z + 70)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 10, 2, 50, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(1, 0.6, 0.55)  # Skin tone
    glTranslatef(x - 20, y, z + 70)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 10, 2, 50, 10, 10)
    glPopMatrix()

    # Gun
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.1)  # Dark gray
    glTranslatef(x, y, z + 70)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 10, 2, 60, 10, 10)
    glPopMatrix()

    # Legs
    glPushMatrix()
    glColor3f(0, 0, 1)  # Blue
    glTranslatef(x + 10, y, z + 30)
    glRotatef(-180, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 10, 2, 50, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0, 0, 1)  # Blue
    glTranslatef(x - 10, y, z + 30)
    glRotatef(-180, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 10, 2, 50, 10, 10)
    glPopMatrix()


def draw_enemy(enemy):
    if game_over:
        return
    scale = 1.0 + 0.3 * math.sin(time.time() * 3)

    glPushMatrix()
    glTranslatef(enemy["x"], enemy["y"], enemy["z"])
    glScalef(scale, scale, scale)

    glColor3f(1, 0, 0)
    glutSolidSphere(enemy_radius, 20, 20)

    glPushMatrix()
    glTranslatef(0, 0, enemy_radius + 5)
    glColor3f(0, 0, 0)
    glutSolidSphere(enemy_radius / 2, 15, 15)
    glPopMatrix()

    glPopMatrix()


def draw_bullet(bullet):
    if game_over:
        return

    glPushMatrix()
    glTranslatef(bullet["x"], bullet["y"], bullet["z"])
    glColor3f(1, 0, 0)  # Red
    glutSolidCube(10)
    glPopMatrix()


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)  # White text
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)

    for character in text:
        glutBitmapCharacter(font, ord(character))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def display_game_info():
    screen_height = 800

    if game_over:
        draw_text(10, screen_height - 20, f"Game Over! Final Score: {score}")
        draw_text(10, screen_height - 40, 'Press "R" to restart the game')
        return

    info_lines = [
        f"Lives: {lives_remaining}",
        f"Score: {score}",
        f"Missed Bullets: {bullets_missed}/{MAX_BULLETS_MISSED}"
    ]

    for i, line in enumerate(info_lines):
        draw_text(10, screen_height - 20 - i * 18, line)

    if cheat_mode_active:
        draw_text(10, screen_height - 74, "CHEAT MODE: ACTIVE", GLUT_BITMAP_9_BY_15)


def fire_bullet():
    angle_radians = math.radians(player_gun_angle)
    gun_height = 70
    gun_length = 50

    bullet_x = player_position[0] + math.cos(angle_radians) * gun_length
    bullet_y = player_position[1] + math.sin(angle_radians) * gun_length
    bullet_z = player_position[2] + gun_height

    bullets.append({
        "x": bullet_x,
        "y": bullet_y,
        "z": bullet_z,
        "angle": player_gun_angle
    })

    print("Bullet fired!")


def update_game_state():
    global bullets_missed, lives_remaining, score, game_over, cheat_mode_active, player_gun_angle

    if game_over:
        return

    # Cheat mode: auto-rotate and auto-fire
    if cheat_mode_active:
        player_gun_angle = (player_gun_angle + 2) % 360

        for enemy in enemies:
            dx = enemy["x"] - player_position[0]
            dy = enemy["y"] - player_position[1]
            angle_to_enemy = (math.degrees(math.atan2(dy, dx)) + 360) % 360

            if abs(angle_to_enemy - player_gun_angle) < 1:
                fire_bullet()
                break

    active_bullets = []
    for bullet in bullets:
        angle_rad = math.radians(bullet["angle"])
        bullet_speed = 5.0

        bullet["x"] += bullet_speed * math.cos(angle_rad)
        bullet["y"] += bullet_speed * math.sin(angle_rad)

        # Check if bullet is still within game area
        if abs(bullet["x"]) < GRID_SIZE and abs(bullet["y"]) < GRID_SIZE:
            active_bullets.append(bullet)
        else:
            bullets_missed += 1
            print(f"Bullet missed! Total: {bullets_missed}")

    bullets[:] = active_bullets

    if lives_remaining <= 0 or bullets_missed >= MAX_BULLETS_MISSED:
        game_over = True
        print(f"Game Over! Final Score: {score}")
        return

    for enemy in enemies:
        dx = player_position[0] - enemy["x"]
        dy = player_position[1] - enemy["y"]
        distance = math.hypot(dx, dy)

        if distance > 0:
            enemy["x"] += enemy_speed * dx / distance
            enemy["y"] += enemy_speed * dy / distance

    for bullet in bullets[:]:
        for enemy in enemies[:]:
            distance = math.hypot(bullet["x"] - enemy["x"], bullet["y"] - enemy["y"])

            if distance < enemy_radius + 10:  # Bullet hit enemy
                bullets.remove(bullet)
                enemies.remove(enemy)
                enemies.append(create_enemy())  # Respawn enemy
                score += 1
                print(f"Enemy hit! Score: {score}")
                break

    for enemy in enemies[:]:
        distance = math.hypot(enemy["x"] - player_position[0], enemy["y"] - player_position[1])

        if distance < enemy_radius + 15:  # Enemy hit player
            enemies.remove(enemy)
            enemies.append(create_enemy())  # Respawn enemy
            lives_remaining -= 1
            print(f"Player hit! Lives remaining: {lives_remaining}")

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(120, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    angle_rad = math.radians(player_gun_angle)

    if first_person_view or (cheat_mode_active and free_camera_mode):
        eye_x = player_position[0] - math.cos(angle_rad) * 15
        eye_y = player_position[1] - math.sin(angle_rad) * 15 + 40
        eye_z = player_position[2] + 100

        center_x = player_position[0] + math.cos(angle_rad) * 100
        center_y = player_position[1] + math.sin(angle_rad) * 100
        center_z = eye_z

        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 0, 1)
    else:
        cam_x = camera_radius * math.cos(camera_angle)
        cam_y = camera_radius * math.sin(camera_angle) - 100
        cam_z = camera_distance

        gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)


def render_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setup_camera()

    if not game_over:
        update_game_state()

    draw_game_environment()

    for enemy in enemies:
        draw_enemy(enemy)

    for bullet in bullets:
        draw_bullet(bullet)

    draw_player()
    display_game_info()

    glutSwapBuffers()


def handle_keyboard(key, x, y):
    global player_gun_angle, free_camera_mode, cheat_mode_active

    if game_over and key == b"r":
        initialize_game()
        return

    if key == b"w":
        angle_rad = math.radians(player_gun_angle)
        new_x = player_position[0] + player_speed * math.cos(angle_rad)
        new_y = player_position[1] + player_speed * math.sin(angle_rad)

        if abs(new_x) < (GRID_SIZE - 50) and abs(new_y) < (GRID_SIZE - 50):
            player_position[0] = new_x
            player_position[1] = new_y

    elif key == b"s":
        angle_rad = math.radians(player_gun_angle)
        new_x = player_position[0] - player_speed * math.cos(angle_rad)
        new_y = player_position[1] - player_speed * math.sin(angle_rad)

        if abs(new_x) < (GRID_SIZE - 50) and abs(new_y) < (GRID_SIZE - 50):
            player_position[0] = new_x
            player_position[1] = new_y

    elif key == b"a":
        player_gun_angle = (player_gun_angle + 3) % 360

    elif key == b"d":
        player_gun_angle = (player_gun_angle - 3) % 360

    elif key == b"c":
        cheat_mode_active = not cheat_mode_active
        print(f"Cheat mode: {'ON' if cheat_mode_active else 'OFF'}")

    elif key == b"v" and cheat_mode_active:
        free_camera_mode = not free_camera_mode
        print(f"Free camera: {'ON' if free_camera_mode else 'OFF'}")

    elif key == b"r":
        initialize_game()
        print("Game reset!")


def handle_special_keys(key, x, y):
    global camera_angle, camera_distance

    if key == GLUT_KEY_UP:
        camera_distance += 4
    elif key == GLUT_KEY_DOWN:
        camera_distance -= 4
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 0.005
    elif key == GLUT_KEY_LEFT:
        camera_angle -= 0.005


def handle_mouse(button, state, x, y):
    global first_person_view

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        fire_bullet()

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_view = not first_person_view
        print(f"Camera mode: {'First Person' if first_person_view else 'Third Person'}")


def update_display():
    glutPostRedisplay()


glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"3D Bullet Frenzy Game")

glutDisplayFunc(render_scene)
glutIdleFunc(update_display)
glutKeyboardFunc(handle_keyboard)
glutSpecialFunc(handle_special_keys)
glutMouseFunc(handle_mouse)

initialize_game()
glutMainLoop()
