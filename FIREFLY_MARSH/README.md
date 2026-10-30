# FIREFLY MARSH

A 2D arcade game made with Python and Pygame for **Multimedia Systems Lab Test 2**.

You are a tiny firefly in a pitch-dark marsh. Only a small circle of light around you is visible. Collect glowing treasures, dodge spiders and frog tongues, and use your **Flare** to light up the whole night.

## 1. Objective

Score as many points as you can before the night ends. The game ends when you lose all 3 lives or the 90-second night timer reaches zero.

## 2. System requirements

- Windows, macOS or Linux
- Python 3.9 or newer
- Pygame 2.5 or newer (the only dependency)
- A screen of at least 960 x 640 pixels. Speakers are optional; the game runs without sound.

## 3. Installation

A virtual environment keeps the libraries for this project separate (recommended):

```bash
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (macOS / Linux)
pip install -r requirements.txt
```

Without a virtual environment, just run `pip install -r requirements.txt`.

## 4. How to run

```bash
python main.py
```

The sound files are already in `assets/sounds/`. To re-create them, run `python make_sounds.py`.

## 5. Controls

| Key | Action |
| --- | --- |
| W / A / S / D or Arrow keys | Move the firefly |
| SPACE | Use the Flare (only when the meter is 100%) |
| P or ESC | Pause / resume |
| ENTER | Start the game / play again |
| ESC | Back to the menu from the Instructions or Game Over screen |
| Mouse | Click the on-screen buttons |

## 6. Customization: the FLARE (Blackout Marsh)

This is my individual customization. It changes both the **look** and the **rules** of the game.

1. **Blackout.** The marsh is covered by a dark layer. Only a lantern circle around the firefly is visible. Treasures and hazard eyes glow faintly so the game stays fair.
2. **Shrinking lantern.** As the level goes up, the lantern circle gets smaller (200, 172, 146, 122 pixels).
3. **Flare meter.** Collecting items fills the meter: Dew Drop +20%, Glow Berry +40%. The meter never goes above 100%.
4. **Using the Flare.** At 100%, press SPACE. The meter resets to 0 and the Flare lasts **5 seconds**:
   - The darkness fades away and the whole marsh is lit.
   - **Every hazard moves at half speed.**
   - You cannot start a second Flare while one is running.
5. The HUD shows `FLARE 60%`, then `FLARE READY - PRESS SPACE`, then `FLARE ACTIVE 3.5s`.

The Flare uses only a few variables (`energy`, `flare_time_left`) and `if` statements, see `try_activate_flare()` and `update_playing()` in `main.py`.

## 7. Collectibles

| Item | Looks like | Effect |
| --- | --- | --- |
| Dew Drop | Teal bubble | +10 points, +20% Flare |
| Glow Berry (rare) | Golden berries | +30 points, +40% Flare |
| Dawn Petal | Lavender flower | +5 seconds (timer is capped at 2:00) |

Collectibles drift slowly around the marsh, bounce off the walls, blink when they are about to vanish (after 10 seconds), and disappear as soon as you pick them up.

## 8. Hazards

| Hazard | Behaviour | Effect |
| --- | --- | --- |
| Spider | Drops from the top on a thread and sways left and right | -1 life, -5 points |
| Frog Tongue | Shoots across the marsh from the left or right edge | -1 life, -5 points |

After a hit the hazard is removed and the firefly blinks and is safe for 1.5 seconds, so one touch can never take more than one life.

## 9. Scoring

- Dew Drop +10, Glow Berry +30, Dawn Petal +0 (time bonus instead)
- Hazard hit: -5 points (the score never goes below 0) and -1 life
- Start: 3 lives and 90 seconds
- The best score is saved in `highscore.json` and survives restarting the program. A missing or broken file is treated as a best score of 0.

## 10. Adaptive difficulty

| Level | Score | Hazard speed | Hazard every | Max hazards | Lantern radius |
| --- | --- | --- | --- | --- | --- |
| 1 | 0 - 49 | 150 | 2.4 s | 2 | 200 |
| 2 | 50 - 99 | 185 | 1.9 s | 3 | 172 |
| 3 | 100 - 149 | 220 | 1.5 s | 4 | 146 |
| 4 | 150+ | 255 | 1.2 s | 5 | 122 |

