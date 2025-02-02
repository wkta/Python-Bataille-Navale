#  Copyright © 2019
#  authored by Jean-Baptiste CAILLAUD et al.
#  contributor list on: https://github.com/yShimoka/python-bataille-navale

from copy import copy

import pygame.locals

import engine
from battleships import glvars
from battleships.objects import ShipBoard, ShotBoard
from battleships.objects.InGameConsole import InGameConsole
from battleships.players.Player import Player


class HumanPlayer(Player, engine.InputListener):
    """
    Human player class.
    Allows a human to play the game.
    """

    def __init__(self):
        """
        Class constructor.
        Creates a new HumanPlayer instance.
        """
        super().__init__()

        # Prepares the boat list.
        self.boat_list = None
        self.fleet = None

        # Prepare the boards.
        self.ship_board = None
        self.shot_board = None
        self.texts = None

    def start_game(self):
        """
        Starts the game.
        Loads all the boats from the game manager.
        """
        # Loads the boat list.
        self.boat_list = engine.Engine.game_manager.human_boats
        self.fleet = engine.Engine.game_manager.human_fleet

        # Create the ships board.
        self.ship_board = ShipBoard(engine.Engine.scene)
        self.ship_board.placed_ships = self.boat_list
        self.shot_board = ShotBoard(engine.Engine.scene)
        self.ship_board.visible = True
        self.shot_board.visible = False

        # Place the boards on the scene.
        self.ship_board.transform.position = engine.math.Vector2(256, 256)
        self.shot_board.transform.position = engine.math.Vector2(256, 256)

        # Create the texts.
        self.texts = InGameConsole(engine.Engine.scene)
        self.texts.transform.position = engine.math.Vector2(256, 608)

        # Add the boats back to the tree.
        for ship in self.boat_list:
            ship.transform.parent = self.ship_board.transform
            ship.enable_rendering()

    def start_turn(self):
        """
        Starts the turn of the human player.
        """
        self.texts.show_std_text(self.texts.TEXT_GAME_NEW_TURN)

    def end_turn(self):
        """
        Ends the player turn.
        """
        self.texts.show_std_text(self.texts.TEXT_GAME_END_TURN)

    def request_shot(self):
        """
        Triggers the player's fire mode.
        """
        # Display the text.
        self.texts.show_std_text(self.texts.TEXT_GAME_REQ_FIRE)

        # Display the shots board.
        self.shot_board.visible = True
        self.ship_board.visible = False

        # Enable input listening.
        engine.Engine.input_handler.add_listener(self)

    def fire(self, at):
        """
        Fires at the specified location.
        :param at: Where to fire.
        """
        # Call the parent method.
        if super().fire(at):
            engine.Engine.play_sound("Fire")
            # Display the text.
            self.texts.show_std_text(self.texts.TEXT_GAME_DO_SHOOT)
            return True
        else:
            return False

    def request_hit(self, at: engine.math.Vector2):
        """
        Request made by the engine to get the hit status.
        :param at: Where the shot was made.
        """
        # Get the touched boat.
        touched_t = self.fleet.collision_check(at, 1, 1)

        # Display the text.
        self.texts.show_std_text(self.texts.TEXT_GAME_REQ_HIT)

        # Add a hit marker.
        col = engine.TexturedGameObject(
            self.ship_board,
            "WaterSplash" if touched_t is None else "BoatDamage",
            engine.math.Vector2(48, 48)
        )
        col.transform.position = (at * self.shot_board.CELL_SIZE) - (self.shot_board.get_size() / 2)
        col.transform.offset = copy(engine.math.UNIT_VECTOR)

        # Compute the hit status.
        if touched_t is None:
            engine.Engine.play_sound("WaterExplosion")
            # Tell the game that he did not hit.
            self.hit(at, self.SHOT_HIT_TYPE_MISS)
            return

        engine.Engine.play_sound("Explosion")
        # Increment the damages on the boat.
        self.fleet.damage(touched_t)

        if not self.fleet.is_sunk(touched_t):  # hit, but not sunk
            self.hit(at, self.SHOT_HIT_TYPE_HIT)

        else:
            if self.fleet.is_sunk():  # all ships just sunk
                self.hit(at, self.SHOT_HIT_TYPE_GAME_OVER)

            else:  # some ships remain
                self.hit(at, self.SHOT_HIT_TYPE_HIT_AND_SUNK)

    def hit(self, at: engine.math.Vector2, hit_status: int):
        """
        Tells the user that he was hit at the specified location.
        :param at: Where the user was hit.
        :param hit_status: The type of hit he endured.
        """
        super().hit(at, hit_status)
        if hit_status == self.SHOT_HIT_TYPE_MISS:
            self.texts.show_std_text(self.texts.TEXT_GAME_GET_HIT_MISS)
        elif hit_status == self.SHOT_HIT_TYPE_HIT:
            self.texts.show_std_text(self.texts.TEXT_GAME_GET_HIT_HIT)
        else:
            self.texts.show_std_text(self.texts.TEXT_GAME_GET_HIT_SUNK)

    def show_hit(self, at: engine.math.Vector2, hit_type: int):
        """
        Shows the result of our hit on the board.
        :param at: Where the shot landed.
        :param hit_type: The type of shot.
        """
        # Call the parent method.
        super().show_hit(at, hit_type)

        if hit_type == self.SHOT_HIT_TYPE_MISS:
            adhoc_texture_path = "Miss_theme{}".format(glvars.colortheme)
        else:
            adhoc_texture_path = "Hit_theme{}".format(glvars.colortheme)

        # Create the rect on the shot board.
        col = engine.TexturedGameObject(
            self.shot_board, adhoc_texture_path, engine.math.Vector2(48, 48)
        )
        col.transform.position = (at * self.shot_board.CELL_SIZE) - (self.shot_board.get_size() / 2)
        col.transform.offset = copy(engine.math.UNIT_VECTOR)
        engine.Engine.play_sound("WaterExplosion" if hit_type == self.SHOT_HIT_TYPE_MISS else "Explosion")

        # Show the hit status.
        if hit_type == self.SHOT_HIT_TYPE_MISS:
            self.texts.show_std_text(self.texts.TEXT_GAME_SHOW_HIT_MISS)
        elif hit_type == self.SHOT_HIT_TYPE_HIT:
            self.texts.show_std_text(self.texts.TEXT_GAME_SHOW_HIT_HIT)
        else:
            self.texts.show_std_text(self.texts.TEXT_GAME_SHOW_HIT_SUNK)

    def await_opponent_shot(self):
        self.shot_board.visible = False
        self.ship_board.visible = True
        self.texts.show_std_text(self.texts.TEXT_GAME_AWAIT_SHOT)

    def handle_input(self, event):
        """
        Handles player shooting input.
        :param event: The event to parse.
        """
        # If the event is a mouse down.
        if event.type == pygame.locals.MOUSEBUTTONDOWN:
            # If the mouse position is on the shots board.
            m_pos = engine.math.Vector2(event.pos[0], event.pos[1])
            b_topl = self.shot_board.get_top_left()
            b_size = self.shot_board.get_size()
            if engine.math.Vector2.in_rect(m_pos, b_topl, b_size):
                # Request a fire at the given position.
                if self.fire((m_pos - b_topl) // self.shot_board.CELL_SIZE):
                    # Stop listening to inputs.
                    engine.Engine.input_handler.remove_listener(self)
