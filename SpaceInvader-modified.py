import sys
from abc import ABC, abstractmethod
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer
from PyQt6.QtGui import QColor, QPainter, QPixmap, QFont, QLinearGradient, QPen
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox, QPushButton
import pandas as pd
from pathlib import Path
import random
import sounds

class GameObject(ABC):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
    @abstractmethod
    def update(self):
        pass
    @abstractmethod
    def draw(self, painter):
        pass

class Player(GameObject):
    SPEED = 5

    def __init__(self, x,y):
        super().__init__(x,y)
        self.lives = 1

    def move_left(self):
        self.x -= self.SPEED
    def move_right(self):
        self.x += self.SPEED
    def update(self):
        pass
    def draw(self, painter):
        painter.drawPixmap(int(self.x), int(self.y), 90, 80, Player.sprite)

    def shot(self):
        self.lives -= 1
        if self.lives <= 0:
            self.active = False

        return self.active

class Enemy(GameObject):
    WIDTH = 70
    HEIGHT = 70
    SPEED = 2
    sprite: QPixmap

    def __init__(self, x, y):
        super().__init__(x, y)
        self.direction = 1

    def update(self):
        self.x += self.direction * self.SPEED
        if self.x < 0:
            self.direction = 1
            self.y += 20
        elif self.x > 960:
            self.direction = -1
            self.y += 20

    def draw(self, painter):
        painter.drawPixmap(int(self.x), int(self.y), Enemy.WIDTH, Enemy.HEIGHT, Enemy.sprite)

class Bullet(GameObject):
    def __init__(self, x, y, owner):
        super().__init__(x, y)
        self.owner = owner

    def update(self):
        if self.owner:
            self.y -= 8
        else:
            self.y += 8

        if self.y < 0 or self.y > 700:
            self.active = False

    def draw(self, painter):
        painter.setBrush(QColor("yellow"))
        painter.drawRect(
            int(self.x),
            int(self.y),
            4,
            10
        )

class Boss(Enemy):
    sprite: QPixmap
    def __init__(self, x, y):
        super().__init__(x, y)
        self.lives = 12

    def draw(self, painter):
        painter.drawPixmap(
            int(self.x), int(self.y),
            Enemy.WIDTH, Enemy.HEIGHT,
            Boss.sprite
        )

    def shot(self):
        self.lives -= 1
        if self.lives == 0:
            self.active = False