Speeds are in pixels per second. Spiders use the value shown and frog tongues move 1.5 times faster (a little random variation is added to each hazard).

The level is worked out by `level_for_score(score)` every time the score changes. For fairness, hazards never spawn in the player's current row or column (`SAFE_LANE`), and new treasures never appear on top of the player.

## 11. Game states, game over and restart

The game has five states: `menu`, `instructions`, `playing`, `paused`, `gameover`.

- **Pause:** `update()` returns immediately while paused, so objects, animation and the timer all freeze.
- **Game over:** lives reach 0, or time reaches 0. The screen shows the final score, best score, highest level reached, **Play Again** and **Main Menu** buttons.
- **Restart:** `reset_round()` sets score, lives, timer, Flare, level, lantern and all objects back to the start values. It does not touch the saved best score. No need to close the program.

## 12. Algorithm

```bash
start Pygame, load sounds, show the menu
loop every frame:
    dt = time since last frame (in seconds, max 0.05)
    handle events (quit, key presses, mouse clicks on buttons)
    if state is "playing":
        read keys -> direction
        timer = timer - dt
        move player: position += direction * speed * dt, then keep inside the arena
        move collectibles; move hazards (half speed if Flare is active)
        spawn new collectibles / hazards when their timers run out
        check collisions
        update the level from the score and shrink the lantern if needed
        if lives == 0 or timer == 0: game over (save best score)
    draw the screen for the current state
```

Because movement uses `speed * dt`, the game runs at the same speed on slow and fast computers.

## 13. Collision-detection logic

Every object has a rectangle (`pygame.Rect`) around its centre. The player's box is 16 x 16 pixels, smaller than the drawing, so near-misses feel fair.

```bash
for each item in the arena:
    if item.rect overlaps player.rect:          # Rect.colliderect()
        if item is a hazard:
            if the player is not in the 1.5 s grace time:
                lives = lives - 1, score = max(0, score - 5), start grace time
                remove the hazard
        else:
            add score / Flare energy / time, then remove the item
```

Removing the item as soon as it touches the player means it can never be counted twice.

## 14. Multimedia elements

- **Graphics:** firefly sprite, collectible and hazard sprites drawn with Pygame shapes, night-sky background with moon, stars, reeds, lily pads and water.
- **Animation:** two-frame wing flapping, pulsing collectibles, swaying spiders, drifting background fireflies, water ripples, particle bursts, floating `+10` text, light trail, lantern flicker, Flare fade-in/out, damage flash.
- **Sound (self-made .wav files):** dew, berry, petal, hit, Flare, game over, and a looping ambient background.
- **Interface:** title screen, instructions, HUD (score, lives, Flare meter, timer, level), pause and game-over screens, buttons with hover feedback.

## 15. Project structure

```bash
FIREFLY_MARSH/
    main.py                  the whole game
    make_sounds.py           creates the .wav files (standard library only)
    tests.py                 40 automatic checks (python tests.py)
    requirements.txt
    README.md
    assets/sounds/           dew, berry, petal, hit, flare, gameover, ambient (.wav)
    screenshots/             start_screen, instructions, gameplay, flare_active, paused, game_over (.png)
    highscore.json           created automatically after the first game
```

If a sound file is missing, the game still runs, just without that sound.

## 16. Screenshots

All are in the `screenshots/` folder:

- `start_screen.png` - main menu
- `instructions.png` - how to play
- `gameplay.png` - normal play, dark marsh with the lantern circle
- `flare_active.png` - Flare active, whole marsh lit
- `paused.png` - pause screen
- `game_over.png` - game-over screen

They show the real game screens. To take your own, run `python main.py` and use your operating system's screenshot tool.

## 17. Tests

```bash
python tests.py
```

The 40 checks run without a window or speakers. They cover launch, buttons, movement and boundaries, item scoring, time bonus and cap, hazard hits, grace time, Flare rules (blocked below 100%, five seconds, half-speed hazards), difficulty levels, game over, restart, saved best score (including broken files), pause, missing sounds and clean exit.
