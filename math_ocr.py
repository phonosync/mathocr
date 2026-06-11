#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = [
#   "pix2text",
#   "anthropic",
#   "pillow",
# ]
# ///
"""math-ocr: Convert images of math (printed or handwritten) to LaTeX.

Engines:
  local   pix2text (MFR model) - offline, free, good on printed equations
  claude  Claude vision API    - best for handwriting; needs ANTHROPIC_API_KEY

Usage:
  math-ocr equation.png                 # local engine, LaTeX to stdout
  math-ocr equation.png -c              # also copy LaTeX to clipboard (macOS)
  math-ocr notes.jpg --engine claude    # handwritten -> use Claude
  math-ocr --paste                      # read image from clipboard (e.g. after
                                        # Cmd+Ctrl+Shift+4 screenshot)
  math-ocr *.png --engine claude --full # full transcription (text + math)
"""

import argparse
import os
import subprocess
import sys

CLAUDE_MODEL = os.environ.get("MATH_OCR_CLAUDE_MODEL", "claude-sonnet-4-6")

EQUATION_PROMPT = (
    "Transcribe the mathematical expression in this image to LaTeX. "
    "Output ONLY the LaTeX code, with no surrounding $ delimiters, "
    "no markdown fences, and no explanation. If the image contains "
    "multiple equations, separate them with newlines (use \\\\ inside "
    "aligned environments where appropriate)."
)

FULL_PAGE_PROMPT = (
    "Transcribe everything in this image to Markdown. Render all "
    "mathematics as LaTeX: inline math in $...$, display math in $$...$$. "
    "Preserve the document structure (headings, lists, tables). "
    "Output ONLY the Markdown, no explanation."
)


def die(msg: str, code: int = 1):
    print(f"math-ocr: error: {msg}", file=sys.stderr)
    sys.exit(code)


def load_image(path: str):
    from PIL import Image

    try:
        return Image.open(path).convert("RGB")
    except FileNotFoundError:
        die(f"file not found: {path}")
    except Exception as e:
        die(f"could not read image {path}: {e}")


def image_from_clipboard():
    from PIL import ImageGrab

    img = ImageGrab.grabclipboard()
    if img is None:
        die("no image in clipboard (take a screenshot with Cmd+Ctrl+Shift+4 first)")
    if isinstance(img, list):  # clipboard holds file path(s)
        return load_image(img[0])
    return img.convert("RGB")


def copy_to_clipboard(text: str):
    if sys.platform == "darwin":
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
    else:
        try:
            subprocess.run(["xclip", "-selection", "clipboard"],
                           input=text.encode(), check=True)
        except FileNotFoundError:
            die("clipboard copy needs pbcopy (macOS) or xclip (Linux)")


# ---------------------------------------------------------------- engines

_P2T_MODEL = None  # lazy singleton: model load takes a few seconds


def ocr_local(img) -> str:
    global _P2T_MODEL
    if _P2T_MODEL is None:
        try:
            from pix2text import Pix2Text
        except ImportError:
            die("pix2text is not installed. Run: pip install pix2text")
        _P2T_MODEL = Pix2Text.from_config()
    return _P2T_MODEL.recognize_formula(img).strip()


def ocr_claude(img, full_page: bool = False) -> str:
    import base64
    import io

    try:
        import anthropic
    except ImportError:
        die("anthropic SDK not installed. Run: pip install anthropic")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        die("ANTHROPIC_API_KEY is not set (export ANTHROPIC_API_KEY=sk-ant-...)")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.standard_b64encode(buf.getvalue()).decode()

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": "image/png",
                            "data": b64}},
                {"type": "text",
                 "text": FULL_PAGE_PROMPT if full_page else EQUATION_PROMPT},
            ],
        }],
    )
    text = msg.content[0].text.strip()
    # strip accidental markdown fences
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:]).rsplit("```", 1)[0].strip()
    return text


# ------------------------------------------------------------------ main

def main():
    p = argparse.ArgumentParser(
        prog="math-ocr",
        description="Convert images of math to LaTeX (Mathpix-style).",
        epilog="Default engine is 'local' (pix2text). Use --engine claude "
               "for handwriting or when the local result is wrong.")
    p.add_argument("images", nargs="*", help="image file(s) (png/jpg)")
    p.add_argument("--paste", action="store_true",
                   help="read the image from the clipboard")
    p.add_argument("--engine", choices=["local", "claude"], default="local",
                   help="OCR engine (default: local)")
    p.add_argument("--full", action="store_true",
                   help="full-page transcription to Markdown (claude engine only)")
    p.add_argument("-c", "--clipboard", action="store_true",
                   help="copy the result to the clipboard")
    p.add_argument("-d", "--delimiters", choices=["none", "inline", "display"],
                   default="none",
                   help="wrap result in $...$ or $$...$$ (default: none)")
    args = p.parse_args()

    if args.full and args.engine != "claude":
        die("--full requires --engine claude")
    if not args.images and not args.paste:
        p.print_help()
        sys.exit(2)

    images = []
    if args.paste:
        images.append(("clipboard", image_from_clipboard()))
    for path in args.images:
        images.append((path, load_image(path)))

    results = []
    for name, img in images:
        if args.engine == "claude":
            latex = ocr_claude(img, full_page=args.full)
        else:
            latex = ocr_local(img)
        if args.delimiters == "inline":
            latex = f"${latex}$"
        elif args.delimiters == "display":
            latex = f"$$\n{latex}\n$$"
        results.append(latex)
        if len(images) > 1:
            print(f"% --- {name}")
        print(latex)

    if args.clipboard:
        copy_to_clipboard("\n\n".join(results))
        print("(copied to clipboard)", file=sys.stderr)


if __name__ == "__main__":
    main()