class World:
    def __init__(self):
        self.game = None
        self.score = 0
        self.player = Player(480, 660)
        self.objects = pd.Series([self.player])
        self.create_enemies()

    def create_enemies(self):
        formation = random.choice(["rectangle","triangle"])

        # put boss spawn in formations to adjust positions
        # enemies spawn afterwards in formation
        if formation == "rectangle":
            for row in range(3):
                for col in range(8):
                    self.objects.loc[len(self.objects)] = Enemy(Enemy.WIDTH//2 + col * Enemy.WIDTH, 50 + row * Enemy.HEIGHT)

            self.objects.loc[len(self.objects)] = Boss(50 + 4 * 60, 50 + 3 * 50)

        elif formation == "triangle":
            for row in range(5):
                for col in range(5 - row):
                    x = 140 + col * 60 + row * 30
                    y = 50 + row * 50
                    self.objects.loc[len(self.objects)] = Enemy(x, y)
            
            self.objects.loc[len(self.objects)] = Boss(260, 190)
    
    def add_object(self, obj):
        next_index = self.objects.index.max() + 1 if not self.objects.empty else 0
        self.objects.loc[next_index] = obj

    def update(self):
        self.objects.apply(lambda obj: obj.update())

        self.enemy_shoot()

        self.check_collisions()

        self.objects = self.objects[
            self.objects.apply(lambda obj: obj.active)
        ]

    def check_collisions(self):
        bullets = self.objects[self.objects.apply(lambda obj: isinstance(obj, Bullet))]
        enemies = self.objects[self.objects.apply(lambda obj: isinstance(obj, Enemy) and not isinstance(obj, Boss))]
        bosses =  self.objects[self.objects.apply(lambda obj: isinstance(obj, Boss))]
        players = self.objects[self.objects.apply(lambda obj: isinstance(obj, Player))]

        if enemies.empty and bosses.empty:
            self.game.timer.stop()
            elapsed = self.game.elapsed_seconds
            ret = QMessageBox.information(
                None,
                "Game Over",
                f"You Win!\n\nTime elapsed: {elapsed} seconds"
            )
            if ret == QMessageBox.StandardButton.Ok:
                QApplication.quit()

        if (enemies.apply(lambda enemy: enemy.y + 20 >= self.player.y)).any() or (bosses.apply(lambda boss: boss.y + Enemy.HEIGHT >= self.player.y)).any():
            self.game.timer.stop()
            ret = QMessageBox.information(
                None,
                "Game Over",
                "The aliens reached your ship!"
            )
            if ret == QMessageBox.StandardButton.Ok:
                QApplication.quit()
        
        if len(enemies) < 18:
            Enemy.SPEED = 4
        if len(enemies) < 12:
            Enemy.SPEED = 7
        if len(enemies) < 10:
            Enemy.SPEED = 10
        if len(enemies) < 5:
            Enemy.SPEED = 15

        for bullet in bullets:
            for enemy in enemies:
                if (
                    bullet.x < enemy.x + Enemy.WIDTH
                    and bullet.x + 4 > enemy.x
                    and bullet.y < enemy.y + Enemy.HEIGHT
                    and bullet.y + 10 > enemy.y
                    and bullet.active
                    and bullet.owner
                ):
                    bullet.active = False
                    enemy.active = False
                    self.score += 100

            for boss in bosses:
                if (
                    bullet.x < boss.x + Enemy.WIDTH
                    and bullet.x + 4 > boss.x
                    and bullet.y < boss.y + Enemy.HEIGHT
                    and bullet.y + 10 > boss.y
                    and bullet.active
                    and bullet.owner
                ):
                    bullet.active = False
                    boss.shot()
                    self.score += 500

            for player in players:
                if (
                    bullet.x < player.x + Enemy.WIDTH
                    and bullet.x + 4 > player.x
                    and bullet.y < player.y + Enemy.HEIGHT
                    and bullet.y + 10 > player.y
                    and bullet.active
                    and not bullet.owner
                ):
                    bullet.active = False
                    
                    if not player.shot():
                        self.game.timer.stop()
                        ret = QMessageBox.information(
                            None,
                            "Game Over",
                            "You got shot :("
                        )
                        if ret == QMessageBox.StandardButton.Ok:
                            QApplication.quit()

    def enemy_shoot(self):
        enemies = self.objects[
            self.objects.apply(
                lambda obj: isinstance(obj, Enemy)
                and obj.active
            )
        ]

        # Limit the number of enemy bullets
        enemy_bullets = self.objects[
            self.objects.apply(
                lambda obj: isinstance(obj, Bullet)
                and not obj.owner
                and obj.active
            )
        ]

        if enemy_bullets.size >= 20:
            return

        # Random chance to shoot
        if enemies.empty or random.random() > 0.01:
            return

        # Pick a random enemy
        shooter = random.choice(list(enemies))

        self.add_object(
            Bullet(
                shooter.x + Enemy.WIDTH // 2,
                shooter.y + Enemy.HEIGHT,
                False
            )
        )

class GameView(QWidget):
    def __init__(self, world):
        super().__init__()
        
        self.world = world
        self.game = None
        self.setFixedSize(1000, 700)
        self.setWindowTitle(
            "Ultra overlords of coding supremacy - Invade the World"
        )
        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        self.background = QPixmap(
            str(Path(__file__).with_name("BG.png"))
        )

        # start button
        self.start_button = QPushButton("START GAME",self)
        self.start_button.setGeometry(375, 420, 250, 60)
        self.start_button.clicked.connect(self.start_game)

        # quit button
        self.quit_button = QPushButton("QUIT",self)
        self.quit_button.setGeometry(375, 500, 250, 50)
        self.quit_button.clicked.connect(QApplication.quit)

        # Button styling
        button_style = """
            QPushButton {
                background-color: #101f19;
                color: #39ff14;
                font-size: 19px;
                font-weight: bold;
                letter-spacing: 2px;
                border: 2px solid #39ff14;
                border-radius: 8px;
            }

            QPushButton:hover {
                background-color: #39ff14;
                color: #07110b;
                border: 2px solid white;
            }

            QPushButton:pressed {
                background-color: #1fa80c;
            }
        """
        self.start_button.setStyleSheet(button_style)
        self.quit_button.setStyleSheet(button_style)

    def start_game(self):
        self.game.started = True
        self.start_button.hide()
        self.quit_button.hide()
        self.game.timer.start(16)
        self.setFocus()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background image
        if not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)
        else:
            painter.fillRect(self.rect(), QColor("#050816"))

        # MENU SCREEN
        if not self.game or not self.game.started:

            # Dark overlay to make the text easier to read
            painter.fillRect(
                self.rect(),
                QColor(0, 0, 0, 150)
            )

            # Decorative central panel
            painter.setPen(QPen(QColor("#39ff14"), 2))
            painter.setBrush(QColor(5, 15, 20, 220))
            painter.drawRoundedRect(
                175, 90, 650, 520, 20, 20
            )

            # Small top label
            painter.setPen(QColor("#39ff14"))
            painter.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
            painter.drawText(
                0, 135, 1000, 30,
                Qt.AlignmentFlag.AlignCenter,
                "★  ARCADE INVASION SYSTEM  ★"
            )

            # Main title
            painter.setPen(QColor("#39ff14"))
            painter.setFont(QFont("Consolas", 52, QFont.Weight.Bold))
            painter.drawText(
                0, 235, 1000, 80,
                Qt.AlignmentFlag.AlignCenter,
                "INVADERS"
            )

            # Underline below title
            painter.setPen(QPen(QColor("#39ff14"), 3))
            painter.drawLine(350, 255, 650, 255)

            # Subtitle
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
            painter.drawText(
                0, 300, 1000, 40,
                Qt.AlignmentFlag.AlignCenter,
                "ULTRA OVERLORDS OF CODING SUPREMACY"
            )

            # Tagline
            painter.setPen(QColor("#b5ffad"))
            painter.setFont(QFont("Consolas", 15))
            painter.drawText(
                0, 355, 1000, 35,
                Qt.AlignmentFlag.AlignCenter,
                "DEFEND THE WORLD. DESTROY THE INVADERS."
            )

            # Controls
            painter.setPen(QColor("#aaaaaa"))
            painter.setFont(QFont("Consolas", 12))
            painter.drawText(
                0, 580, 1000, 25,
                Qt.AlignmentFlag.AlignCenter,
                "MOVE:  ←  →       SHOOT:  ↑       QUIT:  ESC"
            )

        # GAME SCREEN
        else:
            for obj in self.world.objects:
                obj.draw(painter)

            # Score display
            painter.setPen(QColor("#39ff14"))
            painter.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
            painter.drawText(
                20, 35,
                f"SCORE: {self.world.score}"
            )

            # Lives display
            painter.setPen(QColor("white"))
            painter.drawText(
                820, 35,
                f"LIVES: {self.world.player.lives}"
            )


