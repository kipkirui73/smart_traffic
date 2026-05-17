# modules/plate_reader/reader.py
"""
Number Plate Reader
===================
Extracts the region of a detected vehicle from a frame,
then runs OCR (EasyOCR) to read the licence plate text.

Usage example (in main.py):
    from modules.plate_reader.reader import read_plate
    plate_text = read_plate(frame, vehicle["box"])
"""

import cv2
import re
import logging
import numpy as np

logger = logging.getLogger(__name__)

# ── lazy-load the OCR reader so startup isn't slow ─────────────────────────
_reader = None


def _get_reader():
    """Initialise EasyOCR once; reuse on every call."""
    global _reader
    if _reader is None:
        import easyocr
        logger.info("Loading EasyOCR model (first run takes ~30 s)…")
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        logger.info("EasyOCR ready.")
    return _reader


# ── main public function ─────────────────────────────────────────────────────

def read_plate(frame, box, expand_ratio: float = 0.15) -> str | None:
    """
    Crop the lower half of a vehicle's bounding box (where plates usually
    are), pre-process for better OCR accuracy, and return the plate text.

    Parameters
    ----------
    frame       : BGR numpy array — the full video frame.
    box         : (x, y, w, h) bounding box of the vehicle.
    expand_ratio: how much to expand the crop on each side (default 15 %).

    Returns
    -------
    Plate text as a cleaned string, or None if nothing legible was found.
    """
    if frame is None or box is None:
        return None

    x, y, w, h = box
    img_h, img_w = frame.shape[:2]

    # ── 1. Focus on the bottom third of the vehicle (plates live there) ──
    plate_y = y + int(h * 0.55)
    plate_h = int(h * 0.45)

    # ── 2. Expand the crop slightly so we don't clip the plate edges ──
    pad_x = int(w * expand_ratio)
    pad_y = int(plate_h * expand_ratio)

    x1 = max(0,     x - pad_x)
    y1 = max(0,     plate_y - pad_y)
    x2 = min(img_w, x + w + pad_x)
    y2 = min(img_h, plate_y + plate_h + pad_y)

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    # ── 3. Pre-process for OCR ───────────────────────────────────────────
    crop = _preprocess(crop)

    # ── 4. Run OCR ───────────────────────────────────────────────────────
    try:
        reader = _get_reader()
        results = reader.readtext(crop, detail=1, paragraph=False)
    except Exception as e:
        logger.warning(f"OCR error: {e}")
        return None

    # ── 5. Filter & clean ─────────────────────────────────────────────────
    candidates = []
    for (_, text, confidence) in results:
        cleaned = _clean_plate_text(text)
        if cleaned and confidence >= 0.35:
            candidates.append((confidence, cleaned))

    if not candidates:
        return None

    # Return the highest-confidence candidate
    candidates.sort(reverse=True)
    plate = candidates[0][1]
    logger.info(f"Plate read: '{plate}' (conf {candidates[0][0]:.2f})")
    return plate


# ── helpers ──────────────────────────────────────────────────────────────────

def _preprocess(crop: np.ndarray) -> np.ndarray:
    """
    Pipeline tuned for licence plate text:
        resize → grayscale → bilateral filter → adaptive threshold
    """
    # Upscale small crops so OCR has enough pixels to work with
    h, w = crop.shape[:2]
    scale = max(1, int(200 / h))          # target at least 200 px tall
    if scale > 1:
        crop = cv2.resize(crop, (w * scale, h * scale),
                          interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # Bilateral filter keeps edges sharp while reducing noise
    filtered = cv2.bilateralFilter(gray, d=11, sigmaColor=17, sigmaSpace=17)

    # Adaptive threshold handles uneven lighting across the plate
    thresh = cv2.adaptiveThreshold(
        filtered, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Back to BGR so EasyOCR is happy (it accepts both)
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)


# Common OCR mis-reads on number plates
_SUBSTITUTIONS = {
    "O": "0",   # letter O → zero  (context: digit position)
    "I": "1",   # letter I → one
    "S": "5",   # S looks like 5
    "B": "8",   # B looks like 8
    "Z": "2",   # Z looks like 2
}

# Kenyan plates: KAA 123A / KBB 456Z / KCD 789B (adapt as needed)
_PLATE_PATTERN = re.compile(
    r"""
    (?:
        [A-Z]{1,3}\s*\d{1,4}\s*[A-Z]{0,2}   # e.g. KAA 123A
        |
        \d{1,4}\s*[A-Z]{1,3}\s*\d{0,4}       # e.g. 123 KAA
        |
        [A-Z0-9]{4,10}                        # fall-back: 4-10 alphanumerics
    )
    """,
    re.VERBOSE,
)


def _clean_plate_text(raw: str) -> str | None:
    """
    Strip noise characters, apply common OCR corrections, and validate
    against a loose plate pattern.
    """
    # Remove characters that never appear on plates
    cleaned = re.sub(r"[^A-Z0-9\s]", "", raw.upper()).strip()

    # Compact multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned)

    if len(cleaned) < 4:
        return None

    match = _PLATE_PATTERN.search(cleaned)
    if not match:
        return None

    result = match.group(0).strip()
    # Reject if it's all letters with no digits (probably not a plate)
    if result.isalpha() and len(result) <= 5:
        return None
    return result
