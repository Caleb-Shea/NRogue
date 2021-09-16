import pygame as pyg
import random
import math
import os


os.environ['SDL_VIDEO_CENTERED'] = '1'

FPS = 30


class Player(pyg.sprite.Sprite):
    def __init__(self, window, world):
        super().__init__()
        self.window = window
        self.world = world
        self.sheet = player_assets['img_sheet']
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

        self.score_sound = player_assets['score_sound']

        self.has_crystal = False

    def add_hud(self, hud):
        """Helper function that gives internal access to the hud."""
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

    def collect_crystal(self):
        self.has_crystal = True

    def apply_pickup(self, pickup):
        """Execute actions specific to the type of pickup picked up."""
        if pickup.type == 'hp':
            if self.hp < self.max_hp:
                self.heal(1)
                pickup.kill()
        elif pickup.type == 'cube':
            self.add_score(pickup.amount)
            pickup.kill()
            self.hud.update('score')

    def hurt(self, amount):
        """The player has half a second of invincibility after each hit.
           If not invincibile, deal damage to the player equal to amount."""
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
        """The inverse to self.hurt(). Heal the player by a given amount."""
        self.hp += amount

        if self.hp > self.max_hp:
            self.hp = self.max_hp

        self.hud.update('hp')

    def fire(self):
        """Call the fire function on the equipped weapon."""
        self.cur_weapon.fire()

    def add_score(self, amount):
        """Update the score then update the hud."""
        self.score += amount
        play_sound(self.score_sound)
        self.hud.update('score')

    def set_image(self, img):
        """Change the image for the player."""
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
        """Render the player and the equipped weapon."""
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
        self.shadow = pickup_assets['shadow']
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

        self.image = slingshot_assets['slingshot']
        self.rect = self.image.get_rect()

        self.image_source = self.image

        self.b_image = slingshot_assets['pebble']
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

        self.image = lasergun_assets['lasergun']
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


class Crystal(Enemy):
    """The crystal is the goal object of the game, it remains stationary, and
       does not hurt the player, but it has health, and responds to the
       environment, so it is characterized as an enemy"""
    def __init__(self, window, world, pos):
        super().__init__(window, world)

        self.image = pyg.Surface((80, 80))
        self.rect = self.image.get_rect()
        self.rect.center = pos

        self.draw_rect = self.rect
        self.collide_rect = self.rect.inflate(-15, -15)

        self.vel.x = 0
        self.vel.y = 0

        self.hp = 5

    def update(self, player):
        for bullet in self.world.bullets:
            if bullet.owner == 'player':
                if self.collide_rect.colliderect(bullet.rect):
                    self.hp -= 1
                    if not bullet.invulnerable:
                        bullet.kill()

        if self.hp <= 0:
            self.image.fill((0, 200, 0))
            player.collect_crystal()


class Archer(Enemy):
    """A class to represent an enemy that trys to stay a moderate distance
       from the player, as well as firing arrows towards the player."""
    def __init__(self, window, world, pos):
        super().__init__(window, world)

        self.image = archer_assets['archer']
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.draw_rect = self.rect
        self.collide_rect = self.rect.inflate(15, 15)

        self.b_image = archer_assets['arrow']
        self.b_rect = self.b_image.get_rect()

        self.speed = 2.5
        self.dir = 0
        self.score = 30

        self.close_range = 400
        self.fire_range = 600

        self.hp = 1
        self.damage = 1
        self.fire_tick = 2 * FPS//8 # Fire once every other second
        self.bullet_data = {'image': self.b_image,
                            'rect': self.b_rect,
                            'owner': 'enemy',
                            'source': self.rect.center,
                            'target': (0, 0),
                            'speed': 40,
                            'invulnerable': False,
                            'bouncy': False}


    def update(self, player):
        p_pos = player.rect.center
        # Distance but without sqrt so it's faster
        dist = ((self.rect.centerx - player.rect.centerx)**2 +
                (self.rect.centery - player.rect.centery)**2)

         # If too close to player
        if dist < self.close_range**2 and not player.is_invisible:
            self.dir = math.atan2((p_pos[1] - self.rect.center[1]),
                                  (p_pos[0] - self.rect.center[0]))
            self.vel.x -= math.cos(self.dir) * self.speed
            self.vel.y -= math.sin(self.dir) * self.speed
        elif dist < 3 * self.close_range**2: # Randomly move around
            self.dir = random.triangular(-math.pi, math.pi, self.dir)
            self.vel.x += math.cos(self.dir) * self.speed
            self.vel.y += math.sin(self.dir) * self.speed

            self.speed = .3
        else:
            self.vel.x *= .7
            self.vel.y *= .7

        if dist < self.fire_range**2 and not player.is_invisible:
            self.fire_tick -= 1

        if self.fire_tick <= 0:
            self.fire(p_pos)
            self.fire_tick = 2 * FPS

        super().update()

    def fire(self, p_pos):
        """Fire an arrow from the archer towards the player."""
        self.bullet_data['source'] = self.draw_rect.center
        self.bullet_data['target'] = p_pos

        # Rotate the arrow so it faces the right way
        dir = math.degrees(math.atan2((p_pos[1] - self.rect.center[1]),
                         (p_pos[0] - self.rect.center[0])))
        self.bullet_data['image'] = pyg.transform.rotate(self.b_image, -dir)

        bullet = Bullet(self.window, self.world, self.bullet_data)
        self.world.bullets.add(bullet)

