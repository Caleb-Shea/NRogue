import pygame as pyg
import random
import math
import os

os.environ['SDL_VIDEO_CENTERED'] = '1'

FPS = 30


class Player(pyg.sprite.Sprite):
    def __init__(self, window, world, char):
        super().__init__()
        self.window = window
        self.world = world
        self.sheet = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'player', f'{char}', 'normal_sheet.png'))).convert_alpha()
        self.image_rect_dict = {'right': pyg.rect.Rect(0, 0, 50, 60),
                                'left':  pyg.rect.Rect(50, 0, 50, 60)}

        self.image = pyg.Surface((50, 60), flags=pyg.SRCALPHA)

        self.rect = self.image.get_rect()

        self.draw_rect = self.rect

        self.collide_rect = self.rect.inflate(-8, -20)
        self.collide_rect.bottom = self.rect.bottom + 2

        self.vel = pyg.Vector2((0, 0))
        self.speed = 15

        self.max_hp = 4
        self.hp = self.max_hp
        self.is_alive = True

        self.cur_weapon = Slingshot(window, world)

        self.is_invisible = False

        self.free_move = False

        self.score = 0

        self.i_frames_left = 0 # Invincibility frames

        self.score_sound = pyg.mixer.Sound(get_path(os.path.join('assets', 'audio', 'score_up.wav')))

        self.has_crystal = False

    def add_hud(self, hud):
        self.hud = hud

    def move_x(self, amount):
        self.rect.x += int(amount)

         # Edges of the screen
        if self.rect.right > self.world.rect.width:
            self.rect.right = self.world.rect.width
            self.vel.x = 0
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel.x = 0

        if not self.free_move: # Cheat code
            obstacles = self.world.walls.sprites() + self.world.statics.sprites()

            for wall in obstacles:
                if self.rect.colliderect(wall.collide_rect):
                    if self.vel.x > 0:
                        self.rect.right = wall.collide_rect.left
                        self.vel.x = 0
                    elif self.vel.x < 0:
                        self.rect.left = wall.collide_rect.right
                        self.vel.x = 0

    def move_y(self, amount):
        self.rect.y += int(amount)

         # Edges of the screen
        if self.rect.top < 0:
            self.rect.top = 0
            self.vel.y = 0
        if self.rect.bottom > self.world.rect.height:
            self.rect.bottom = self.world.rect.height
            self.vel.y = 0

        if not self.free_move:
            obstacles = self.world.walls.sprites() + self.world.statics.sprites()

            for wall in obstacles:
                if self.rect.colliderect(wall.collide_rect):
                    if self.vel.y < 0:
                        self.rect.top = wall.collide_rect.bottom
                        self.vel.y = 0
                    elif self.vel.y > 0:
                        self.rect.bottom = wall.collide_rect.top
                        self.vel.y = 0

    def apply_pickup(self, pickup):
        if pickup.type == 'hp':
            if self.hp < self.max_hp:
                self.heal(1)
                pickup.kill()
        elif pickup.type == 'cube':
            self.add_score(pickup.amount)
            pickup.kill()
            self.hud.update('score')

    def hurt(self, amount):
        if self.i_frames_left > 0:
            return
        else:
            self.hp -= amount

            if self.hp < 0:
                self.hp = 0
                self.is_alive = False

            self.i_frames_left = FPS // 2 # Half a second invincibility

        self.hud.update('hp', 'score')

    def heal(self, amount):
        self.hp += amount

        if self.hp > self.max_hp:
            self.hp = self.max_hp

        self.hud.update('hp')

    def fire(self):
        self.cur_weapon.fire()

    def add_score(self, amount):
        self.score += amount
        play_sound(self.score_sound)
        self.hud.update('score')

    def set_image(self, img):
        self.image.fill((0, 0, 0, 0))
        self.image.blit(self.sheet, (0, 0), self.image_rect_dict[img])
        # Uncomment when testing one image
        #self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'player', 'block', 'test.png'))).convert_alpha()

    def update(self):
        if self.i_frames_left > 0:
            self.i_frames_left -= 1

        self.collide_rect.center = self.rect.center

        self.move_x(self.vel.x)
        self.move_y(self.vel.y)

        self.vel.x *= .3
        if abs(self.vel.x) < .2: self.vel.x = 0
        self.vel.y *= .3
        if abs(self.vel.y) < .2: self.vel.y = 0

        self.cur_weapon.set_pos(self.draw_rect)

        for enemy in self.world.enemies:
            if self.collide_rect.colliderect(enemy.rect):
                self.hurt(enemy.damage)
        for bullet in self.world.bullets:
            if bullet.owner != 'player':
                if self.collide_rect.colliderect(bullet.rect):
                    self.hurt(1)
                    bullet.kill()
        for pickup in self.world.pickups:
            if self.collide_rect.colliderect(pickup.rect):
                self.apply_pickup(pickup)

        if pyg.mouse.get_pos()[0] > WIDTH//2:
            self.set_image('right')
        else:
            self.set_image('left')

        self.hud.update('pos')

    def render(self):
        self.window.blit(self.image, self.draw_rect)

        self.cur_weapon.render()


class Pickup(pyg.sprite.Sprite):
    def __init__(self, window, data):
        """A pickup on the ground.
        The data argument contains three items:
            'image' = a Surface containing the image to be displayed.
            'pos' = a coordinate pair for the topleft of the pickup.
            'type' = one of ['hp', 'cube']
        """
        super().__init__()
        self.window = window
        self.window_rect = self.window.get_rect()
        self.image = data['image'].convert_alpha()
        self.shadow = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'shadows', 'pickup.png'))).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = data['pos']
        self.draw_rect = self.rect

        self.vel = pyg.Vector2()

        self.type = data['type']
        if self.type in ['cube']:
            self.seek_player = True

        self.amount = 100

        self.on_ground = True

    def update(self, player):
        if self.type == 'hp':
            if player.hp == player.max_hp:
                self.seek_player = False
            else:
                self.seek_player = True

        # Distance but no sqrt so it's faster
        dist = ((self.rect.centerx - player.rect.centerx)**2 +
                (self.rect.centery - player.rect.centery)**2)
        if dist < 10000 and self.seek_player:
            dir = math.atan2((player.rect.center[1] - self.rect.center[1]),
                             (player.rect.center[0] - self.rect.center[0]))

            self.vel.x += math.cos(dir)
            self.vel.y += math.sin(dir)

            self.rect.x += int(self.vel.x) * 5
            self.rect.y += int(self.vel.y) * 5
        else:
            self.vel.x *= .5
            self.vel.y *= .5

    def render(self):
        if self.on_ground:
            if self.draw_rect.colliderect(self.window_rect):
                self.window.blit(self.shadow, self.draw_rect.move(0, 15))
                self.window.blit(self.image, self.draw_rect)
        else:
            if self.draw_rect.colliderect(self.window_rect):
                self.window.blit(self.image, self.draw_rect)


