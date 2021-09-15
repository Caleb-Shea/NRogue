import pygame as pyg
import os

from main import get_path

player_assets = {'img_sheet': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'player', 'normal_sheet.png'))).convert_alpha(),
                 'score_sound': pyg.mixer.Sound(get_path(os.path.join('assets', 'audio', 'score_up.wav')))}

pickup_assets = {'shadow': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'shadows', 'pickup.png'))).convert_alpha(),
                 'cube': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'pickups', 'cube.png'))),
                 'hp': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'pickups', 'hp.png')))}

fonts = {'apache32': pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'apache.ttf')), 32),
         'apache30': pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'apache.ttf')), 30),
         'coffee30': pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'coffee.ttf')), 30),
         'coffee24': pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'coffee.ttf')), 24),
         'londrina36': pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'Londrina.otf')), 36),
         'londrina40': pyg.font.Font(get_path(os.path.join('assets', 'fonts', 'Londrina.otf')), 40)}

slingshot_assets = {'slingshot': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'weapons', 'slingshot.png'))).convert_alpha(),
                    'pebble': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'weapons', 'pebble.png'))).convert_alpha()}

lasergun_assets = {'lasergun': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'weapons', 'lasergun.png'))).convert_alpha()}

archer_assets = {'archer': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'archer.png'))).convert_alpha(),
                 'arrow': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'arrow.png'))).convert_alpha()}

charger_assets = {'charger': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'charger.png'))).convert_alpha()}

dummy_assets = {'dummy': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'sprites', 'Dummy.png'))).convert_alpha()}

hud_assets = {'hp': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'hud', 'hp.png'))).convert_alpha()}

world_decor_assets = {'bg_set_1': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'background', 'bg_set_1.png'))),
                      'bg_set_2': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'background', 'bg_set_2.png'))),
                      'bg_set_3': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'background', 'bg_set_3.png'))),
                      'bg_set_4': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'background', 'bg_set_4.png')))}

static_assets = {'fountain': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'fountain.png'))),
                 'ladder_up': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'ladder', 'up.png'))),
                 'ladder_down': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'world', 'ladder', 'down.png')))}

mouse_assets = {'pointer': pyg.image.load(get_path(os.path.join('assets', 'imgs', 'misc', 'mouse', 'target.png'))).convert_alpha()}