class Charger(Enemy):
    """A class to represent an enemy that has the characteristic to charge
       towards the player whenever they get nearby."""
    def __init__(self, window, world, pos):
        super().__init__(window, world)
        self.image = charger_assets['charger']
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.draw_rect = self.rect
        self.collide_rect = self.rect.inflate(15, 15)

        self.speed = 2
        self.max_speed = 3.4
        self.dir = 0
        self.score = 20

        self.seek_range = 500

        self.damage = 2

        self.hp = 1

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

        super().update()

    def render(self):
        super().render()


class Dummy(Enemy):
    def __init__(self, window, world, pos):
        super().__init__(window, world)
        self.image = dummy_assets['dummy']
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


class Sensor(pyg.sprite.Sprite):
    def __init__(self, window, world, rect, type, detail, num_uses=-1):
        super().__init__()
        self.window = window
        self.world = world
        self.rect = rect
        self.draw_rect = rect
        self.type = type
        self.detail = detail

        self.color = (0, 0, 0)

        self.num_uses = num_uses

    def trigger(self):
        self.world.trigger(self.type, self.detail, self.rect)
        self.num_uses -= 1
        if self.num_uses == 0:
            self.kill()

    def update(self, player):
        if self.type == 'touch':
            if self.draw_rect.colliderect(player.draw_rect):
                self.triggered = True
                self.color = (0, 250, 0)
            else:
                self.triggered = False
                self.color = (0, 0, 0)

        if self.triggered:
            self.trigger()

    def render(self):
        pyg.draw.rect(self.window, self.color, self.draw_rect, 10)


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
        self.hp_sheet = hud_assets['hp']

        self.text_col = (0, 150, 200)

        self.hp_rect_full = pyg.Rect(0, 0, 52, 47)
        self.hp_rect_empty = pyg.Rect(53, 0, 52, 47)
        self.hp_rect = pyg.rect.Rect(0, 0, 1000, 47)
        self.hp_image = pyg.Surface(self.hp_rect.size, flags=pyg.SRCALPHA)
        self.hp_image.fill((0, 0, 0, 0))
        self.hp_rect.topleft = (10, 10)

        self.score_image = fonts['apache32'].render(str(self.player.score), True, self.text_col)
        self.score_rect = self.score_image.get_rect()
        self.score_rect.bottomright = (WIDTH - 10, HEIGHT - 10)

        self.pos_image = fonts['apache32'].render(str(self.player.rect.center), True, self.text_col)
        self.pos_rect = self.pos_image.get_rect()
        self.pos_rect.topright = (WIDTH - 10, 10)

        self.level_image = fonts['coffee24'].render(f'Current Level: {level}', True, self.text_col)
        self.level_rect = self.level_image.get_rect()
        self.level_rect.topright = self.pos_rect.move(0, 10).bottomright

        self.fps_image = fonts['coffee24'].render('FPS: 0', True, self.text_col)
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
            self.score_image = fonts['apache32'].render(str(self.player.score), True, self.text_col)
            self.score_rect = self.score_image.get_rect()
            self.score_rect.bottomright = (WIDTH - 10, HEIGHT - 10)

        if 'pos' in args:
            self.pos_image = fonts['apache32'].render(str(self.player.rect.topleft), True, self.text_col)
            self.pos_rect = self.pos_image.get_rect()
            self.pos_rect.topright = (WIDTH - 10, 10)

        if 'level' in args:
            self.level_image = fonts['coffee24'].render(f'Current Level: {args[-1]}', True, self.text_col)
            self.level_rect = self.level_image.get_rect()
            self.level_rect.topright = self.pos_rect.move(0, 10).bottomright

        if 'fps' in args:
            self.fps_image = fonts['coffee24'].render(f'FPS: {args[-1]}', True, self.text_col)
            self.fps_rect = self.fps_image.get_rect()
            self.fps_rect.topright = self.level_rect.move(0, 10).bottomright

    def render(self):
        self.window.blit(self.hp_image, self.hp_rect)
        self.window.blit(self.score_image, self.score_rect)
        self.window.blit(self.pos_image, self.pos_rect)
        self.window.blit(self.level_image, self.level_rect)
        self.window.blit(self.fps_image, self.fps_rect)