class Game:
    def __init__(self, world, view):
        self.world = world
        self.view = view
        self.cooldown_ms = 300
        self.left_pressed = False
        self.right_pressed = False
        self.shoot_pressed = False
        self.last_shot_timer = QElapsedTimer()
        self.last_shot_timer.start()
        self.elapsed_seconds = 0
        self.frames = 0       
        self.world.game = self
        self.view.game = self

        self.started = False

        self.timer = QTimer()
        self.timer.timeout.connect(
            self.game_loop
        )

    def game_loop(self):
        if not self.started:
            return

        player = self.world.player
        if self.left_pressed:
            player.move_left()
        if self.right_pressed:
            player.move_right()
            player.x = max(0, min(960, player.x))

        if self.shoot_pressed:
              sounds.play("shoot")
              if self.last_shot_timer.elapsed() >= self.cooldown_ms:
                    self.world.add_object(
                        Bullet(
                            player.x + 18,
                            player.y,
                            True
                        )
                    )
                    self.last_shot_timer.restart()
                    
        self.world.update()
        self.frames += 1
        if self.frames >= 60:
            self.elapsed_seconds += 1
            self.frames = 0
        self.view.repaint()

    def key_press(self, event):
        if event.key() == Qt.Key.Key_Left:
           self.left_pressed = True
        elif event.key() == Qt.Key.Key_Right:
           self.right_pressed = True
        elif event.key() == Qt.Key.Key_Up:
           self.shoot_pressed = True
        elif event.key() == Qt.Key.Key_Escape:
            QApplication.quit()

    def key_release(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.left_pressed = False
        elif event.key() == Qt.Key.Key_Right:
            self.right_pressed = False
        elif event.key() == Qt.Key.Key_Up:
            self.shoot_pressed = False
        

def main():
    app = QApplication(sys.argv)
    Enemy.sprite = QPixmap(str(Path(__file__).with_name("bug.png")))
    if Enemy.sprite.isNull():
        raise FileNotFoundError("Could not load bug.png")
    Boss.sprite = QPixmap(str(Path(__file__).with_name("boss.png")))
    if Boss.sprite.isNull():
        raise FileNotFoundError("Could not load boss.png")
    Player.sprite = QPixmap(str(Path(__file__).with_name("player.jpeg")))
    if Player.sprite.isNull():
        raise FileNotFoundError("Could not load player.jpeg")

    world = World()
    view = GameView(world)
    game = Game(world, view)
    view.game = game
    view.keyPressEvent = game.key_press
    view.keyReleaseEvent = game.key_release
    view.show()
    sounds.start_music()
    sounds.preload("shoot")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

            # if not bullet.active:
            #     continue

            # for boss in bosses:

            #     if not boss.active:
            #         continue

            #     if (
            #         bullet.x < boss.x + Enemy.WIDTH
            #         and bullet.x + 4 > boss.x
            #         and bullet.y < boss.y + Enemy.HEIGHT
            #         and bullet.y + 10 > boss.y
            #     ):
            #         bullet.active = False
            #         boss.shot()
            #         break


# To do:
# - Fix menu, allow to view high score
# - multiplayer (QTThreads with optional sockets)
# - Add sound effects
# - Customised QWidgets
#  
# Menu
# Change skins?
# Enemies going down, formations
# upgrading items, if you collect then you can upgrade the bullets
# hearts, enemies attack too


# DONE: 
# - different enemy formations
# - Boss enemy - Wyatt
# - Lose and Win condition - Resham
# - Blocks move down individually - Resham
# - User quits via escape - Resham
# - Allow shooting while moving - Wisteria
# - Improve player control (movement is choppy) - Wisteria
# - Background image and player skin - Wisteria
# - pandas integration - Wyatt 
# - Images for sprites - Jonah
# - Make window resizeable - Jonah
# - Different enemy formations - George
# - User quit - Resham
# - boss sprite - Jonah
# - Make enemies move down - resham
# - simplified UML - Jonah (diagrams.net)
# - added score counter - George


# test 




# Team name: "Ultra overlords of coding supremacy" 


