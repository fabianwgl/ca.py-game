import sys, random
import pygame
from pygame.locals import *
from pygame import mixer

pygame.init()
mixer.init()

mixer.music.load('lloyd.wav')

mixer.music.set_volume(0.5)

pygame.display.set_caption('capi the game')
WINDOW_SIZE = (900, 506)
screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)
display = pygame.Surface(WINDOW_SIZE)

clock = pygame.time.Clock()
game_map = {}

ground_image = pygame.image.load('earth/sprite_01.png')
dirt_image = pygame.image.load('earth/sprite_05.png')
oak_seed_image = pygame.image.load('oak_seed.png')

TILE_SIZE = ground_image.get_width()
TILE_SIZE_SCALE = round(TILE_SIZE*0.05)
ground_image_resized = pygame.transform.scale(ground_image,(TILE_SIZE_SCALE, TILE_SIZE_SCALE))
dirt_image_resized = pygame.transform.scale(dirt_image,(TILE_SIZE_SCALE, TILE_SIZE_SCALE))

tile_index = {  1: ground_image_resized,
                2: dirt_image_resized,
                3: oak_seed_image
            }

bg1_image = pygame.image.load('clouds/1.png')
bg2_image = pygame.image.load('clouds/6.png')
bg3_image = pygame.image.load('clouds/2.png')
bg4_image = pygame.image.load('clouds/4.png')
bg4_image.set_alpha(200)
bg5_image = pygame.image.load('clouds/5.png')

single_cloud_image = pygame.image.load('clouds/3.png')
single_cloud_image.set_alpha(230)

# print(bg1_image.get_height())
# print(bg1_image.get_width())

CHUNK_SIZE = 8
def generate_chunk(x,y):
    chunk_data = []
    for y_pos in range(CHUNK_SIZE):
        for x_pos in range(CHUNK_SIZE):
            target_x = x * CHUNK_SIZE + x_pos
            target_y = y * CHUNK_SIZE + y_pos
            tile_type = 0
            if target_y > 10:
                tile_type = 2 # dirt
            elif target_y == 10:
                tile_type = 1 # grass
            elif target_y == 9:
                if random.randint(1,2) == 1: # chance of spawning an oak seed
                    tile_type = 3 # oak seed
            if tile_type != 0:
                chunk_data.append([[target_x, target_y], tile_type])
    return chunk_data


def collision_test(rect, tiles):
    hit_list = []
    for tile in tiles:
        if rect.colliderect(tile):
            hit_list.append(tile)
    return hit_list

def move(rect, movement, tiles):
    collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

    rect.x += movement[0]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[0] > 0:
            rect.right = tile.left
            collision_types['right'] = True
        elif movement[0] < 0:
            rect.left = tile.right
            collision_types['left'] = True

    rect.y += movement[1]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[1] > 0:
            rect.bottom = tile.top
            collision_types['bottom'] = True
        elif movement[1] < 0:
            rect.top = tile.bottom
            collision_types['top'] = True

    return rect, collision_types

global animation_frames
animation_frames = {}

def load_animation(path, frame_durations):
    global animation_frames
    animation_name = path.split('/')[-1]
    animation_frame_data = []
    n = 0
    for frame in frame_durations:
        animation_frame_id = animation_name+'-'+str(n)
        img_location = path+'/'+animation_frame_id+'.png'
        animation_image = pygame.image.load(img_location).convert()
        animation_image.set_colorkey((255, 255, 255, 255))
        animation_frames[animation_frame_id] = animation_image.copy()
        for i in range(frame):
            animation_frame_data.append(animation_frame_id)
        n += 1
    return animation_frame_data

def change_action(action_var, frame, new_value):
    if action_var != new_value:
        action_var = new_value
        frame = 0
    return action_var,frame

#   load animation database
animation_database = {}
animation_database['walk'] = load_animation('capy/walk', [4,4,4,4,4,4,4,4])
animation_database['sitting-idle'] = load_animation('capy/sitting-idle', [4,4,4,4,4,4,4,4])
animation_database['idle'] = load_animation('capy/idle', [4,4,4,4,4,4,4,4])
animation_database['munch'] = load_animation('capy/munch', [4,4,4,4,4,4,4,4])

player_action = 'walk'
player_frame = 0
player_flip = False

moving_right = False
moving_left = False
moving_up = False
moving_down = False

player_location = [20, 20]
player_y_momentum = 0
player_is_jumping = False
velocity = 0.2

true_scroll = [0,0]

player_rect = pygame.Rect(200, 200, 64, 45)

print("TILE SIZE "+str(TILE_SIZE*0.05))

