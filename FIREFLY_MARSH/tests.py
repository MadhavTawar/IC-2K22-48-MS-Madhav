"""Automated checks for FIREFLY MARSH. Run:  python tests.py

Runs without a window or speakers (SDL dummy drivers), so it works anywhere.
"""
import os
import subprocess
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import main  # noqa: E402
from main import Game, Item, SoundManager  # noqa: E402

NO_KEYS = pygame.Vector2(0, 0)


class GameTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.score_path = os.path.join(self.temp_dir.name, "highscore.json")
        self.game = Game(high_score_path=self.score_path)
        self.game.start_round()
        self.game.items.clear()          # start every test with an empty arena

    def tearDown(self):
        self.temp_dir.cleanup()

    def put_on_player(self, kind, velocity=(0, 0)):
        item = Item(kind, self.game.player.pos, velocity)
        item.phase = 0.0                 # spiders sway sideways; start the sway at zero for a fixed test
        self.game.items.append(item)
        return item

    def step(self, seconds=1 / 60, direction=NO_KEYS):
        self.game.update_playing(seconds, direction)


class TestLaunchAndMenu(GameTestCase):
    def test_01_game_launches_in_menu_state(self):
        fresh = Game(high_score_path=self.score_path)
        self.assertEqual(fresh.state, "menu")

    def test_02_every_screen_draws(self):
        for state in ("menu", "instructions", "playing", "paused", "gameover"):
            self.game.state = state
            self.game.draw()

    def test_03_start_button_starts_game(self):
        self.game.state = "menu"
        start = self.game.buttons["menu"][0]
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start.rect.center, button=1)
        self.game.handle_event(click)
        self.assertEqual(self.game.state, "playing")

    def test_03b_instructions_and_back_buttons_work(self):
        self.game.state = "menu"
        self.game.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, pos=self.game.buttons["menu"][1].rect.center, button=1))
        self.assertEqual(self.game.state, "instructions")
        self.game.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, pos=self.game.buttons["instructions"][0].rect.center, button=1))
        self.assertEqual(self.game.state, "menu")


class TestMovement(GameTestCase):
    def test_04_moves_in_all_four_directions(self):
        for direction, axis, sign in (((1, 0), "x", 1), ((-1, 0), "x", -1), ((0, 1), "y", 1), ((0, -1), "y", -1)):
            before = getattr(self.game.player.pos, axis)
            self.game.player.move(pygame.Vector2(direction), 0.1)
            after = getattr(self.game.player.pos, axis)
            self.assertGreater((after - before) * sign, 0)

    def test_04b_speed_does_not_depend_on_frame_rate(self):
        one_big = main.Player()
        many_small = main.Player()
        one_big.move(pygame.Vector2(1, 0), 0.1)
        for _ in range(10):
            many_small.move(pygame.Vector2(1, 0), 0.01)
        self.assertAlmostEqual(one_big.pos.x, many_small.pos.x, places=3)

    def test_05_player_cannot_leave_arena(self):
        for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for _ in range(200):
                self.game.player.move(pygame.Vector2(direction), 0.1)
            self.assertTrue(main.ARENA.contains(self.game.player.rect))


class TestItems(GameTestCase):
    def test_06_dew_gives_10_points(self):
        self.put_on_player("dew")
        self.step()
        self.assertEqual(self.game.score, 10)
        self.assertEqual(self.game.items, [])

    def test_07_berry_gives_30_points(self):
        self.put_on_player("berry")
        self.step()
        self.assertEqual(self.game.score, 30)

    def test_08_petal_adds_five_seconds(self):
        self.game.time_left = 50
        self.put_on_player("petal")
        self.step(0.0)
        self.assertAlmostEqual(self.game.time_left, 55)

    def test_08b_petal_respects_time_cap(self):
        self.game.time_left = main.MAX_TIME - 1
        self.put_on_player("petal")
        self.step(0.0)
        self.assertEqual(self.game.time_left, main.MAX_TIME)

    def test_09_hazard_removes_one_life_and_penalty(self):
        self.game.score = 20
        self.put_on_player("spider")
        self.step()
        self.assertEqual(self.game.lives, main.START_LIVES - 1)
        self.assertEqual(self.game.score, 20 - main.HIT_SCORE_PENALTY)

    def test_09b_score_penalty_never_below_zero(self):
        self.put_on_player("tongue", velocity=(10, 0))
        self.step()
        self.assertEqual(self.game.score, 0)

    def test_10_one_collision_does_not_repeat(self):
        self.put_on_player("spider")
        self.step()
        for _ in range(30):
            self.step()
        self.assertEqual(self.game.lives, main.START_LIVES - 1)

    def test_10b_grace_period_blocks_second_hazard(self):
        self.put_on_player("spider")
        self.step()
        self.put_on_player("tongue")
        self.step()
        self.assertEqual(self.game.lives, main.START_LIVES - 1)

    def test_10c_item_is_not_processed_twice(self):
        self.put_on_player("dew")
        self.step()
        self.step()
        self.assertEqual(self.game.score, 10)


