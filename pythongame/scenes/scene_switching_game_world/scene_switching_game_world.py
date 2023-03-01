from typing import Optional, Callable, Tuple

from pythongame.core.common import Millis, AbstractScene, SceneTransition, AbstractWorldBehavior
from pythongame.core.global_path_finder import init_global_path_finder
from pythongame.scenes.scene_factory import AbstractSceneFactory
from pythongame.scenes.scenes_game.game_engine import GameEngine
from pythongame.scenes.scenes_game.game_ui_view import GameUiView
from pythongame.world_init_util import register_game_engine_observers, register_game_state_observers


class SwitchingGameWorldScene(AbstractScene):
    def __init__(
            self,
            scene_factory: AbstractSceneFactory,
            game_engine: GameEngine,
            ui_view: GameUiView,
            character_file: str,
            total_time_played_on_character: Millis,
            create_new_game_engine_and_behavior: Callable[[GameEngine], Tuple[GameEngine, AbstractWorldBehavior]]):
        self.scene_factory = scene_factory
        self.previous_game_engine = game_engine
        self.ui_view = ui_view
        self.character_file = character_file
        self.total_time_played_on_character = total_time_played_on_character
        self.create_new_game_engine_and_behavior = create_new_game_engine_and_behavior

    def run_one_frame(self, _time_passed: Millis) -> Optional[SceneTransition]:
        # movement speed affects the hero entity in the game state (in contrast to other stats)
        player_speed_multiplier = self.previous_game_engine.game_state.game_world.player_entity.get_speed_multiplier()

        # NPC's share a "global path finder" that needs to be initialized before we start creating NPCs.
        # TODO This is very messy
        path_finder = init_global_path_finder()
        new_game_engine, new_world_behavior = self.create_new_game_engine_and_behavior(self.previous_game_engine)
        new_game_state = new_game_engine.game_state
        path_finder.set_grid(new_game_state.pathfinder_wall_grid)

        # Must center camera before notifying player position as it affects which walls are shown on the minimap
        new_game_state.center_camera_on_player()
        self.ui_view.on_world_area_updated(new_game_state.game_world.entire_world_area)

        # We set up observers for gameEngine and gameState, since they are newly created in this scene. The player
        # state's observers (ui view) have already been setup in an earlier scene however.
        register_game_engine_observers(new_game_engine, self.ui_view)
        register_game_state_observers(new_game_state, self.ui_view, include_player_state=False)

        new_game_state.game_world.set_hero_movement_speed(player_speed_multiplier)

        # Clear any messages to give space for any messages generated by the new world behavior
        self.ui_view.info_message.clear_messages()

        # If we don't clear the minimap, there will be remains from the previous game state
        self.ui_view.minimap.clear_exploration()

        playing_scene = self.scene_factory.playing_scene(
            game_state=new_game_state,
            game_engine=new_game_engine,
            world_behavior=new_world_behavior,
            ui_view=self.ui_view,
            new_hero_was_created=False,
            character_file=self.character_file,
            total_time_played_on_character=self.total_time_played_on_character)
        return SceneTransition(playing_scene)
