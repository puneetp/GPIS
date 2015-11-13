from tfx import point, rotation
from numpy import pi
class DexConstants:

    ROBOT_OP_TIMEOUT = 2

    ZEKE_LOCAL_FRAME = "ZEKE_LOCAL_FRAME"
    WORLD_FRAME = "WORLD_FRAME"
    
    ORIGIN = point(0,0,0)
    
    MAX_ROT_SPEED = pi/2 #90 degrees per second maximum rotation
    MAX_TRA_SPEED = 0.1 #10cm per second maximum translation
    
    INTERP_TIME_STEP = 0.03 #30ms interpolation time step
    INTERP_MAX_RAD = MAX_ROT_SPEED * INTERP_TIME_STEP 
    INTERP_MAX_M = MAX_TRA_SPEED * INTERP_TIME_STEP 

    DEFAULT_ROT_SPEED = pi/4 #rad per second
    DEFAULT_TRA_SPEED = 0.06 #6cm per second (roughly 5 secs for 1 ft)