class Textbox():
    def __init__(self, window, text_lines, pos, placement, image=None, font='apache', size=32):
        self.window = window
        self.texts = []
        self.rects = []

        if font == 'apache':
            self.font = pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'apache.ttf')), size)
        elif font == 'coffee':
            self.font = pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'coffee.ttf')), size)

        for line in text_lines:
            text = self.font.render(line, True, (0, 0, 0))
            rect = text.get_rect()
            rect.center = pos

            self.texts.append(text)
            self.rects.append(rect)

            # Move the next line down enough to be read
            pos = (pos[0], pos[1] + size + size//10)

        if placement == 'above':
            for rect in self.rects:
                rect.y -= len(text_lines) * int(size * 1.1) + 15

        self.bg_rect = self.rects[0].unionall(self.rects[1:]).inflate(15, 15)
        self.bg = pyg.Surface((self.bg_rect.size)).convert_alpha()
        self.bg.fill((175, 175, 175, 150))
        pyg.draw.rect(self.bg, (10, 10, 10), ((0, 0), self.bg_rect.size), width=8)

    def render(self):
        self.window.blit(self.bg, self.bg_rect)

        for text, rect in zip(self.texts, self.rects):
            self.window.blit(text, rect)


class Meter():
    def __init__(self, window, max, pos, size, color):
        self.window = window
        self.window_rect = self.window.get_rect()
        self.max = max
        self.cur = self.max

        self.image = pyg.Surface(size)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos

        self.color = color

        self.update_bar()

    def update_bar(self):
        self.image.fill((0, 0, 0))

        # Make a slightly smaller rect that represents the value
        border_width = int(self.rect.height*.15)

        height = self.rect.height - 2*border_width
        width = int((self.rect.width - 2*border_width) * (self.cur / self.max))

        bar_rect = pyg.rect.Rect(border_width, border_width, width, height)

        pyg.draw.rect(self.image, self.color, bar_rect)

    def set_value(self, value):
        if self.cur == value:
            return
        self.cur = value
        self.cur = min(self.cur, self.max)
        self.cur = max(self.cur, 0)

        self.update_bar()


    def add_value(self, amount):
        self.cur += amount
        self.cur = min(self.cur, self.max)
        self.cur = max(self.cur, 0)

        self.update_bar()

    def get_value(self):
        return self.cur

    def render(self):
        if self.rect.colliderect(self.window_rect):
            self.window.blit(self.image, self.rect)


class Slingshot():
    def __init__(self, window, world):
        self.window = window
        self.world = world

        self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'weapons', 'slingshot.png'))).convert_alpha()
        self.rect = self.image.get_rect()

        self.image_source = self.image

        self.b_image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'weapons', 'pebble.png'))).convert_alpha()
        self.b_rect = self.b_image.get_rect()

        self.bullet_data = {'image': self.b_image,
                            'rect': self.b_rect,
                            'owner': 'player',
                            'source': (self.rect.centerx, self.rect.y),
                            'target': camera.get_world_pos(pyg.mouse.get_pos()),
                            'speed': 40,
                            'invulnerable': False,
                            'bouncy': False}

    def fire(self):
        self.bullet_data['source'] = (self.rect.centerx, self.rect.y)
        self.bullet_data['target'] = camera.get_world_pos(pyg.mouse.get_pos())

        bullet = Bullet(self.window, self.world, self.bullet_data)
        self.world.bullets.add(bullet)

    def set_pos(self, p_rect):
        # Rotate towards the mouse pointer
        m_pos = pyg.mouse.get_pos()

        dir = math.atan2((m_pos[1] - p_rect.centery), (m_pos[0] - p_rect.centerx))
        x = math.cos(dir)
        y = math.sin(dir)

        self.rect.center = p_rect.center
        self.rect.move_ip((x * 30, y * 30))

        # Flip the image if necassary
        if self.rect.centerx < p_rect.centerx:
            self.image = pyg.transform.flip(self.image_source, True, False)
            self.image = pyg.transform.rotate(self.image, 180)
        else:
            self.image = self.image_source

        self.image = pyg.transform.rotate(self.image, math.degrees(-dir))


    def render(self):
        self.window.blit(self.image, self.rect)


