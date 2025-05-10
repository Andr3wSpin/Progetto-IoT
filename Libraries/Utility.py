class Utility:
    @staticmethod
    def map_linear(x: int | float, x_start: int | float, x_end: int | float,
                   y_start: int | float, y_end: int | float) -> float:
        if x_end == x_start:
            raise ValueError("x_start e x_end non possono essere uguali")

        ratio = (x - x_start) / (x_end - x_start)
        return y_start + ratio * (y_end - y_start)

    @staticmethod
    def make_irq_handler(callback: "Callable", *args, **kwargs) -> "Callable":
        def handler(pin):
            callback(*args, **kwargs)
        return handler

    class Pointer:
        def __init__(self, value: any):
            self.value = value

# Alias per import diretto
map_linear = Utility.map_linear
make_irq_handler = Utility.make_irq_handler
Pointer = Utility.Pointer

__all__ = ["map_linear", "make_irq_handler", "Pointer"]