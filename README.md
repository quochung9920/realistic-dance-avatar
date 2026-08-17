# Realistic Dance Avatar

MVP pipeline for turning a dance reference video into reusable body-motion data for a photorealistic 3D character.

The project is intentionally split into two stages:

1. **Video to motion** - runs locally in Python using MediaPipe Pose Landmarker.
2. **Motion to photorealistic character** - runs in Blender on your own rigged human character.

This separation keeps the motion extractor reusable when you later replace the MVP pose solver with a higher-quality mocap provider.


## Current development focus: character first

The project now supports a **Character Viewer** workflow in addition to the original motion-extraction MVP.

### Phase 1 goal

Create and review a photorealistic 3D human character **before** any dance, rigging, or livestream work.

### Web character viewer

Start the app and open the **Character Viewer** tab. You can:

- load the project default model from `models/characters/main_character.glb`;
- upload a `.glb`, `.gltf`, `.fbx`, `.obj`, `.stl`, or `.ply` file and preview it in the browser;
- review the default character blueprint from `config/character_blueprint.json`.

### Character asset location

Put your approved web-viewable model here:

```text
models/characters/main_character.glb
```

For production, keep a higher-fidelity source model as `.blend` or `.fbx` beside it when possible.

## What works in v0.1

- Upload a dance reference video.
- Optionally upload a clean song/audio file.
- Extract one human pose in video mode.
- Save normalized landmarks and world landmarks for every frame.
- Smooth motion with an exponential moving average.
- Derive pelvis, chest, neck, head, wrists, ankles and other useful joints.
- Generate a pose-overlay preview video.
- Keep the supplied music synchronized with the preview.
- Export `motion.json` and a job ZIP.
- Drive a generic humanoid, Mixamo-style, or Unreal-style rig in Blender with IK targets.
- Render vertically at 1080x1920 from Blender.
- Mux the final render with music using FFmpeg.

## Important v0.1 limitation

This is an **MVP monocular pose pipeline**, not a studio-grade motion-capture solver. MediaPipe world landmarks are excellent for a fast local baseline, but a single camera cannot perfectly recover body twist, floor contact, occluded limbs, hand/finger detail, cloth dynamics, or true global movement through 3D space.

For production-quality dance, keep this repository and replace only the motion-extractor adapter with a stronger solver or a mocap service. The character/render side can stay the same.

## Recommended machine

For motion extraction:

- Windows 10/11, macOS, or modern Linux.
- Python **3.10, 3.11, or 3.12**. Python 3.12 is recommended.
- FFmpeg available on `PATH`.

For 3D rendering:

- Blender 4.5 LTS or newer is recommended for the project workflow.
- A discrete NVIDIA/AMD GPU is strongly recommended for photorealistic rendering.
- A rigged humanoid `.blend` file.

## Windows setup

### 1. Install Python 3.12

Install 64-bit Python 3.12 and make sure the `py` launcher is installed.

Check:

```powershell
py -3.12 --version
```

### 2. Install FFmpeg

Install FFmpeg and make sure these commands work in a new PowerShell window:

```powershell
ffmpeg -version
ffprobe -version
```

### 3. Create the environment

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```

The script creates `.venv`, installs the Python package, and downloads the official MediaPipe Pose Landmarker model into `models/`.

### 4. Start the local UI

```bat
scripts\run_windows.bat
```

The browser opens the local interface. Upload:

- **Dance reference video**: the dancer should remain fully visible when possible.
- **Optional replacement music**: use this when the clean track is separate from the reference video.

Click **Extract motion**.

Outputs are written to:

```text
output/<job-id>/
  motion.json
  pose_preview.mp4
  manifest.json
  dance_motion_bundle.zip
```

## macOS / Linux setup

Install Python 3.12 and FFmpeg, then:

```bash
./scripts/setup_macos_linux.sh
./scripts/run_macos_linux.sh
```

## CLI usage

Download the pose model:

```bash
dance-avatar download-model
```

Extract motion:

```bash
dance-avatar extract \
  --video input/dance.mp4 \
  --audio input/song.wav \
  --output output