class LaserGun():
    def __init__(self, window, world):
        self.window = window
        self.world = world

        self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'weapons', 'lasergun.png'))).convert_alpha()
        self.rect = self.image.get_rect()

        self.image_source = self.image

        self.color = (200, 0, 0)

        # The laser kills by summoning a bullet at self.target
        self.bullet_data = {'image': pyg.Surface((1, 1)),
                            'rect': pyg.rect.Rect(0, 0, 20, 20),
                            'owner': 'player',
                            'source': self.rect.center,
                            'target': (0, 0),
                            'speed': 0,
                            'invulnerable': False,
                            'bouncy': False}

    def fire(self):
        def get_dist(x):
            x1, y1 = x.collide_rect.center
            x2, y2 = self.rect.center

            return (x1 - x2)**2 + (y1 - y2)**2

        # Loop through all enemies and track if they overlap with the line.
        hits = []
        for enemy in self.world.enemies.sprites():
            if enemy.draw_rect.clipline(self.rect.center, self.target):
                hits.append(enemy)

        # Then target the one that is closest to the gun.
        if len(hits) > 0:
            hits_sorted = sorted(hits, key=get_dist)
            closest = hits_sorted[0]

            closest.die()

    def set_pos(self, p_rect):
        # Rotate towards the mouse pointer
        m_pos = pyg.mouse.get_pos()

        dir = math.atan2((m_pos[1] - p_rect.centery), (m_pos[0] - p_rect.centerx))
        x = math.cos(dir)
        y = math.sin(dir)

        self.rect.center = p_rect.center
        self.rect.move_ip((x * 30, y * 30))

        # Flip the image if necassary
        if self.rect.centerx < p_rect.centerx:
            self.image = pyg.transform.flip(self.image_source, True, False)
            self.image = pyg.transform.rotate(self.image, 180)
        else:
            self.image = self.image_source

        self.image = pyg.transform.rotate(self.image, math.degrees(-dir))

        # Generate a line to be drawn as the sight
        self.target = [x * WIDTH + self.rect.centerx, y * WIDTH + self.rect.centery]

        # Stop the line once it hits a wall or an enemy
        sprites = (self.world.walls.sprites() +
                  self.world.enemies.sprites() +
                  self.world.statics.sprites())
        for sprite in sprites:
            if sprite.draw_rect.clipline(self.rect.center, self.target):
                self.target = sprite.draw_rect.clipline(self.rect.center, self.target)[0]

    def render(self):
        pyg.draw.line(self.window, self.color, self.rect.center, self.target, 3)
        self.window.blit(self.image, self.rect)


class Bullet(pyg.sprite.Sprite):
    """
         XXXXXXXXXXXX
         XXXX      XXXX
         XXXX      XXXX
         XXXXXXXXXXX
         XXXX      XXXX
         XXXX      XXXX
         XXXXXXXXXXXX

    Minimap label
    """
    def __init__(self, window, world, data):
        super().__init__()
        self.window = window
        self.world = world

        self.data = data

        self.owner = self.data['owner']

        self.image = self.data['image']
        self.rect = self.data['rect'].copy()
        self.rect.center = camera.get_world_pos(self.data['source'])
        self.draw_rect = self.rect

        self.speed = self.data['speed']

        self.invulnerable = self.data['invulnerable']
        self.bouncy = self.data['bouncy']
        if self.bouncy:
            self.num_bounce = self.data['num_bounce']

        self.kill_next_frame = False

        self.vel = pyg.Vector2()
        target = self.data['target']
        dir = math.atan2((target[1] - self.rect.centery), (target[0] - self.rect.centerx))
        # A number in the range (-1, 1), multiplied by speed to move each tick
        self.vel.x = math.cos(dir)
        self.vel.y = math.sin(dir)

    def update(self):
        if self.kill_next_frame == True:
            self.kill()

        self.rect.x += int(self.vel.x * self.speed)
        self.rect.y += int(self.vel.y * self.speed)

        for wall in self.world.walls:
             # Don't use wall.collide_rect so bullet collisions seem fair
            if self.rect.colliderect(wall.rect):
                if self.bouncy and self.num_bounce > 0:
                        if self.vel.x > 0:
                            self.rect.right = wall.rect.left
                            self.vel.x *= -1
                        elif self.vel.x < 0:
                            self.rect.left = wall.rect.right
                            self.vel.x *= -1

                        if self.vel.y < 0:
                            self.rect.top = wall.rect.bottom
                            self.vel.y *= -1
                        elif self.vel.y > 0:
                            self.rect.bottom = wall.rect.top
                            self.vel.y *= -1
                else:
                    self.kill_next_frame = True

    def render(self):
        if self.draw_rect.colliderect(self.world.rect):
            self.window.blit(self.image, self.draw_rect)


class Enemy(pyg.sprite.Sprite):
    """
         XXXXXXXXXXXXX
         XXXX
         XXXX
         XXXXXXXXXXXXX
         XXXX
         XXXX
         XXXXXXXXXXXXX

    Minimap label
    """
    def __init__(self, window, world):
        super().__init__()
        self.window = window
        self.window_rect = self.window.get_rect()
        self.world = world

        self.hp = 1
        self.damage = 1

        self.vel = pyg.Vector2((0, 0))

    def move_x(self, amount):
        self.rect.x += int(amount)

        obstacles = self.world.walls.sprites() + self.world.statics.sprites()

        for wall in obstacles:
            if self.rect.colliderect(wall.collide_rect):
                if self.vel.x > 0:
                    self.rect.right = wall.collide_rect.left
                    self.vel.x = 0
                elif self.vel.x < 0:
                    self.rect.left = wall.collide_rect.right
                    self.vel.x = 0

    def move_y(self, amount):
        self.rect.y += int(amount)

        obstacles = self.world.walls.sprites() + self.world.statics.sprites()

        for wall in obstacles:
            if self.rect.colliderect(wall.collide_rect):
                if self.vel.y < 0:
                    self.rect.top = wall.collide_rect.bottom
                    self.vel.y = 0
                elif self.vel.y > 0:
                    self.rect.bottom = wall.collide_rect.top
                    self.vel.y = 0

    def die(self):
        self.kill()
        # player.add_score(self.score)

    def update(self):
        self.move_x(self.vel.x)
        self.move_y(self.vel.y)

        self.collide_rect.center = self.rect.center

        for bullet in self.world.bullets:
            if bullet.owner == 'player':
                if self.collide_rect.colliderect(bullet.rect):
                    self.hp -= 1
                    if not bullet.invulnerable:
                        bullet.kill()

        if self.hp <= 0:
            self.die()

    def render(self):
        if self.draw_rect.colliderect(self.window_rect):
            self.window.blit(self.image, self.draw_rect)

