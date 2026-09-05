# Wondernight

My first video game! 🎮

When you run it, a window opens with a black background, and the word
**Wondernight** flashes in the middle of the screen, switching between
blue and green.

## How to run it

1. Create a virtual environment:
   ```
   python3 -m venv venv
   ```
2. Turn it on:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
3. Install the game's requirements:
   ```
   pip install -r requirements.txt
   ```
4. Run the game:
   ```
   python wondernight.py
   ```
5. Press **Esc** or close the window to quit.

## Wondernight 3D

A full 3D rebuild of the same game using the [Ursina](https://www.ursinaengine.org/) engine
(Python, built on Panda3D). Same map, same race-and-battle rules, same
dragon/whale/bird/werewolf forms and princess companion - but rendered
in a real 3D world with a perspective camera instead of 2D sprites.

Characters, Dark Knights, the pirate ship, and the princess are voxel-style
character art (in `assets3d/`) shown as billboards that always face the
camera - since no actual 3D model files exist for them, this is the
closest practical stand-in for "real 3D models." The whale
transformation has no source art, so it's still a simple primitive shape.

### How to run it

1. Install the extra requirement (on top of the normal ones):
   ```
   pip install -r requirements-3d.txt
   ```
2. Run it:
   ```
   python wondernight3d.py
   ```
3. Controls are the same as the 2D game: arrow keys to move, I to
   attack, D/W/B/R to transform (dragon/whale/bird/werewolf), Esc to quit.
