# The Lighthouse at the Edge of the World

A 20-second Blender cinematic: a lone lighthouse on a rocky island at dusk,
its beam sweeping the dark water while the camera slowly orbits. No living
beings, no music — male voiceover only.

## Production Brief (blender-director)

**Type:** environment / cinematic shot
**Target:** cinematic video (MP4, 1280x720, 24fps)
**Style:** stylised, dusk mood
**Poly budget:** procedural primitives only (~15k tris total — ocean grid,
displaced island, stacked lighthouse cylinders)
**Texture budget:** none (all procedural — Noise/Clouds textures, no image maps)
**Export:** MP4 video (PNG sequence + ffmpeg), not FBX/GLTF
**Animation:** camera orbit (~70°), beam rig 360° turn, ocean Wave modifier +
animated noise bump, rotating spotlight
**Engine:** Eevee Next (Blender 4.2 LTS), AgX, bloom + GTAO

### Active Skills
1. `blender-director` — orchestration, brief, validation loop
2. `blender-environment-artist` — island / ocean / rocks
3. `blender-lighting` — dusk sun, lamp, beam spotlights
4. `blender-camera-cinematography` — 35mm orbit rig, Track-To
5. `blender-rendering` — Eevee settings, AgX, stills QC

### Pipeline Phases
- [x] Reference & Planning (brief above)
- [x] Blockout & Silhouette (procedural scene script)
- [x] Modeling (build_scene.py)
- [x] Materials (procedural Principled, emissive lamp/beam)
- [x] Lighting (dusk sun + lamp + spots)
- [x] Camera (orbit rig + Track-To)
- [ ] Stills validation (3 frames inspected before full render)
- [ ] Full render + voiceover mux + release

### Execution note
No Blender MCP is available on the build machine, so the director's MCP
execution is replaced by a headless `blender -b --python build_scene.py`
run on GitHub Actions (same "build on GitHub" pattern as the 3D Kaz videos).
Validation happens on rendered stills, per the director's compare loop.

## How to render

Dispatch the workflow with `mode: stills` first (renders frames 1 / 264 / 528).
Inspect the stills, then dispatch `mode: full` — it renders all 528 frames,
generates the voiceover with edge-tts (male, `en-US-GuyNeural`), muxes with
ffmpeg (`-shortest` trims the 22s of video to the voice length) and creates
release v1.0.

## Narration

> At the edge of the world, one light never sleeps.
> Every night, its beam sweeps the dark water, searching for ships that never come.
> Storms have tried to break it for a hundred years.
> But the light keeps turning — patient, stubborn, and alone.
> Some lights do not guide ships. They simply refuse to go out.

## Files

- `build_scene.py` — whole scene + animation + render (Blender 4.2, Eevee)
- `beats.txt` — narration lines
- `gen_voice.py` — edge-tts voiceover (male)
- `render.yml` — GitHub Actions workflow (dispatch: stills | full)