class Charger(Enemy):
    def __init__(self, window, world, pos):
        super().__init__(window, world)
        self.image = pyg.Surface((40, 40))
        # self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'charger.png'))).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.draw_rect = self.rect
        self.collide_rect = self.rect.inflate(15, 15)

        self.speed = 2
        self.max_speed = 4
        self.dir = 0
        self.score = 20

        self.seek_range = 500

        self.damage = 2

        self.hp = 2
        self.hp_meter = Meter(self.window, 2, (0, 0), (50, 10), (200, 50, 50))
        self.show_hp_meter = False

    def update(self, player):
        p_pos = player.rect.center
        # Distance but no sqrt so it's faster
        dist = ((self.rect.centerx - player.rect.centerx)**2 +
                (self.rect.centery - player.rect.centery)**2)
        if dist < self.seek_range**2 and not player.is_invisible: # Seek out player
            self.dir = math.atan2((p_pos[1] - self.rect.center[1]),
                                  (p_pos[0] - self.rect.center[0]))
            self.vel.x += math.cos(self.dir) * self.speed
            self.vel.y += math.sin(self.dir) * self.speed

            if self.speed < self.max_speed:
                self.speed += .07
        elif dist < 2 * self.seek_range**2: # Randomly move around
            self.dir = random.triangular(-math.pi, math.pi, self.dir)
            self.vel.x += math.cos(self.dir) * self.speed
            self.vel.y += math.sin(self.dir) * self.speed

            self.speed = .7
        else: # Do nothing
            self.vel.x *= .5
            self.vel.y *= .5
            self.speed = 2

        self.hp_meter.rect.midbottom = self.draw_rect.midtop
        self.hp_meter.rect.y -= 10

        self.hp_meter.set_value(self.hp)
        if (math.dist(pyg.mouse.get_pos(), self.draw_rect.center) < 250 or
            math.dist(player.draw_rect.center, self.draw_rect.center) < self.seek_range):
            self.show_hp_meter = True
        else:
            self.show_hp_meter = False

        super().update()

    def render(self):
        super().render()
        if self.show_hp_meter:
            self.hp_meter.render()


class Dummy(Enemy):
    def __init__(self, window, world, pos):
        super().__init__(window, world)
        self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'Dummy.png'))).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = pos

        self.draw_rect = self.rect

        self.collide_rect = self.rect.inflate(5, 5)

        self.vel.x = random.randint(5, 15)
        self.vel.y = random.randint(5, 10)

        self.score = 10

    def update(self, player):
        for wall in self.world.walls:
            if self.rect.colliderect(wall.rect):
                if self.vel.x > 0:
                    self.rect.right = wall.rect.left
                    self.vel.x *= -1
                elif self.vel.x < 0:
                    self.rect.left = wall.rect.right
                    self.vel.x *= -1

        for wall in self.world.walls:
            if self.rect.colliderect(wall.rect):
                if self.vel.y < 0:
                    self.rect.top = wall.rect.bottom
                    self.vel.y *= -1
                elif self.vel.y > 0:
                    self.rect.bottom = wall.rect.top
                    self.vel.y *= -1

        super().update()


class HUD():
    """
        XXX        XXX
        XXX        XXX
        XXXXXXXXXXXXXX
        XXXXXXXXXXXXXX
        XXX        XXX
        XXX        XXX
        XXX        XXX

    Minimap label
    """
    def __init__(self, window, player, level):
        self.window = window
        self.player = player
        self.apache32 = pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'apache.ttf')), 32)
        self.coffee24 = pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'coffee.ttf')), 24)
        self.hp_sheet = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'hud', 'hp2.png'))).convert_alpha()

        self.hp_rect_full = pyg.Rect(0, 0, 52, 47)
        self.hp_rect_empty = pyg.Rect(53, 0, 52, 47)
        self.hp_rect = pyg.rect.Rect(0, 0, 380, 47)
        self.hp_image = pyg.Surface(self.hp_rect.size, flags=pyg.SRCALPHA)
        self.hp_image.fill((0, 0, 0, 0))
        self.hp_rect.topleft = (10, 10)

        self.score_image = self.apache32.render(str(self.player.score), True, (0, 0, 0))
        self.score_rect = self.score_image.get_rect()
        self.score_rect.bottomright = (WIDTH - 10, HEIGHT - 10)

        self.pos_image = self.apache32.render(str(self.player.rect.center), True, (0, 0, 0))
        self.pos_rect = self.pos_image.get_rect()
        self.pos_rect.topright = (WIDTH - 10, 10)

        self.level_image = self.coffee24.render(f'Current Level: {level}', True, (0, 0, 0))
        self.level_rect = self.level_image.get_rect()
        self.level_rect.topright = self.pos_rect.move(0, 10).bottomright

        self.fps_image = self.coffee24.render('FPS: 0', True, (0, 0, 0))
        self.fps_rect = self.fps_image.get_rect()
        self.fps_rect.topright = self.level_rect.move(0, 10).bottomright

        self.update('hp')

    def update(self, *args):
        if 'hp' in args:
            self.hp_image.fill((0, 0, 0, 0))
            for i in range(self.player.max_hp):
                if i < self.player.hp:
                    self.hp_image.blit(self.hp_sheet, (58*i, 0), self.hp_rect_full)
                else:
                    self.hp_image.blit(self.hp_sheet, (58*i, 0), self.hp_rect_empty)

        if 'score' in args:
            self.score_image = self.apache32.render(str(self.player.score), True, (0, 0, 0))
            self.score_rect = self.score_image.get_rect()
            self.score_rect.bottomright = (WIDTH - 10, HEIGHT - 10)

        if 'pos' in args:
            self.pos_image = self.apache32.render(str(self.player.rect.topleft), True, (0, 0, 0))
            self.pos_rect = self.pos_image.get_rect()
            self.pos_rect.topright = (WIDTH - 10, 10)

        if 'level' in args:
            self.level_image = self.coffee24.render(f'Current Level: {args[-1]}', True, (0, 0, 0))
            self.level_rect = self.level_image.get_rect()
            self.level_rect.topright = self.pos_rect.move(0, 10).bottomright

        if 'fps' in args:
            self.fps_image = self.coffee24.render(f'FPS: {args[-1]}', True, (0, 0, 0))
            self.fps_rect = self.fps_image.get_rect()
            self.fps_rect.topright = self.level_rect.move(0, 10).bottomright

    def render(self):
        self.window.blit(self.hp_image, self.hp_rect)
        self.window.blit(self.score_image, self.score_rect)
        self.window.blit(self.pos_image, self.pos_rect)
        self.window.blit(self.level_image, self.level_rect)
        self.window.blit(self.fps_image, self.fps_rect)

