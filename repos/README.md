# Reference repos

Code-driven animation and video projects kept for reference, added as Git
submodules: this repo stores only a link to each upstream repo and the commit it
points to, so it stays small. After cloning VideoEdit, fetch their contents from
the repo root with:

```bash
bash scripts/clone_repos.sh
```

The script checks for Node.js 22+, git and ffmpeg, then fetches each submodule
shallowly (`--depth 1`). To move a submodule to its latest upstream commit, run
`git submodule update --remote repos/<name>` and commit the change. HyperFrames is cloned with `GIT_LFS_SKIP_SMUDGE=1`, so its heavy
LFS test videos are not downloaded.

| Repo | What it is |
|---|---|
| [JohnHeibel/PDoomVideo](https://github.com/JohnHeibel/PDoomVideo) | Source for the "I'm Upping My P(doom)" music video, animated in p5.js by Claude Opus 5.5 |
| [JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) | Starter kit (p5.js + p5.brush, `ANIMATION_GUIDE.md`) for having Claude storyboard and render character animation to MP4 |
| [buildwithhanif/claude-animation-skill](https://github.com/buildwithhanif/claude-animation-skill) | Claude skill for hand-drawn-looking 2D animation in code (Node + ffmpeg, no browser/GPU), with synthesized sound |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | HeyGen's framework for writing videos as HTML and rendering them to MP4, built for AI agents |
| [WinterArc21/Battle-of-Austerlitz-Film](https://github.com/WinterArc21/Battle-of-Austerlitz-Film) | Five-minute historical film rendered entirely in WebGL code, with synthesized sound, generated narration and subtitles |
| [guanmo-ai/awesome-ai-motion](https://github.com/guanmo-ai/awesome-ai-motion) | Curated gallery of 1,700+ AI-made motion works, with their prompts |
| [athemeroy/awesome-opus-5-5-videos](https://github.com/athemeroy/awesome-opus-5-5-videos) | Curated list and analysis of videos and reusable projects made with Claude 5.5 models |
