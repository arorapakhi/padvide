"""Central settings for PadVide. Edit values here, not scattered in code."""

# ---------- Identity ----------
APP_NAME = "PadVide"
APP_TAGLINE = "Care, stocked and accounted for."
SCHOOL_NAME = "Rosewood Middle & High School"

# ---------- Palette ----------
COLORS = {
    "dusty_rose":    "#C98A94",
    "warm_cream":    "#FDF6EC",
    "sage_green":    "#9CAF95",
    "muted_coral":   "#E09383",
    "soft_lavender": "#C5BBD6",
    "deep_plum":     "#4A3B45",
    "soft_gray":     "#8C8289",
    "card_cream":    "#FFFBF5",
    "border_tan":    "#E8DCCA",
}

# ---------- Statuses ----------
STATUS_STOCKED = "stocked"
STATUS_LOW     = "low"
STATUS_EMPTY   = "empty"
STATUS_OFFLINE = "offline"
STATUS_FAULTY  = "faulty"

STATUS_LABELS = {
    STATUS_STOCKED: "Stocked",
    STATUS_LOW:     "Low inventory",
    STATUS_EMPTY:   "Empty",
    STATUS_OFFLINE: "Sensor offline",
    STATUS_FAULTY:  "Needs repair",
}

STATUS_COLORS = {
    STATUS_STOCKED: COLORS["sage_green"],
    STATUS_LOW:     COLORS["muted_coral"],
    STATUS_EMPTY:   COLORS["dusty_rose"],
    STATUS_OFFLINE: COLORS["soft_gray"],
    STATUS_FAULTY:  COLORS["soft_lavender"],
}

# Pale versions for table row backgrounds.
STATUS_TINTS = {
    STATUS_STOCKED: "#EDF2EB",
    STATUS_LOW:     "#FBEDE9",
    STATUS_EMPTY:   "#F7E9EB",
    STATUS_OFFLINE: "#EFECEE",
    STATUS_FAULTY:  "#F1EEF6",
}

# How urgently each status needs a human. Lower = more urgent.
STATUS_PRIORITY = {
    STATUS_EMPTY:   0,
    STATUS_FAULTY:  1,
    STATUS_OFFLINE: 2,
    STATUS_LOW:     3,
    STATUS_STOCKED: 9,
}

# ---------- Thresholds ----------
LOW_THRESHOLD = 30        # fill % at or below this -> low
EMPTY_THRESHOLD = 5       # fill % at or below this -> empty
OFFLINE_AFTER_MINUTES = 90

# ---------- Paths ----------
DB_PATH = "data/padvide.db"
ILLUSTRATION_DIR = "assets/illustrations"