class Camera():
    """
            XXXXXXXXX
         XXXX       XXXX
         XXXX
         XXXX
         XXXX
         XXXX       XXXX
            XXXXXXXXX

    Minimap label
    """
    def __init__(self):
        self.rect = pyg.rect.Rect(0, 0, WIDTH, HEIGHT)

    def get_world_pos(self, pos):
        return (pos[0] - self.rect.left, pos[1] - self.rect.top)

    def apply_lens(self, player, world, world_decor):
        player.draw_rect = player.rect.move(self.rect.topleft)
        world_decor.bg_draw_rect = world_decor.bg_rect.move(self.rect.topleft)

        everything = (world.walls.sprites() +
                      world.statics.sprites() +
                      world.pickups.sprites() +
                      world.enemies.sprites() +
                      world.bullets.sprites())

        for sprite in everything:
            sprite.draw_rect = sprite.rect.move(self.rect.topleft)

    def follow(self, sprite):
        pos = sprite.rect.center

         # Subtract half of the screen to center the sprite
        top = pos[0] - WIDTH//2
        left = pos[1] - HEIGHT//2
        width = self.rect.width
        height = self.rect.height

        self.rect = pyg.rect.Rect(-top, -left, width, height)


class World():
    """
        XXX         XXX
        XXX         XXX
        XXX   XXX   XXX
        XXX  XXXXX  XXX
        XXX XXX XXX XXX
        XXXXX     XXXXX
        XXX         XXX

    Minimap label
    """
    def __init__(self, window):
        self.window = window
        self.rooms = []
        self.walls = pyg.sprite.Group()
        self.statics = pyg.sprite.Group()
        self.pickups = pyg.sprite.Group()
        self.enemies = pyg.sprite.Group()
        self.bullets = pyg.sprite.Group()

        self.saved_levels = {}

    def save_level(self, cur_level):
        self.saved_levels[cur_level] = {'rooms': self.rooms[:],
                                             'walls': self.walls.copy(),
                                             'statics': self.statics.copy(),
                                             'pickups': self.pickups.copy(),
                                             'enemies': self.enemies.copy(),
                                             'bullets': self.bullets.copy(),
                                             'up_ladder': self.up_ladder,
                                             'down_ladder': self.down_ladder}

    def gen_saved_level(self, level, dir):
        self.rooms = []
        self.walls.empty()
        self.statics.empty()
        self.pickups.empty()
        self.enemies.empty()
        self.bullets.empty()

        self.rooms = self.saved_levels[level]['rooms']
        self.walls = self.saved_levels[level]['walls']
        self.statics = self.saved_levels[level]['statics']
        self.pickups = self.saved_levels[level]['pickups']
        self.enemies = self.saved_levels[level]['enemies']

        self.up_ladder = self.saved_levels[level]['up_ladder']
        self.down_ladder = self.saved_levels[level]['down_ladder']

        if dir == 'up':
            self.spawn = self.down_ladder.rect.center
        elif dir == 'down':
            self.spawn = self.up_ladder.rect.center
        else:
            print('eooror')
            0/0

    def generate(self, level, theme, dir, preset=None):
        """Create a given level procedurally. Until level 10, use the grid
        generation type, where a grid of rooms is created, then a maze is
        constructed that reaches every room.
        """

        if level in self.saved_levels.keys():
            self.gen_saved_level(level, dir)
            return

        self.rooms = []
        self.walls.empty()
        self.statics.empty()
        self.pickups.empty()
        self.enemies.empty()
        self.bullets.empty()

        if preset:
            self.gen_with_preset(preset)
            return

        if level < 10:
            gen_type = 'grid'
        else:
            gen_type = 'grid'

        if gen_type == 'grid':
            # Create all the rooms, then make the maze, then set the special
            # rooms, e.g. start, exit, treasure
            self.image = pyg.Surface((3750, 3000))
            self.rect = self.image.get_rect()

            for y in range(0, self.rect.bottom, 600):
                for x in range(0, self.rect.right, 750):
                    room = self.create_room('grid', theme, 'regular', (x, y))
                    self.rooms.append(room)

            # Use recursive backtracking to create a path that hits every
            # room.
            """
            From wikipedia:
            Choose the initial cell, mark it as visited and push it to the stack
            While the stack is not empty
                Pop a cell from the stack and make it a current cell
                If the current cell has any neighbours which have not been visited
                    Push the current cell to the stack
                    Choose one of the unvisited neighbours
                    Remove the wall between the current cell and the chosen cell
                    Mark the chosen cell as visited and push it to the stack"""

            dim_x = 5
            dim_y = 5
            stack = []
            visited = []

            cur = random.randint(0, 24)
            stack.append(cur)
            visited.append(cur)

            while len(stack) > 0:
                cur = stack.pop()
                if len(self.get_adj_cells(dim_x, dim_y, visited, cur)) > 0:
                    stack.append(cur)
                    next = random.choice(self.get_adj_cells(dim_x, dim_y, visited, cur))

                    # Remove wall segments from cur and next
                    if next == (cur - dim_x): # Up
                        start = random.randint(1, 4)
                        wall_seg = [i for i in range(start, random.randint(start + 1, 5))]
                        self.rooms[next].remove_wall('bottom', wall_seg)
                        self.rooms[cur].remove_wall('top', wall_seg)

                    if next == (cur + dim_x): # Down
                        start = random.randint(1, 4)
                        wall_seg = [i for i in range(start, random.randint(start + 1, 5))]
                        self.rooms[next].remove_wall('top', wall_seg)
                        self.rooms[cur].remove_wall('bottom', wall_seg)

                    if next == (cur + 1): # Right
                        start = random.randint(1, 3)
                        wall_seg = [i for i in range(start, random.randint(start + 1, 4))]
                        self.rooms[next].remove_wall('left', wall_seg)
                        self.rooms[cur].remove_wall('right', wall_seg)

                    if next == (cur - 1): # Left
                        start = random.randint(1, 3)
                        wall_seg = [i for i in range(start, random.randint(start + 1, 4))]
                        self.rooms[next].remove_wall('right', wall_seg)
                        self.rooms[cur].remove_wall('left', wall_seg)

                    cur = next
                    stack.append(next)
                    visited.append(next)

            # Set the start/ exit points to be the first/ last rooms visited
            start = visited[0]
            exit = visited[-1]

            random.choice(self.rooms[1:-2]).add_features('treasure')
            random.choice(self.rooms[1:-2]).set_features('danger')
            self.rooms[start].set_features('start')
            self.rooms[exit].set_features('exit')

            self.down_ladder = self.rooms[exit].statics[0]
            self.up_ladder = self.rooms[start].statics[0]

            self.walls.add([room.walls for room in self.rooms])
            self.statics.add([room.statics for room in self.rooms])
            self.pickups.add([room.pickups for room in self.rooms])
            self.enemies.add([room.enemies for room in self.rooms])

            self.spawn = self.up_ladder.rect.center

    def get_adj_cells(self, dim_x, dim_y, visited, cur):
        """Get the adjacent cells, and if on the edge of the grid,
        don't go there."""
        adj_cells = []

        # Up
        if cur - dim_x >= 0 and cur - dim_x not in visited:
            adj_cells.append(cur - dim_x)

        # Down
        if cur + dim_x <= 24 and cur + dim_x not in visited:
            adj_cells.append(cur + dim_x)

        # Right
        if cur % dim_x != 4 and cur + 1 <= 24 and cur + 1 not in visited:
            adj_cells.append(cur + 1)

        # Left
        if cur % dim_x != 0 and cur - 1 >= 0 and cur - 1 not in visited:
            adj_cells.append(cur - 1)

        return adj_cells

    def create_room(self, location, theme, type, *args):
        if location == 'corner':
            corner = args[0]

            size_x = random.randrange(450, 751, 150)
            size_y = random.randrange(450, 751, 150)
            room_rect = pyg.rect.Rect(0, 0, size_x, size_y)

            if corner == 0:
                room_rect.topleft = (0, 0)
            elif corner == 1:
                room_rect.topright = (self.rect.width, 0)
            elif corner == 2:
                room_rect.bottomleft = (0, self.rect.height)
            elif corner == 3:
                room_rect.bottomright = (self.rect.width, self.rect.height)

        elif location == 'grid':
            size_x = 750
            size_y = 600
            room_rect = pyg.rect.Rect(args[0][0], args[0][1], size_x, size_y)

        room = Room(self.window, self, room_rect, type, theme)

        return room


