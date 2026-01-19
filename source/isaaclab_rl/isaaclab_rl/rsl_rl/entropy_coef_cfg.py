from isaaclab.utils import configclass


@configclass
class RslRlEntropyCoefCfg:
    """The configuration for the entropy coefficient."""

    entropy_coef: float = 0.01
    """The initial value of the entropy coefficient. Default is 0.01."""

    schedule: str = "linear"
    """The schedule of the entropy coefficient. Default is linear.
    
    Supported schedules:
        - "linear": Linear interpolation between initial and target value.
        - "exp": Exponential interpolation (requires positive values).
        - "cosine": Cosine annealing.
    """
    
    schedule_target: float = 0.0
    """The end value of the entropy coefficient. Default is 0.0.""" 
    
    start_ratio: float = 0.0
    """The start ratio of the schedule. Default is 0."""
    
    end_ratio: float = 1.0
    """The end ratio of the schedule. Default is 1.0."""
