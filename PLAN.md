# Phase 5: Debug & Polish

Refine the game feel, smooth out transitions, and add visual feedback for actions.

## Objectives

1. **Smooth Camera**: Use Panda3D's task system to interpolate camera movement between tiles.
2. **Entity Animations**: Basic "hop" animation when moving to make the grid transition feel alive.
3. **Message Log**: HUD-integrated text log for combat and item events.
4. **AI Refinement**: Enemies will avoid stacking and prioritize better pathing.
5. **Death Screen**: Clearer visual feedback when the player is defeated.

## Next Steps

- Implement `smooth_move` Task for the camera.
- Implement `Entity.animate_move` for bouncy grid movement.
- Update `GameHUD` with a message log area.
- Refine AI for diagonal checks and occupancy.
