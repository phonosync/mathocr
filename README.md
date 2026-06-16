# math-ocr

Mathpix-style CLI: image of an equation in, LaTeX out. No training needed — it uses the pretrained **pix2text** model locally, with optional escalation to the **Claude API** for handwriting or hard cases. pix2text ships pretrained on millions of rendered LaTeX equations, and Claude handles math transcription out of the box.

## Install (macOS, with uv)

The script carries PEP 723 inline metadata, so `uv` handles everything — no venv, no pip:

``` bash
brew install uv        # if not already installed
chmod +x math_ocr.py
./math_ocr.py equation.png        # uv resolves deps on first run
```

Or explicitly: `uv run math_ocr.py equation.png`.

To get a `math-ocr` command anywhere, add to `~/.zshrc`:

``` bash
alias math-ocr="$HOME/projects/mathocr/math_ocr.py"
```

First run creates a cached environment and downloads the pix2text model weights (\~100 MB); after that it starts fast and works offline.

For the Claude engine, set your key once (e.g. in `~/.zshrc`):

``` bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

``` bash
math-ocr equation.png              # printed math, offline
math-ocr equation.png -c           # + copy LaTeX to clipboard
math-ocr notes.jpg --engine claude # handwritten math
math-ocr --paste -c                # clipboard image -> clipboard LaTeX
math-ocr page.png --engine claude --full   # full page -> Markdown + LaTeX
math-ocr eq.png -d display         # wrap in $$...$$
```

### Mathpix-Snip-like workflow

1.  `Cmd+Ctrl+Shift+4` — screenshot a region **to the clipboard**
2.  `math-ocr --paste -c`
3.  Paste the LaTeX wherever you need it

### Watch mode (interactive loop)

Keep the tool running and process multiple screenshots without restarting:

``` bash
math-ocr --watch --engine claude -c
```

1.  `Cmd+Ctrl+Shift+4` — screenshot a region to the clipboard
2.  Press **Enter** — LaTeX is printed (and copied to clipboard with `-c`)
3.  Repeat from step 1; **Ctrl+C** to quit

This avoids re-running `uv` and reloading the model on every screenshot. All other flags (`--engine`, `--full`, `-c`, `-d`) work normally inside the loop.

Alias for `~/.zshrc`:

``` bash
alias snip2tex="$HOME/projects/mathocr/math_ocr.py --paste -c --watch"
```

## Engine guidance

|                       | local (pix2text) | claude                            |
|----------------------|------------------|---------------------------------|
| Printed equations     | very good        | excellent                         |
| Handwriting           | weak             | very good                         |
| Full pages (`--full`) | –                | yes                               |
| Cost / privacy        | free, offline    | per-request, image leaves machine |

Default model for the Claude engine is `claude-sonnet-4-6`; override with `MATH_OCR_CLAUDE_MODEL`.

## Dependencies

| Package | Role | License | Link |
|---------|------|---------|------|
| [pix2text](https://github.com/breezedeus/pix2text) | Local OCR engine (MFR model) for printed equations | MIT | https://github.com/breezedeus/pix2text |
| [anthropic](https://github.com/anthropics/anthropic-sdk-python) | Claude API client for the cloud engine | MIT | https://github.com/anthropics/anthropic-sdk-python |
| [Pillow](https://python-pillow.org) | Image loading and clipboard access | MIT-CMU (MIT-compatible) | https://pillow.readthedocs.io |

All dependencies are MIT-licensed, imposing no restrictions beyond attribution. This project is released under the [MIT License](LICENSE).

### pix2text

[pix2text](https://github.com/breezedeus/pix2text) by [breezedeus](https://github.com/breezedeus) is a Python library for recognizing mixed text and math in images. It uses the **MFR** (Math Formula Recognition) model, pretrained on millions of rendered LaTeX equations. On first run it downloads ~100 MB of model weights to a local cache; all subsequent inference is fully offline.