class PauseMenu():
    def __init__(self, window):
        self.window = window

        self.grayout = pyg.Surface((WIDTH, HEIGHT)).convert_alpha()
        self.grayout.fill((0, 0, 0, 100))

        self.button_text = ['CONTINUE', 'OPTIONS', 'EXIT']
        self.buttons = self.make_buttons()
        self.arrange_buttons()

    def make_buttons(self):
        buttons = []

        for text in self.button_text:
            image = fonts['londrina36'].render(f'| {text} |', True, (0, 150, 250))
            rect = image.get_rect()
            buttons.append([image, rect, text])

        return buttons

    def arrange_buttons(self):
        # Center all buttons in a vertical stack in the middle of the screen
        for i, button in enumerate(self.buttons):
            button[1].centerx = WIDTH//2
            button[1].centery = HEIGHT//2 + 120*i - 60*len(self.buttons) + 60

    def update(self):
        m_pos = pyg.mouse.get_pos()
        for i, button in enumerate(self.buttons):
            if button[1].collidepoint(m_pos):
                button[0] = fonts['londrina40'].render(f'| {self.button_text[i]} |', True, (0, 150, 250))
            else:
                button[0] = fonts['londrina36'].render(f'| {self.button_text[i]} |', True, (0, 150, 250))
            button[1] = button[0].get_rect()

        self.arrange_buttons()

    def render(self):
        self.window.blit(self.grayout, (0, 0))
        for b in self.buttons:
            self.window.blit(b[0], b[1])


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
                      world.sensors.sprites() +
                      world.pickups.sprites() +
                      world.enemies.sprites() +
                      world.fogs.sprites() +
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
        self.sensors = pyg.sprite.Group()
        self.pickups = pyg.sprite.Group()
        self.enemies = pyg.sprite.Group()
        self.bullets = pyg.sprite.Group()
        self.fogs = pyg.sprite.Group()

        self.saved_levels = {}

    def save_level(self, cur_level):
        self.saved_levels[cur_level] = {'rooms': self.rooms[:],
                                        'walls': self.walls.copy(),
                                        'statics': self.statics.copy(),
                                        'sensors': self.sensors.copy(),
                                        'pickups': self.pickups.copy(),
                                        'enemies': self.enemies.copy(),
                                        'bullets': self.bullets.copy(),
                                        'fogs': self.fogs.copy(),
                                        'up_ladder': self.up_ladder,
                                        'down_ladder': self.down_ladder,
                                        'crystal': self.crystal}

    def gen_saved_level(self, level, dir):
        self.rooms = []
        self.walls.empty()
        self.statics.empty()
        self.sensors.empty()
        self.pickups.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.fogs.empty()

        self.rooms = self.saved_levels[level]['rooms']
        self.walls = self.saved_levels[level]['walls']
        self.statics = self.saved_levels[level]['statics']
        self.sensors = self.saved_levels[level]['sensors']
        self.pickups = self.saved_levels[level]['pickups']
        self.enemies = self.saved_levels[level]['enemies']
        self.fogs = self.saved_levels[level]['fogs']

        self.up_ladder = self.saved_levels[level]['up_ladder']
        self.down_ladder = self.saved_levels[level]['down_ladder']
        self.crystal = self.saved_levels[level]['crystal']

        if dir == 'up':
            self.spawn = self.down_ladder.rect.center
        elif dir == 'down':
            self.spawn = self.up_ladder.rect.center

    def trigger(self, type, detail, sensor_rect):
        """Executes every tick while a sensor is activated."""
        if type == 'touch':
            ...

    def generate(self, level, dir):
        """Create a given level randomly. Until level 10, use grid
        generation, in which a grid of rooms is created, then a maze is
        constructed that reaches every room.
        """

        if level in self.saved_levels.keys():
            self.gen_saved_level(level, dir)
            return

        self.rooms = []
        self.walls.empty()
        self.statics.empty()
        self.sensors.empty()
        self.pickups.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.fogs.empty()

        is_bottom_level = False
        if level == 10:
            is_bottom_level = True

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
                    room = self.create_room('regular', (x, y))
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
            exit = visited[random.randint(-3, -1)]

            self.rooms[start].set_features('start')
            self.up_ladder = self.rooms[start].statics[0]
            self.spawn = self.up_ladder.rect.center

            if is_bottom_level:
                self.rooms[exit].set_features('crystal')
                self.down_ladder = None
                self.crystal = self.rooms[exit].enemies[0]
            else:
                self.rooms[exit].set_features('exit')
                self.down_ladder = self.rooms[exit].statics[0]
                self.crystal = None

            random.choice(self.rooms[2:-4]).add_features('treasure')
            random.choice(self.rooms[2:-4]).add_features('danger')

            self.walls.add([room.walls for room in self.rooms])
            self.statics.add([room.statics for room in self.rooms])
            self.sensors.add([room.sensors for room in self.rooms])
            self.pickups.add([room.pickups for room in self.rooms])
            self.enemies.add([room.enemies for room in self.rooms])
            self.fogs.add([room.fogs for room in self.rooms])

            self.update_wall_textures()


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

    def create_room(self, type, pos):
        size_x = 750
        size_y = 600
        room_rect = pyg.rect.Rect(pos[0], pos[1], size_x, size_y)

        room = Room(self.window, self, room_rect, type)

        return room

    def update_wall_textures(self):
        for wall in self.walls:
            needed_covers = set(['top', 'bottom', 'left', 'right'])

            if wall.rect.top == self.rect.top: # Remove covers if on the edge of the map
                needed_covers.discard('top')
            if wall.rect.bottom == self.rect.bottom:
                needed_covers.discard('bottom')
            if wall.rect.right == self.rect.right:
                needed_covers.discard('right')
            if wall.rect.left == self.rect.left:
                needed_covers.discard('left')

            for other in self.walls: # Loop through each wall again to check for connected walls
                if wall.rect.y == other.rect.y:
                    if wall.rect.left == other.rect.right:
                        needed_covers.discard('left')
                    if wall.rect.right == other.rect.left:
                        needed_covers.discard('right')

                if wall.rect.x == other.rect.x:
                    if wall.rect.top == other.rect.bottom:
                        needed_covers.discard('top')
                    if wall.rect.bottom == other.rect.top:
                        needed_covers.discard('bottom')

            # if wall.type == 'corner':
            #     needed_covers.add('tr')
            #     needed_covers.add('tl')
            #     needed_covers.add('br')
            #     needed_covers.add('bl')
            #     if wall.rect.top == self.rect.top: # Remove covers if on the edge of the map
            #         needed_covers.discard('tr')
            #         needed_covers.discard('tl')
            #         needed_covers.discard('br')
            #         needed_covers.discard('bl')
            #     if wall.rect.bottom == self.rect.bottom:
            #         needed_covers.discard('tr')
            #         needed_covers.discard('tl')
            #         needed_covers.discard('br')
            #         needed_covers.discard('bl')
            #     if wall.rect.right == self.rect.right:
            #         needed_covers.discard('tr')
            #         needed_covers.discard('br')
            #     if wall.rect.left == self.rect.left:
            #         needed_covers.discard('tl')
            #         needed_covers.discard('bl')
            #
            #     for other in self.walls:
            #         if other.type == 'corner':
            #             if wall.rect.y == other.rect.y:
            #                 if wall.rect.left == other.rect.right:
            #                     needed_covers.discard('bl')
            #                 if wall.rect.right == other.rect.left:
            #                     needed_covers.discard('br')
            #
            #             if wall.rect.x == other.rect.x:
            #                 if wall.rect.top == other.rect.bottom:
            #                     needed_covers.discard('tl')
            #                 if wall.rect.bottom == other.rect.top:
            #                     needed_covers.discard('tr')

            wall.add_covers(needed_covers)