FACTOR_SCALE = 1.6
PLAYER_MOVEMENT_SPEED = 3

#   draw background
image = pygame.transform.scale(bg1_image, (bg1_image.get_width()*FACTOR_SCALE, bg1_image.get_height()*FACTOR_SCALE))
image2 = pygame.transform.scale(bg2_image, (bg2_image.get_width()*FACTOR_SCALE, bg2_image.get_height()*FACTOR_SCALE))
image3 = pygame.transform.scale(bg3_image, (bg3_image.get_width()*FACTOR_SCALE, bg3_image.get_height()*FACTOR_SCALE))
image5 = pygame.transform.scale(bg5_image, (bg5_image.get_width()*FACTOR_SCALE, bg5_image.get_height()*FACTOR_SCALE))

image4 = pygame.transform.scale(bg4_image, (bg4_image.get_width()*FACTOR_SCALE, bg4_image.get_height()*FACTOR_SCALE))
image4_x = -20
image4_return = False

cloud = pygame.transform.scale(single_cloud_image, (single_cloud_image.get_width(), single_cloud_image.get_height()))
cloud_x = 0

mixer.music.play()
img3_x = 0
clouds_x = 0
clouds_y = 0
main_text = "Oak seeds"
seed_amount = 0
alpha = 300

last_oak_rect = pygame.Rect(0, 0, 1, 1)
eaten_oaks = []

main_font_french = pygame.font.SysFont('Verdana', 50)
main_font = pygame.font.SysFont('Verdana', 20)

player_ticks_idle = 0

