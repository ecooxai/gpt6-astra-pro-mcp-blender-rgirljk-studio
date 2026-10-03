# Agent handoff - Rgirljk Blender studio

## Task and constraints
Reconstruct the user-supplied reference as an original 3D character using headless Blender in mcp_colabdev. Do not import existing meshes, textures, character assets or HDRIs. Do not use the photo as a texture or a flat plane. Inspect the reference and rendered previews visually; no programmatic image analysis of the reference. Keep a live auto-refreshing web preview, Git history, actual iteration records and honest quality scores. The requested target is over 95/100 and 20,000 iterations; neither should be asserted without real evidence.

## Workspace
Project: /home/dev/project/3d/gpt6_astra_pro_mcp_blender_rgirljk_studio
Build: /build/gpt6_astra_pro_mcp_blender_rgirljk_studio (project `build` is a symlink)
Branch: gpt6-astra-pro-mcp/blender-rgirljk-studio
Working Blender: /home/dev/.local/opt/blender-4.2.3-linux-x64/blender
The system Blender executable in .local/sysroot is broken because its Python resources are missing. Use the portable 4.2.3 build above.

## Live services
Node static preview on 0.0.0.0:8867; source src/server.mjs; logs/server.log and logs/server.pid.
Cloudflared logs/tunnel.log contains the current quick-tunnel URL. Quick-tunnel URLs can change after a restart. Services must be detached with subprocess.Popen(start_new_session=True, redirected stdio), not merely shell background jobs.
Colab terminal records are persistent. Prefer reusing terminals with webterm write/read; indiscriminate webterm run eventually reaches the shared 32-session limit. Never stop other projects' terminals.

## Current progress
Revision 1: completed and visually inspected front/face, 48/100. Major defects were scalp gap, sock intersections, angular face, stiff ponytails and neckline edges.
Revision 2: completed and visually inspected front/face/back/side, 62/100. Main holes/intersections fixed; remaining neck join, narrow face, stiff hair, floating bag straps and shoe saddle edges.
Revision 3: under construction at handoff-file creation. Check logs/build_r03.log and preview/*_r03.png. It adds a broader, less elongated head, refined hairline, continuous neck attachment, equal-length IK leg joints, a relaxed torso lean and fitted leather saddle straps.
Always read preview/status.json for the authoritative latest reviewed revision and actual iteration count. Do not increment the count for retries, compilation errors, random parameter sweeps or renders not visually inspected.

## Source and output
src/build_character.py creates the entire scene from scratch. It never loads the reference image. Original plaid and tie patterns are generated mathematically and embedded in the GLB. Editable hair curves are saved in the Blender scene before curve conversion for glTF export. The GLB excludes the studio, floor, lights and camera.
src/render.sh is the headless entry point. src/review.py records visual-review state. src/viewer.js is bundled to preview/viewer.js via npm run build:viewer.
The reference is reference/rgirljk.png and a comparison-only preview copy; neither should be embedded in the model. No other workspace assets were reused.

## QA and next work
Inspect every new model in front, face, three-quarter, back and side views. Pay particular attention to face resemblance, neck silhouette, natural hair strands, cloth contact, thumb/finger joins, shoe surfaces and mesh intersections. Leg length metadata is in build/geometry_metrics_rNN.json.
Run tests/browser_qa.mjs with the installed Chromium executable. The initial headless-shell path was missing; the installed browser is /home/dev/.local/share/chromium/chromium-1243/chrome-linux64/chrome. Desktop/mobile screenshots are under preview/browser_*.png. An earlier mobile element screenshot timed out while rendering; use the updated full-page screenshot flow and inspect build/browser_qa.json for real outcomes.
WebGL character self-shadowing produced severe fine-hair artifacts; receiveShadow is disabled on character meshes while the floor receives cast shadows. An original procedural light-room reflection environment was added. Visually verify this fix rather than assuming it works.