class WorldDecoration():
    def __init__(self, window, world):
        """A class similar to World() in that it is a organization class.
        However, this class only contains things not essential to gameplay.
        E.g. the background and ambient decoration."""
        self.window = window
        self.world = world

        # self.bg_set_1 = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'background', 'bg_set_1.png')))
        # self.bg_set_2 = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'background', 'bg_set_2.png')))
        self.bg_set_3 = world_decor_assets['bg_set_3']
        self.bg_set_4 = world_decor_assets['bg_set_4']

    def generate(self, cur_level):
        self.bg_rect = self.world.rect
        self.bg_rect.topleft = self.world.rect.topleft
        self.bg_draw_rect = self.bg_rect
        self.bg = pyg.Surface((self.bg_rect.size)).convert()

        self.bg_color = (20, 20, 20)
        self.bg.fill(self.bg_color)

        # Create a static background generated from a spritesheet
        for y in range(0, self.bg_rect.height, 50):
            for x in range(0, self.bg_rect.width, 50):
                rect = pyg.rect.Rect(0, 0, 50, 50)
                rect.x = 50 * random.randint(0, 3)
                rect.y = 50 * random.randint(0, 1)
                self.bg.blit(self.bg_set_4, (x, y), rect)

        self.bg.convert()

    def render_bg(self):
        self.window.fill(self.bg_color)
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
    def __init__(self, window, world, rect, type):
        self.window = window
        self.world = world
        self.rect = rect
        self.walls = []
        self.statics = []
        self.sensors = []
        self.pickups = []
        self.enemies = []
        self.fogs = []

        assert type in ['regular', 'start', 'exit', 'treasure', 'danger',
                        'crystal']

         # Create the corners of the room
        pos = [(0, 0),
               (self.rect.width - 75, 0),
               (0, self.rect.height - 75),
               (self.rect.width - 75, self.rect.height - 75)]
        for corn in pos:
            pos = (corn[0] + self.rect.x, corn[1] + self.rect.y)
            wall = Wall(self.window, pos, 'corner', 'default')
            self.walls.append(wall)

        # Create the walls between each corner
        # Top
        for x in range(75, self.rect.width - 75, 150):
            pos = (x + self.rect.x, self.rect.y)
            wall = Wall(self.window, pos, 'rl', 'default')
            self.walls.append(wall)

        # Bottom
        for x in range(75, self.rect.width - 75, 150):
            pos = (x + self.rect.x, self.rect.y + self.rect.height - 75)
            wall = Wall(self.window, pos, 'rl', 'default')
            self.walls.append(wall)

        # Right
        for y in range(75, self.rect.height - 75, 150):
            pos = (self.rect.x + self.rect.width - 75, y + self.rect.y)
            wall = Wall(self.window, pos, 'ud', 'default')
            self.walls.append(wall)

        # Left
        for y in range(75, rect.height - 75, 150):
            pos = (rect.x, y + rect.y)
            wall = Wall(self.window, pos, 'ud', 'default')
            self.walls.append(wall)

        self.add_features(type)

    def remove_wall(self, side, pos):
        side_walls = []
        if side == 'top': # Get all the walls on a certain side
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

        if side in ['top', 'bottom']: # Sort the walls by their coords
            side_walls.sort(key=lambda wall: wall.rect.x)
        else:
            side_walls.sort(key=lambda wall: wall.rect.y)

        for i in pos: # Remove the walls specified
            self.walls.remove(side_walls[i])

    def set_features(self, type):
        self.statics = []
        self.sensors = []
        self.pickups = []
        self.enemies = []
        self.fogs = []

        self.add_features(type)

    def add_features(self, type):
        """Generate any special decorations etc."""
        if type == 'start':
            pos = (random.randint(self.rect.x + 200, self.rect.right - 200),
                      random.randint(self.rect.y + 200, self.rect.bottom - 200))
            self.statics.append(Ladder(self.window, pos, 'up'))

        elif type == 'exit':
            pos = (random.randint(self.rect.x + 200, self.rect.right - 200),
                      random.randint(self.rect.y + 200, self.rect.bottom - 200))
            self.statics.append(Ladder(self.window, pos, 'down'))

        elif type == 'treasure':
             # Create a bunch of cubes centered around a random point in the room
            center = (random.randint(self.rect.x + 200, self.rect.right - 200),
                      random.randint(self.rect.y + 200, self.rect.bottom - 200))
            for i in range(random.randint(8, 12)):
                image = pickup_assets['cube']
                pos = (center[0] + random.randint(-75, 75), center[1] + random.randint(-75, 75))
                pickup = Pickup(self.window, {'image': image, 'pos': pos, 'type': 'cube'})
                self.pickups.append(pickup)

        elif type == 'danger':
            self.statics.append(Fountain(self.window, self.rect.center))

            pos = (random.randint(self.rect.x + 200, self.rect.right - 200),
                   random.randint(self.rect.y + 200, self.rect.bottom - 200))
            self.enemies.append(Charger(self.window, self.world, pos))
            self.enemies.append(Archer(self.window, self.world, pos))

        elif type == 'crystal':
            self.enemies.append(Crystal(self.window, self.world, self.rect.center))

        elif type == 'regular':
            # The regular room has a 50% chance to have pickups
            # If the room has pickups, also spawn enemies
            if random.random() < .5:
                num_p = random.randint(2, 5)
                num_e = random.randint(1, 2)
            else:
                num_p = 0
                num_e = 0

            for i in range(num_p):
                p_type = random.choices(['hp', 'cube'], weights=[1, 3], k=1)[0]
                if p_type == 'hp':
                    image = pickup_assets['hp']
                elif p_type == 'cube':
                    image = pickup_assets['cube']
                pos = (random.randint(self.rect.x + 100, self.rect.right - 100),
                       random.randint(self.rect.y + 100, self.rect.bottom - 100))
                pickup = Pickup(self.window, {'image': image, 'pos': pos, 'type': f'{p_type}'})
                self.pickups.append(pickup)

            for i in range(num_e):
                e_type = random.choices(['dummy', 'archer'], weights=[4, 1], k=1)[0]
                pos = (random.randint(self.rect.x + 100, self.rect.right - 100),
                       random.randint(self.rect.y + 100, self.rect.bottom - 100))
                if e_type == 'dummy':
                    enemy = Dummy(self.window, self.world, pos)
                elif e_type == 'archer':
                    enemy = Archer(self.window, self.world, pos)
                self.enemies.append(enemy)

        fog = RoomFog(self.window, self.rect.center)
        self.fogs.append(fog)

    def move(self, pos):
        sprite_list = self.walls + self.pickups + self.statics + self.sensors

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
    def __init__(self, window, pos, type, theme):
        self.type = type
        self.theme = theme
        self.image = pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'{self.type}.png')))
        super().__init__(window, pos, False)
        self.collide_rect = self.rect.inflate(-20, -30)
        self.collide_rect.bottom -= 5

        self.covers = {'top': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'{self.type}_top.png'))),
                       'bottom': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'{self.type}_bottom.png'))),
                       'right': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'{self.type}_right.png'))),
                       'left': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'{self.type}_left.png'))),
                       'br': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'corner_br.png'))),
                       'bl': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'corner_bl.png'))),
                       'tr': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'corner_tr.png'))),
                       'tl': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'walls', theme, f'corner_tl.png')))}

    def add_covers(self, covers):
        for c in covers:
            self.image.blit(self.covers[c], (0, 0))

