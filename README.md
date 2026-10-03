# Rgirljk - original Blender character studio

An original, procedurally authored 3D character study made with headless Blender and displayed in a Three.js WebGL viewer. The supplied photograph is used for visual comparison only. No existing character meshes, hair assets, texture scans, HDRIs, clothing models or photo-projected surfaces are used.

## Current state

This is a work in progress, not a claim of photographic identity or AAA quality. The authoritative visual-review state is `preview/status.json`. Only actual completed build, preview and visual-review cycles are counted. The requested 20,000 iterations must not be confused with the much smaller actual completed count. Scores are subjective estimates of resemblance, not objective measurements.

## Build

Tested in the user's Colab dev instance with Blender 4.2.3, Node.js 22 and Python 3. All geometry and generated fabric textures are rebuilt from `src/build_character.py`.

```bash
npm ci
npm run build:viewer
BLENDER_BIN=/path/to/blender ./src/render.sh --revision 4 --samples 48 --size 1200 --views front,face,threequarter,back,side
npm run dev
```

The development preview runs on port 8867. Drag to orbit, scroll or pinch to zoom, and use the front, three-quarter, back, face, rotation and wireframe controls.

`src/review.py` records a completed visual review. Do not invoke it for a render that has not actually been inspected. `tests/browser_qa.mjs` checks desktop/mobile loading, horizontal overflow, controls and browser errors. `build/browser_qa.json` records the results. A headless software-WebGL test is not a physical-phone performance benchmark.

## Files and provenance

- `src/build_character.py`: original mesh, face, eyes, hair, clothing, hands, socks, footwear, camera and lighting code.
- `src/viewer.js`: interactive renderer; the lighting environment is generated from original geometry, not an imported HDRI.
- `preview/index.html`: live comparison, latest renders, scores, paths and review history.
- `preview/gpt6_astra_pro_mcp_blender_rgirljk.glb`: portable character-only model.
- `preview/gpt6_astra_pro_mcp_blender_rgirljk.blend`: editable Blender scene, including editable hair curves and studio lights.
- `Agents.md`: continuation context, environment details, actual progress and remaining issues.

Third-party software libraries are used as development tools, not as sources of character assets. The reference photograph remains user-supplied; no ownership claim is made over it, and it is not embedded in the model.