class TestFlare(GameTestCase):
    def test_11_flare_blocked_before_full_meter(self):
        self.game.energy = 99
        self.assertFalse(self.game.try_activate_flare())
        self.assertFalse(self.game.flare_active())

    def test_12_flare_activates_with_full_meter(self):
        self.game.energy = 100
        self.assertTrue(self.game.try_activate_flare())
        self.assertTrue(self.game.flare_active())
        self.assertEqual(self.game.energy, 0)

    def test_12b_energy_never_exceeds_100(self):
        for _ in range(10):
            self.put_on_player("berry")
            self.step()
        self.assertEqual(self.game.energy, 100)

    def test_12c_cannot_activate_twice(self):
        self.game.energy = 100
        self.game.try_activate_flare()
        self.game.energy = 100
        self.assertFalse(self.game.try_activate_flare())

    def test_13_flare_lights_arena_and_slows_hazards(self):
        normal = Item("tongue", (0, 300), (200, 0))
        slowed = Item("tongue", (0, 300), (200, 0))
        normal.update(1.0, 1.0)
        slowed.update(1.0, main.FLARE_HAZARD_SLOWDOWN)
        self.assertAlmostEqual(slowed.pos.x, normal.pos.x / 2)
        self.game.energy = 100
        self.game.try_activate_flare()
        self.game.flare_time_left = 2.5           # middle of the flare
        self.assertEqual(self.game.darkness_strength(), 0.0)
        self.game.flare_time_left = 0.0
        self.assertEqual(self.game.darkness_strength(), 1.0)

    def test_13b_hazards_move_slower_inside_a_flare(self):
        self.game.player.pos = pygame.Vector2(80, 500)
        self.game.hazard_timer = 999
        self.game.collectible_timer = 999
        far = Item("tongue", (400, 150), (300, 0))
        self.game.items.append(far)
        self.step(0.1)
        normal_distance = far.pos.x - 400
        far.pos.x = 400
        self.game.energy = 100
        self.game.try_activate_flare()
        self.step(0.1)
        flare_distance = far.pos.x - 400
        self.assertAlmostEqual(flare_distance, normal_distance * main.FLARE_HAZARD_SLOWDOWN, places=3)

    def test_14_flare_ends_after_five_seconds(self):
        self.game.energy = 100
        self.game.try_activate_flare()
        self.game.hazard_timer = 999
        self.game.collectible_timer = 999
        for _ in range(int(4.9 * 10)):
            self.step(0.1)
        self.assertTrue(self.game.flare_active())
        for _ in range(3):
            self.step(0.1)
        self.assertFalse(self.game.flare_active())


class TestDifficulty(GameTestCase):
    def test_15_levels_change_at_thresholds(self):
        expected = {0: 1, 49: 1, 50: 2, 99: 2, 100: 3, 149: 3, 150: 4, 900: 4}
        for score, level in expected.items():
            self.assertEqual(main.level_for_score(score), level, "score %d" % score)

    def test_15b_every_level_is_harder(self):
        self.assertEqual(list(main.LANTERN_RADIUS), sorted(main.LANTERN_RADIUS, reverse=True))
        self.assertEqual(list(main.HAZARD_SPEED), sorted(main.HAZARD_SPEED))
        self.assertEqual(list(main.MAX_HAZARDS), sorted(main.MAX_HAZARDS))
        self.assertEqual(list(main.HAZARD_INTERVAL), sorted(main.HAZARD_INTERVAL, reverse=True))

    def test_15c_game_level_follows_score(self):
        self.game.add_score(100)
        self.assertEqual(self.game.level, 3)

    def test_15d_hazards_never_spawn_in_players_lane(self):
        self.game.player.pos = pygame.Vector2(480, 340)
        for _ in range(200):
            self.game.items.clear()
            self.game.spawn_hazard()
            hazard = self.game.items[0]
            if hazard.kind == "spider":
                self.assertGreaterEqual(abs(hazard.pos.x - 480), main.SAFE_LANE)
            else:
                self.assertGreaterEqual(abs(hazard.pos.y - 340), main.SAFE_LANE)
            self.assertFalse(hazard.rect.colliderect(self.game.player.rect))

    def test_15e_hazard_count_is_capped(self):
        self.game.hazard_timer = 0
        self.game.collectible_timer = 999
        for _ in range(40):
            self.game.hazard_timer = 0
            self.game.update_spawning(0.01)
        self.assertLessEqual(self.game.hazard_count(), main.MAX_HAZARDS[0])