run = True
while run:
    #   scroll and camera offset
    true_scroll[0] += (player_rect.x-true_scroll[0]-300)/5
    true_scroll[1] += (player_rect.y-true_scroll[1]-400)/5
    #   purify scroll integers 
    scroll = true_scroll.copy()
    scroll[0] = int(scroll[0])
    scroll[1] = int(scroll[1])

    #   draw background
    display.blit(image, (0, 0))
    display.blit(image2, (0, 0))
    image3.set_alpha(alpha)
    display.blit(image3, (clouds_x, clouds_y-10))
    
    #   create and render background poem
    main_text_render = main_font.render(f"{str(seed_amount)} {main_text}", True, (0,0,0))
    main_text_render.set_alpha(125)
    display.blit(main_text_render, (100, 100))


    display.blit(image5, (clouds_x, clouds_y-10))

    #   lullaby clouds animation
    # display.blit(cloud, (clouds_x, clouds_y))
    image4.set_alpha(alpha)
    display.blit(image4, (clouds_x*3, clouds_y*5))
    
    if not image4_return:
        image4_x += 1
        clouds_x += 0.03
        if image4_x > -1:
            image4_return = True
    else:
        image4_x -= 1
        clouds_x -= 0.03
        if image4_x < -50:
            image4_return = False


    #   text poem logic
    # if player_rect.x < 500:
    #     main_text = "Si tengo apetito es solo..."
        # letter = list(text).pop()
        # main_text += main_text + list(text).pop()
    # if player_rect.x > 500 and player_rect.x < 1000:
    #     main_text = "...de la tierra y de las piedras"
    # if player_rect.x > 1000 and player_rect.x < 1500:
    #     main_text = "Almuerzo siempre con aire..."
    # if player_rect.x > 1500 and player_rect.x < 2000:
    #     main_text = "...tierra, carbones y piedras"



    tile_rects = []
    oak_seeds = []
    #   display tiles and things and 
    for y in range(3):
        for x in range(4):
            target_x = x - 1 + int(round(scroll[0]/(CHUNK_SIZE*TILE_SIZE_SCALE)))
            target_y = y - 1 + int(round(scroll[1]/(CHUNK_SIZE*TILE_SIZE_SCALE)))
            target_chunk = str(target_x) + ':' + str(target_y)
            if target_chunk not in game_map:
                game_map[target_chunk] = generate_chunk(target_x, target_y)
            for tile in game_map[target_chunk]:
                if tile[1] in [1,2]:
                    display.blit(tile_index[tile[1]], (tile[0][0]*TILE_SIZE_SCALE-scroll[0], tile[0][1]*TILE_SIZE_SCALE-scroll[1]))
                    tile_rects.append(pygame.Rect(tile[0][0]*TILE_SIZE_SCALE, tile[0][1]*TILE_SIZE_SCALE, TILE_SIZE_SCALE, TILE_SIZE_SCALE))
                if tile[1] == 3:
                    oak_rect = pygame.Rect(tile[0][0]*TILE_SIZE_SCALE, tile[0][1]*TILE_SIZE_SCALE, tile_index[tile[1]].get_width()/3, tile_index[tile[1]].get_height())
                    oak_seeds.append(oak_rect)
                    #   dont draw oak seeds that have been eaten
                    # if not oak_rect == last_oak_rect:
                    if oak_rect not in eaten_oaks:
                        display.blit(tile_index[tile[1]], (tile[0][0]*TILE_SIZE_SCALE-scroll[0], tile[0][1]*TILE_SIZE_SCALE-scroll[1]+oak_seed_image.get_height()-5) )


    # print('OAKSEEDS')
    # print(oak_seeds)

    if moving_right or moving_left or moving_up:
        #   reset ticks count since inactive
        player_ticks_idle = 0

    player_movement = [0,0]
    if moving_right and not moving_down:
        # clouds_x += 0.03
        player_movement[0] += PLAYER_MOVEMENT_SPEED
    if moving_left and not moving_down:
        # clouds_x -= 0.03
        player_movement[0] -= PLAYER_MOVEMENT_SPEED
    if moving_up:
        clouds_y += 0.09
        if alpha > -125:
            alpha -= 1
        # print('moving up')
        # player_movement[1] += PLAYER_MOVEMENT_SPEED
    if moving_down:
        # print('moving down')
        if clouds_y > 0:
            alpha += 1
            clouds_y -= 0.09
        # player_movement[1] -= PLAYER_MOVEMENT_SPEED
        
    # print(player_y_momentum)

    player_movement[1] += player_y_momentum
    player_y_momentum += velocity

    #   player falling
    if player_is_jumping and player_y_momentum > 0:
        if alpha < 250:
            alpha += 1
        if clouds_y > 0:
            clouds_y -= 1
    #   don't fall way to fast
    if player_y_momentum > 10:
        player_y_momentum = 10

    #   player actions
    if player_movement[0] > 0: #    walk right
        player_action, player_frame = change_action(player_action, player_frame, 'walk')
        img3_x += 0.01
        player_flip = False
    if player_movement[0] < 0: #    walk left
        player_action, player_frame = change_action(player_action, player_frame, 'walk')
        player_flip = True
    if player_movement[0] == 0: #   idle
        player_action, player_frame = change_action(player_action, player_frame, 'idle')
    if moving_down and not moving_left: #   munch right
        player_action, player_frame = change_action(player_action, player_frame, 'munch')
    if moving_down and moving_left: #   munch left
        player_action, player_frame = change_action(player_action, player_frame, 'munch')
        player_flip = True


    player_rect, collisions = move(player_rect, player_movement, tile_rects)
    # player_rect2, collisions2 = move(player_rect, player_movement, oak_seeds)

    #   check colission with oak seeds
    oak_colission = player_rect.collideobjects(oak_seeds)
    if player_rect.collideobjects(oak_seeds):
        # print(oak_colission)
        display.blit(oak_seed_image, (0,0))
        if moving_down and oak_colission not in eaten_oaks:
            seed_amount += 1
            eaten_oaks.append(oak_colission)
    # else:
    #     print('not in oak')

    # print("player X "+str(player_rect.x))
    if collisions['bottom']:
        player_is_jumping = False
        player_y_momentum = 0
    if collisions['right']:
        print('COLLISSIONS RIGHT')
        print(collisions)

    #   change idle animation after 3 seconds standing
    if player_ticks_idle >= 90:
        # player_ticks_idle =
        player_action, player_frame = change_action(player_action, player_frame, 'sitting-idle')


    #   draw player sprite
    player_frame += 1
    if player_frame >= len(animation_database[player_action]):
        player_frame = 0
    player_img_id = animation_database[player_action][player_frame]
    player_img = animation_frames[player_img_id]

    display.blit(pygame.transform.flip(player_img, player_flip, False), (player_rect.x-scroll[0], player_rect.y-scroll[1]))


    #   event handler
    for event in pygame.event.get():
        if event.type == QUIT:
            run = False
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_RIGHT:
                moving_right = True
            if event.key == K_LEFT:
                moving_left = True
            if event.key == K_UP:
                moving_up = True
                player_is_jumping = True
                player_y_momentum = -5
            if event.key == K_DOWN:
                moving_down = True
                player_is_jumping = False
                player_y_momentum = 5
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                moving_right = False
            if event.key == K_LEFT:
                moving_left = False
            if event.key == K_UP:
                moving_up = False
            if event.key == K_DOWN:
                moving_down = False
            
    
    # screen.blit(pygame.transform.scale(display, WINDOW_SIZE), (0,0))
    screen.blit(display, (0,0))
    pygame.display.update()
    clock.tick(30)
    player_ticks_idle += 1
    # print(clock.get_fps())