class Fountain(StaticObject):
    def __init__(self, window, pos):
        self.image = static_assets['fountain']
        super().__init__(window, pos, True)
        self.collide_rect = self.rect.inflate(-20, -6)


class Ladder(StaticObject):
    def __init__(self, window, pos, dir):
        self.image = static_assets[f'ladder_{dir}']
        super().__init__(window, pos, True)
        # Ladders do not use the collision rect, but a collide_rect
        # attribute is required, so set it to zeros
        self.collide_rect = pyg.rect.Rect(0, 0, 0, 0)


class RoomFog(StaticObject):
    def __init__(self, window, pos):
        """A class to represent the 'fog of war' effect. It is classified as a
        StaticObject because it does not move, however it differs from other
        StaticObjects because it has an update(player) method that detects if
        it has collided with the player. If it does, it kills itself."""
        self.image = pyg.Surface((750, 600)).convert()
        self.image.fill((20, 20, 20))
        super().__init__(window, pos, True)
        # A collide_rect attribute is required, but it won't be used
        # so set it to zeros
        self.collide_rect = pyg.rect.Rect(0, 0, 0, 0)

    def update(self, player):
        if self.rect.colliderect(player.rect):
            self.kill()


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
    if type == 'hp':
        image = pickup_assets['hp']
    elif type == 'cube':
        image = pickup_assets['cube']
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
    pointer = mouse_assets['pointer']
    pointer_rect = pointer.get_rect()

     # Custom Events
    custom_event = pyg.USEREVENT + 1
    pyg.time.set_timer(custom_event, 50)

    cur_level = 1
    world = World(window)
    world.generate(cur_level, 'nodir')

    world_decor = WorldDecoration(window, world)
    world_decor.generate(cur_level)

    player = Player(window, world)
    player.rect.center = world.spawn

    hud = HUD(window, player, cur_level)
    player.add_hud(hud)

    render_sensors = False

    textboxes = []

    cheat_codes = {'speed': False,
                   'free_move': False,
                   'invisibility': False}

    clock = pyg.time.Clock()

    paused = False
    pause_menu = PauseMenu(window)

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
                        if player.collide_rect.colliderect(world.up_ladder.rect):
                            if cur_level == 1:
                                if player.has_crystal:
                                    win()
                            else:
                                world.save_level(cur_level)
                                cur_level -= 1
                                world.generate(cur_level, 'up')
                                player.rect.center = world.spawn
                                hud.update('level', cur_level)
                        elif world.down_ladder != None:
                            if player.collide_rect.colliderect(world.down_ladder.rect):
                                world.save_level(cur_level)
                                cur_level += 1
                                world.generate(cur_level, 'down')
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
                # elif event.type == pyg.WINDOWEVENT:
                #     if event.event == 'WINDOWEVENT_FOCUS_LOST':
                #         paused = True

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
            if world.down_ladder != None:
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

            # for s in world.sensors:
            #     s.update(player)
            # if render_sensors:
            #     for s in world.sensors:
            #         s.render()

            for s in world.statics:
                s.render()

            for b in world.bullets:
                b.update()
                b.render()

            for e in world.enemies:
                e.update(player)
            for e in world.enemies:
                e.render()

            player.update()
            player.render()

            for w in world.walls:
                w.render()

            for f in world.fogs:
                f.update(player)
                f.render()

            for t in textboxes:
                t.render()
            textboxes = []

            hud.update('fps', round(clock.get_fps()))
            hud.render()

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
                elif event.type == pyg.MOUSEBUTTONDOWN:
                    for button in pause_menu.buttons:
                        if button[1].collidepoint(event.pos):
                            if button[2] == 'EXIT':
                                terminate()
                            elif button[2] == 'CONTINUE':
                                paused = False
                            # elif button[2] == 'OPTIONS':
                            #     print('OPTIONS')

            world_decor.render_bg()

            for p in world.pickups:
                p.render()

            for b in world.bullets.sprites():
                b.render()

            # if render_sensors:
            #     for s in world.sensors:
            #         s.render()

            for s in world.statics:
                s.render()

            for e in world.enemies:
                e.render()

            player.render()

            for w in world.walls:
                w.render()

            for f in world.fogs:
                f.render()

            hud.update('fps', round(clock.get_fps()))
            hud.render()

            pause_menu.update()
            pause_menu.render()

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

    # Import assets after pygame is initalized
    from asset_loader import *

    main()