class TestEndConditions(GameTestCase):
    def test_16_timer_reaching_zero_ends_game(self):
        self.game.hazard_timer = 999
        self.game.time_left = 0.05
        self.step(0.1)
        self.assertEqual(self.game.state, "gameover")
        self.assertEqual(self.game.time_left, 0)

    def test_17_no_lives_ends_game(self):
        self.game.lives = 1
        self.put_on_player("spider")
        self.step()
        self.assertEqual(self.game.state, "gameover")

    def test_18_restart_resets_everything_but_high_score(self):
        self.game.score = 120
        self.game.lives = 1
        self.game.energy = 80
        self.game.time_left = 3
        self.game.flare_time_left = 2
        self.game.best_level = 3
        self.game.high_score = 500
        self.game.start_round()
        self.assertEqual((self.game.score, self.game.lives, self.game.energy), (0, main.START_LIVES, 0))
        self.assertEqual(self.game.time_left, main.START_TIME)
        self.assertEqual(self.game.flare_time_left, 0)
        self.assertEqual((self.game.level, self.game.best_level), (1, 1))
        self.assertEqual(self.game.hazard_count(), 0)
        self.assertEqual(self.game.state, "playing")
        self.assertEqual(self.game.high_score, 500)

    def test_18b_enter_restarts_from_game_over(self):
        self.game.state = "gameover"
        self.game.handle_key(pygame.K_RETURN)
        self.assertEqual(self.game.state, "playing")

    def test_19_high_score_persists_between_runs(self):
        self.game.score = 77
        self.game.end_round("test")
        self.assertTrue(self.game.new_best)
        second_run = Game(high_score_path=self.score_path)
        self.assertEqual(second_run.high_score, 77)

    def test_19b_bad_high_score_files_are_safe(self):
        for content in ("", "not json", '{"high_score": "abc"}', "[]", '{"other": 1}'):
            with open(self.score_path, "w", encoding="utf-8") as file:
                file.write(content)
            self.assertEqual(main.load_high_score(self.score_path), 0, content)
        self.assertEqual(main.load_high_score(os.path.join(self.temp_dir.name, "missing.json")), 0)

    def test_19c_lower_score_does_not_replace_high_score(self):
        self.game.high_score = 200
        self.game.score = 50
        self.game.end_round("test")
        self.assertEqual(self.game.high_score, 200)
        self.assertFalse(self.game.new_best)


class TestPauseAndSound(GameTestCase):
    def test_20_pause_freezes_game_and_timer(self):
        self.game.hazard_timer = 999
        item = Item("tongue", (100, 200), (200, 0))
        self.game.items.append(item)
        self.game.handle_key(pygame.K_p)
        self.assertEqual(self.game.state, "paused")
        time_before, x_before = self.game.time_left, item.pos.x
        for _ in range(60):
            self.game.update(1 / 60)
        self.assertEqual(self.game.time_left, time_before)
        self.assertEqual(item.pos.x, x_before)
        self.game.handle_key(pygame.K_ESCAPE)
        self.assertEqual(self.game.state, "playing")

    def test_21_missing_sound_files_do_not_crash(self):
        manager = SoundManager(sound_dir=os.path.join(self.temp_dir.name, "no_such_folder"))
        for name in SoundManager.NAMES:
            manager.play(name)
        silent_game = Game(high_score_path=self.score_path, sound_dir=self.temp_dir.name)
        silent_game.start_round()
        silent_game.items.clear()
        silent_game.items.append(Item("dew", silent_game.player.pos, (0, 0)))
        silent_game.update_playing(0.01, NO_KEYS)
        self.assertEqual(silent_game.score, 10)

    def test_21b_real_sound_files_load(self):
        self.assertGreaterEqual(len(SoundManager().sounds), 1)


class TestExit(unittest.TestCase):
    def test_22_application_runs_and_closes_cleanly(self):
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        result = subprocess.run([sys.executable, os.path.join(main.BASE_DIR, "main.py"), "--frames", "90"],
                                env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_22b_quit_event_stops_loop(self):
        game = Game(high_score_path=os.path.join(tempfile.gettempdir(), "fm_quit_test.json"))
        game.handle_event(pygame.event.Event(pygame.QUIT))
        self.assertFalse(game.running)


if __name__ == "__main__":
    unittest.main(verbosity=2)