class WorldDecoration():
    def __init__(self, window, world):
        """A class similar to World() in that it is a organization class.
        However, this class only contains things not essential to gameplay.
        E.g. the background and ambient decoration."""
        self.window = window
        self.world = world

        self.bg_set_1 = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'background', 'bg_set_1.png')))

    def generate(self, cur_level, theme):
        if theme == 'castle':
            bg_color = (41, 39, 42)
        elif theme == 'test':
            bg_color = (60, 70, 70)

        self.bg_rect = self.world.rect
        self.bg_rect.topleft = self.world.rect.topleft
        self.bg_draw_rect = self.bg_rect
        self.bg = pyg.Surface((self.bg_rect.size)).convert()
        self.bg.fill(bg_color)

        # Create a static background generated from a spritesheet
        for y in range(0, self.bg_rect.height, 50):
            for x in range(0, self.bg_rect.width, 50):
                rect = pyg.rect.Rect(0, 0, 50, 50)
                rect.x = 50 * random.randint(0, 3)
                self.bg.blit(self.bg_set_1, (x, y), rect)

    def render_bg(self):
        self.window.fill((255, 255, 255))
        self.window.blit(self.bg, self.bg_draw_rect)

class Room():
    """
         XXXXXXXXXXXX
         XXXX      XXXX
         XXXX      XXXX
         XXXXXXXXXXX
         XXXX      XXXX
         XXXX      XXXX
         XXXX      XXXX

    Minimap label
    """
    def __init__(self, window, world, rect, type, theme):
        self.window = window
        self.world = world
        self.rect = rect
        self.walls = []
        self.statics = []
        self.pickups = []
        self.enemies = []

        if type in ['regular', 'start', 'exit', 'treasure', 'danger']:
            keep = [True, True, True, True]

        self.add_features(type)

         # Create the corners of the room
        corner_coords = [(0, 0),
                         (self.rect.width - 75, 0),
                         (0, self.rect.height - 75),
                         (self.rect.width - 75, self.rect.height - 75)]
        for coord in corner_coords:
            pos = (coord[0] + self.rect.x, coord[1] + self.rect.y)
            wall = Wall(self.window, pos, theme, 'corner')
            self.walls.append(wall)

        if type == 'just_corners':
            return

        # Top
        for x in range(75, self.rect.width - 75, 150):
            pos = (x + self.rect.x, self.rect.y)
            wall = Wall(self.window, pos, theme, 'rl_bottom')
            self.walls.append(wall)

        # Right
        for y in range(75, self.rect.height - 75, 150):
            pos = (self.rect.x + self.rect.width - 75, y + self.rect.y)
            wall = Wall(self.window, pos, theme, 'ud')
            self.walls.append(wall)

        # Bottom
        for x in range(75, self.rect.width - 75, 150):
            pos = (x + self.rect.x, self.rect.y + self.rect.height - 75)
            wall = Wall(self.window, pos, theme, 'rl_top')
            self.walls.append(wall)

        # Left
        for y in range(75, rect.height - 75, 150):
            pos = (rect.x, y + rect.y)
            wall = Wall(self.window, pos, theme, 'ud')
            self.walls.append(wall)

    def remove_wall(self, side, pos):
        side_walls = []
        if side == 'top':
            for wall in self.walls:
                if wall.rect.top == self.rect.top:
                    side_walls.append(wall)
        if side == 'bottom':
            for wall in self.walls:
                if wall.rect.bottom == self.rect.bottom:
                    side_walls.append(wall)
        if side == 'left':
            for wall in self.walls:
                if wall.rect.left == self.rect.left:
                    side_walls.append(wall)
        if side == 'right':
            for wall in self.walls:
                if wall.rect.right == self.rect.right:
                    side_walls.append(wall)

        if side in ['top', 'bottom']:
            side_walls.sort(key=lambda wall: wall.rect.x)
        else:
            side_walls.sort(key=lambda wall: wall.rect.y)

        for i in pos:
            self.walls.remove(side_walls[i])

    def set_features(self, type):
        self.statics = []
        self.pickups = []
        self.enemies = []

        self.add_features(type)

    def add_features(self, type):
        """Generate any special decorations etc."""
        if type == 'start':
            self.statics.append(Ladder(self.window, self.rect.center, 'up'))

        elif type == 'exit':
            self.statics.append(Ladder(self.window, self.rect.center, 'down'))

        elif type == 'treasure':
             # Create a bunch of cubes centered around a point in the room
            center = (random.randint(self.rect.x + 200, self.rect.right - 200),
                      random.randint(self.rect.y + 200, self.rect.bottom - 200))
            for i in range(random.randint(8, 12)):
                image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'pickups', 'cube.png')))
                pos = (center[0] + random.randint(-75, 75), center[1] + random.randint(-75, 75))
                pickup = Pickup(self.window, {'image': image, 'pos': pos, 'type': 'cube'})
                self.pickups.append(pickup)

        elif type == 'danger':
            self.statics.append(Fountain(self.window, self.rect.center))

            pos = (random.randint(self.rect.x + 200, self.rect.right - 200),
                   random.randint(self.rect.y + 200, self.rect.bottom - 200))
            self.enemies.append(Charger(self.window, self.world, pos))

        elif type == 'regular':
            # The regular room has a 50% chance to have pickups
            # If the room has pickups, also spawn dummies
            if random.random() < .5:
                num_p = random.randint(2, 5)
                num_e = random.randint(1, 2)
            else:
                num_p = 0
                num_e = 0

            for i in range(num_p):
                p_type = random.choices(['hp', 'cube'], weights=[1, 3], k=1)[0]
                image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'pickups', f'{p_type}.png')))
                pos = (random.randint(self.rect.x + 100, self.rect.right - 100),
                       random.randint(self.rect.y + 100, self.rect.bottom - 100))
                pickup = Pickup(self.window, {'image': image, 'pos': pos, 'type': f'{p_type}'})
                self.pickups.append(pickup)

            for i in range(num_e):
                pos = (random.randint(self.rect.x + 100, self.rect.right - 100),
                       random.randint(self.rect.y + 100, self.rect.bottom - 100))
                dummy = Dummy(self.window, self.world, pos)
                self.enemies.append(dummy)

    def move(self, pos):
        sprite_list = self.walls + self.pickups + self.statics

        for sprite in sprite_list:
            sprite.rect.x = pos[0] + (sprite.rect.x - self.rect.x)
            sprite.rect.y = pos[1] + (sprite.rect.y - self.rect.y)

        self.rect.topleft = pos

