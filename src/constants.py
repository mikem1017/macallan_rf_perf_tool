"""
Constants for Macallan RF Performance Tool
"""

# Test stage constants
TEST_STAGES = {
    "board_bringup": "board_bringup",
    "sit": "sit", 
    "test_campaign": "test_campaign"
}

# Test stage display names
TEST_STAGE_DISPLAY_NAMES = {
    "board_bringup": "Board Bring-up",
    "sit": "SIT",
    "test_campaign": "Test Campaign"
}

# Default test stage
DEFAULT_TEST_STAGE = "board_bringup"

# Plot expansion factors
PLOT_EXPANSION_FACTOR = 0.1
VSWR_Y_AXIS_EXPANSION_FACTOR = 1.2

# P1dB calculation threshold
P1DB_THRESHOLD_DB = 1.0

# Plot styling
ACCEPTANCE_REGION_ALPHA = 0.3
ACCEPTANCE_REGION_COLOR = 'green'
SUBTITLE_Y_POSITION = -0.15
SUBTITLE_X_POSITION = 0.5



