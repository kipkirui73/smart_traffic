# modules/plate_reader/reader.py
"""
Number Plate Reader  —  UK format, Tesseract backend
=====================================================
Tested against traffic.mp4 (1920×1080, 30fps road footage).
Reads UK current format plates: AB12 ABC  e.g. NA13 NRU, GX15 OGJ, MY51 VSU
"""

import cv2
import re
import logging
import numpy as np

logger = logging.getLogger(__name__)

_tesseract_ok = None

def _check_tesseract():
    global _tesseract_ok
    if _tesseract_ok is None:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            _tesseract_ok = True
            logger.info("Tesseract OCR ready.")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            _tesseract_ok = False
    return _tesseract_ok


def read_plate(frame, box) -> str | None:
    """
    Extract plate text from a vehicle bounding box in a video frame.
    Returns e.g. 'NA13 NRU' or None if unreadable.
    """
    if frame is None or box is None:
        return None
    if not _check_tesseract():
        return None

    import pytesseract

    x, y, w, h = box
    img_h, img_w = frame.shape[:2]

    # ── Crop the bottom 30% of the vehicle — plate lives here ───────────
    # Tuned on traffic.mp4: top_frac=0.70 gave best results
    py1 = y + int(h * 0.70)
    py2 = min(img_h, y + h)
    x1  = max(0,     x)
    x2  = min(img_w, x + w)

    crop = frame[py1:py2, x1:x2]
    if crop.size == 0:
        return None

    processed = _preprocess(crop)

    whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    config    = f'--psm 11 --oem 3 -c tessedit_char_whitelist="{whitelist}"'

    try:
        import pytesseract
        raw = pytesseract.image_to_string(processed, config=config)
    except Exception as e:
        logger.warning(f"OCR error: {e}")
        return None

    return _clean_plate_text(raw)


def _preprocess(crop: np.ndarray) -> np.ndarray:
    """4× upscale → grayscale → bilateral filter → Otsu threshold."""
    h, w = crop.shape[:2]
    scale = max(2, int(100 / max(h, 1)))
    big   = cv2.resize(crop, (w * scale, h * scale),
                       interpolation=cv2.INTER_CUBIC)
    gray  = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    bil   = cv2.bilateralFilter(gray, 11, 17, 17)
    _, thresh = cv2.threshold(bil, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


# OCR character confusion pairs for the Charles Wright plate font
_LETTER_TO_DIGIT = {"O": "0", "I": "1", "Z": "2", "S": "5",
                    "B": "8", "G": "6", "T": "7"}
_DIGIT_TO_LETTER = {v: k for k, v in _LETTER_TO_DIGIT.items()}

_PLATE_RE = re.compile(
    r"""
    (?:
        [A-Z]{2}\d{2}\s?[A-Z]{3}      # Current:  AB12 ABC  ← most common
        |
        [A-Z]\d{1,3}\s?[A-Z]{3}       # Prefix:   A123 ABC
        |
        [A-Z]{3}\s?\d{1,3}\s?[A-Z]    # Suffix:   ABC 123A
        |
        [A-Z]{1,3}\s?\d{1,4}          # Dateless: ABC 123
        |
        \d{1,4}\s?[A-Z]{1,3}          # Dateless: 1234 AB
    )
    """,
    re.VERBOSE,
)


def _clean_plate_text(raw: str) -> str | None:
    text = re.sub(r"[^A-Z0-9\s]", "", raw.upper())
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) < 4:
        return None

    # ── Scan all 7-char windows in the OCR output ────────────────────────
    compact = text.replace(" ", "")
    for start in range(max(1, len(compact) - 6)):
        window = compact[start:start + 7]
        if len(window) < 7:
            break
        c = list(window)
        # Positional correction: UK AB12 ABC format
        # pos 0,1 → letters;  pos 2,3 → digits;  pos 4,5,6 → letters
        for i in (0, 1, 4, 5, 6):   # must be letters
            c[i] = _DIGIT_TO_LETTER.get(c[i], c[i])
        for i in (2, 3):             # must be digits
            c[i] = _LETTER_TO_DIGIT.get(c[i], c[i])
        # Validate
        if (c[0].isalpha() and c[1].isalpha()
                and c[2].isdigit() and c[3].isdigit()
                and c[4].isalpha() and c[5].isalpha() and c[6].isalpha()):
            plate = "".join(c[:4]) + " " + "".join(c[4:])
            logger.info(f"Plate read: {plate}")
            return plate

    # ── Fall back: pattern match ─────────────────────────────────────────
    for line in text.split("\n"):
        m = _PLATE_RE.search(line.strip())
        if m:
            result = m.group(0).strip()
            if not result.isalpha():
                logger.info(f"Plate read (pattern): {result}")
                return result

    return None