class StaticObject(pyg.sprite.Sprite):
    def __init__(self, window, pos, is_centered):
        super().__init__()
        self.window = window
        self.window_rect = window.get_rect()
        self.rect = self.image.get_rect()
        if is_centered:
            self.rect.center = pos
        else:
            self.rect.topleft = pos
        self.draw_rect = self.rect

    def render(self):
        if self.draw_rect.colliderect(self.window_rect):
            self.window.blit(self.image, self.draw_rect)


class Wall(StaticObject):
    def __init__(self, window, pos, type, dir):
        self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', f'{type}_{dir}.png')))
        super().__init__(window, pos, False)
        self.collide_rect = self.rect.inflate(-20, -30)
        self.collide_rect.bottom -= 5


class Fountain(StaticObject):
    def __init__(self, window, pos):
        self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'fountain.png')))
        super().__init__(window, pos, True)
        self.collide_rect = self.rect.inflate(-20, -6)


class Ladder(StaticObject):
    def __init__(self, window, pos, dir):
        self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'ladder', f'{dir}.png')))
        super().__init__(window, pos, True)
        # Ladders do not use the collision rect, but a collide_rect
        # attribute is required, so set it to zeros
        self.collide_rect = pyg.rect.Rect(0, 0, 0, 0)


class RoomCover(StaticObject):
    def __init__(self, window, pos):
        self.image = pyg.Surface(600, 750)
        self.image.fill(0, 0, 0)
        super().__init__(window, pos, True)
        # Ladders do not use the collision rect, but a collide_rect
        # attribute is required, so set it to zeros
        self.collide_rect = pyg.rect.Rect(0, 0, 0, 0)


def terminate():
    pyg.quit()
    raise SystemExit()

def get_path(path):
    """Returns the full file path of a file."""
    dirname = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dirname, path)

def play_sound(sound):
    se_channel = pyg.mixer.find_channel()

    se_channel.play(sound)

def toggle_cheat_code(player, cheat_codes, *codes):
    if 'speed' in codes:
        if not cheat_codes['speed']:
            player.speed *= 2
            cheat_codes['speed'] = True
        else:
            player.speed /= 2
            cheat_codes['speed'] = False

    if 'free_move' in codes:
        if not cheat_codes['free_move']:
            player.free_move = True
            cheat_codes['free_move'] = True
        else:
            player.free_move = False
            cheat_codes['free_move'] = False

    if 'invisibility' in codes:
        if not cheat_codes['invisibility']:
            player.is_invisible = True
            cheat_codes['invisibility'] = True
        else:
            player.is_invisible = False
            cheat_codes['invisibility'] = False

def new_dummy(world, type):
    pos = (random.randint(0, world.rect.width), random.randint(0, world.rect.height))
    if type == 'bounce':
        dummy = Dummy(window, world, pos)
    else:
        return
    world.enemies.add(dummy)

def new_pickup(window, world, pos=None):
    """Create a random pickup anywhere in the world. Guarantee that one is
    generated."""
    if not pos:
        valid = False
        while not valid:
            pos = (random.randint(50, world.rect.width - 50), random.randint(50, world.rect.height - 50))
            valid = True
            for sprite in (world.walls.sprites() + world.statics.sprites()):
                if sprite.rect.inflate(40, 40).collidepoint(pos):
                    valid = False

    type = random.choices(['hp', 'cube'], weights=[1, 2], k=1)[0]
    image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'pickups', f'{type}'))).convert_alpha()
    data = {'pos': pos, 'type': type, 'image': image}

    return Pickup(window, data)