```

For a quick test, process only the first 300 frames:

```bash
dance-avatar extract --video input/dance.mp4 --max-frames 300
```

## Blender retargeting

### Character preparation

Use a **rigged photorealistic human**. The repository does not redistribute a MetaHuman, Character Creator character, or any third-party human asset.

Your character needs a humanoid armature. Three starter bone maps are included:

```text
config/rig_generic.json
config/rig_mixamo.json
config/rig_unreal_style.json
```

If your bone names are different, copy one file and change only the names.

### Run Blender retargeting

Example with a Mixamo-style rig:

```bash
blender character.blend --background \
  --python blender/retarget_motion.py -- \
  --motion output/JOB_ID/motion.json \
  --rig-map config/rig_mixamo.json \
  --save output/JOB_ID/animated.blend
```

To render immediately using the camera and lighting already stored in the `.blend` scene:

```bash
blender character.blend --background \
  --python blender/retarget_motion.py -- \
  --motion output/JOB_ID/motion.json \
  --rig-map config/rig_mixamo.json \
  --save output/JOB_ID/animated.blend \
  --render output/JOB_ID/avatar_render.mp4
```

The script creates IK targets for wrists and ankles, applies a hip-orientation track, sets the animation frame range, and configures a vertical 1080x1920 render when `--render` is used.

### Add the final music

```bash
dance-avatar finalize \
  --video output/JOB_ID/avatar_render.mp4 \
  --audio input/song.wav \
  --output output/JOB_ID/tiktok_final.mp4
```

If the song starts later than the animation:

```bash
dance-avatar finalize \
  --video output/JOB_ID/avatar_render.mp4 \
  --audio input/song.wav \
  --audio-offset 0.18 \
  --output output/JOB_ID/tiktok_final.mp4
```

## Making the person look real

The motion extractor does **not** determine visual realism. Photorealism comes from the character and render scene:

- high-quality skin shader and textures;
- realistic eyes and teeth;
- strand/groom hair;
- body proportions and corrective shapes;
- clothing with believable materials and secondary motion;
- good lighting, contact shadows and camera exposure;
- final motion cleanup, especially feet, hands and occluded frames.

A practical production path is:

```text
Reference dance video
        -> this repository: motion extraction
        -> Blender: retarget + cleanup
        -> photorealistic rigged human
        -> Blender/Unreal: lighting + render
        -> FFmpeg: music + 9:16 final file
        -> TikTok
```

## MetaHuman path

The repository can be used as the **motion source** for a MetaHuman pipeline, but MetaHuman body retargeting is best finished in Unreal Engine using Epic's IK Retargeter workflow. The included `rig_unreal_style.json` is a starter map for Unreal-style humanoid naming; it should not be treated as a guarantee that every MetaHuman/UE export uses identical bone names.

## Input video tips

For the cleanest motion extraction:

- keep the whole body, especially both feet, inside the frame;
- avoid heavy motion blur;
- use a stable camera when possible;
- avoid long occlusions behind objects or other dancers;
- use the highest-quality source you legally control;
- prefer a single continuous take instead of frequent cuts.

## Project structure

```text
realistic_dance_avatar/
  assets.py       model download
  pose.py         MediaPipe video pose extraction
  motion.py       smoothing and derived joints
  pipeline.py     end-to-end extraction job
  finalize.py     final FFmpeg mux
  ui.py           local Gradio interface
  cli.py          command-line interface
blender/
  retarget_motion.py
config/
  rig_generic.json
  rig_mixamo.json
  rig_unreal_style.json
scripts/
tests/
```

## Tests

```bash
pytest -q
```

GitHub Actions runs tests on Python 3.10, 3.11 and 3.12.

## Safety and rights

Use dance videos, music, faces, and character likenesses that you own or have permission to use. If you create a realistic digital double of a real person, obtain their consent and follow the platform rules that apply to synthetic or AI-generated media.

## License

MIT for the source code in this repository. Third-party models, Blender assets, MetaHuman assets, music, reference videos, and character content retain their own licenses.
