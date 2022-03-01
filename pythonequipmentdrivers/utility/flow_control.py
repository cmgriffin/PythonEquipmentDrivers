from time import sleep
from typing import Callable


def wait_unit(meas_func: Callable[[], float], limit: float, limit_type: str):
    """
    A sweep flow control function that waits until a measurement is within the 
    desired range.

    Typically used to pause a sweep before the next operating point while the 
    unit under test cools down 

    Args:
        meas_func (Callable[[], float]): A callable that takes no arguments and 
        returns the measurement intended to be checked
        limit (float): Limit to impose on the measurement value
        limit_type (str):  Whether limit is considered a minimum ("LOW") or 
        maximum ("HIGH")
    """
    def check_value(value):
        if limit_type == "LOW":
            return value > limit
        elif limit_type == "HIGH":
            return value < limit
        else:
            raise ValueError(f"Invalid limit_type of {limit_type}")

    waiting = True
    meas = meas_func()
    less_greater = "<" if limit_type == "HIGH" else ">"
    print(
        f"waiting for value to be {less_greater}{limit}, current value: {meas}",
        end="",
    )
    while waiting:
        print(" .", end="", flush=True)
        if check_value(meas):
            waiting = False
            print("\n")
        sleep(1)
        meas = meas_func()