def win():
    print('YAY GOOD JOB BUDDY')
    terminate()


    """
        XXX         XXX
        XXXXX     XXXXX
        XXX XXX XXX XXX
        XXX  XXXXX  XXX
        XXX   XXX   XXX
        XXX         XXX
        XXX         XXX

    Minimap label
    """

def main():
     # Custom mouse pointer
    pyg.mouse.set_visible(False)
    pointer = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'misc', 'mouse', 'target.png'))).convert_alpha()
    pointer_rect = pointer.get_rect()

     # Custom Events
    custom_event = pyg.USEREVENT + 1
    pyg.time.set_timer(custom_event, 50)

    cur_level = 1
    world = World(window)
    world.generate(cur_level, 'castle', 'nodir')

    world_decor = WorldDecoration(window, world)
    world_decor.generate(cur_level, 'castle')

    player = Player(window, world, 'block')
    player.rect.center = world.spawn

    hud = HUD(window, player, cur_level)
    player.add_hud(hud)

    textboxes = []

    cheat_codes = {'speed': False,
                   'free_move': False,
                   'invisibility': False}

    clock = pyg.time.Clock()

    paused = False
    pause_menu_grayout = pyg.Surface((WIDTH, HEIGHT)).convert_alpha()
    pause_menu_grayout.fill((0, 0, 0, 100))

    while True:
        if not paused:
            for event in pyg.event.get():
                if event.type == pyg.QUIT:
                    terminate()
                elif event.type == pyg.KEYDOWN:
                    if event.key == pyg.K_ESCAPE:
                        paused = True
                    elif event.key == pyg.K_BACKQUOTE:
                        terminate()
                    elif event.key == pyg.K_SPACE:
                        ...
                    elif event.key == pyg.K_f: # Interact button
                        if player.collide_rect.colliderect(world.down_ladder.rect):
                            world.save_level(cur_level)
                            cur_level += 1
                            world.generate(cur_level, 'castle', 'down')
                            player.rect.center = world.spawn
                            hud.update('level', cur_level)

                        elif player.collide_rect.colliderect(world.up_ladder.rect):
                            if cur_level == 1:
                                if player.has_crystal:
                                    win()
                            else:
                                world.save_level(cur_level)
                                cur_level -= 1
                                world.generate(cur_level, 'castle', 'up')
                                player.rect.center = world.spawn
                                hud.update('level', cur_level)

                    elif event.key == pyg.K_COMMA:
                        player.cur_weapon = Slingshot(window, world)
                    elif event.key == pyg.K_PERIOD:
                        player.cur_weapon = LaserGun(window, world)
                    elif event.key == pyg.K_KP9:
                        toggle_cheat_code(player, cheat_codes, 'speed')
                    elif event.key == pyg.K_KP8:
                        toggle_cheat_code(player, cheat_codes, 'invisibility')
                    elif event.key == pyg.K_KP7:
                        toggle_cheat_code(player, cheat_codes, 'speed', 'free_move')
                    elif event.key == pyg.K_KP1:
                        player.has_crystal = True
                    elif event.key == pyg.K_1:
                        new_dummy(world, 'bounce')
                    elif event.key == pyg.K_2:
                        new_dummy(world, 'charger')
                elif event.type == pyg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        player.fire()
                elif event.type == pyg.WINDOWEVENT_FOCUS_LOST:
                    paused = True

            event_keys = pyg.key.get_pressed()
             # Movement keys
            if event_keys[pyg.K_LEFT] or event_keys[pyg.K_a]:
                player.vel.x -= player.speed
            if event_keys[pyg.K_RIGHT] or event_keys[pyg.K_d]:
                player.vel.x += player.speed
            if event_keys[pyg.K_UP] or event_keys[pyg.K_w]:
                player.vel.y -= player.speed
            if event_keys[pyg.K_DOWN] or event_keys[pyg.K_s]:
                player.vel.y += player.speed

             # Create textboxes for ladder collisions
            if player.collide_rect.colliderect(world.down_ladder.rect):
                pos = (player.draw_rect.midtop)
                textbox = Textbox(window, ["Press 'F'"], pos, 'above')
                textboxes.append(textbox)
            if player.collide_rect.colliderect(world.up_ladder.rect):
                pos = (player.draw_rect.midtop)
                textbox = Textbox(window, ["Press 'F'"], pos, 'above')
                textboxes.append(textbox)

            camera.follow(player)
            camera.apply_lens(player, world, world_decor)

            world_decor.render_bg()

            for p in world.pickups:
                p.update(player)
                p.render()

            for b in world.bullets.sprites():
                b.update()
                b.render()

            for s in world.statics:
                s.render()

            for e in world.enemies:
                e.update(player)
            for e in world.enemies:
                e.render()

            player.update()
            player.render()

            for w in world.walls:
                w.render()

            hud.update('fps', round(clock.get_fps()))
            hud.render()

            for t in textboxes:
                t.render()
            textboxes = []

            pointer_rect.center = pyg.mouse.get_pos()
            window.blit(pointer, pointer_rect)

            pyg.display.flip()
            clock.tick(FPS)

        else: # If paused
            for event in pyg.event.get():
                if event.type == pyg.QUIT:
                    terminate()
                elif event.type == pyg.KEYDOWN:
                    if event.key == pyg.K_ESCAPE:
                        paused = False
                    elif event.key == pyg.K_BACKQUOTE:
                        terminate()

            window.fill((255, 255, 255))
            window.blit(world_decor.bg, world_decor.bg_draw_rect)

            window.blit(pause_menu_grayout, (0, 0))

            pointer_rect.center = pyg.mouse.get_pos()

            window.blit(pointer, pointer_rect)

            pyg.display.flip()

            clock.tick(FPS)


if __name__ == '__main__':
    pyg.mixer.pre_init(44100, -16, 2, 512)
    pyg.mixer.init()
    pyg.init()
    pyg.display.set_caption("NRogue")
    window = pyg.display.set_mode(flags=pyg.HWSURFACE | pyg.FULLSCREEN | pyg.DOUBLEBUF)
    WIDTH, HEIGHT = pyg.display.get_window_size()

    # Init camera outside of main() so we can access it anywhere
    camera = Camera()

    main()