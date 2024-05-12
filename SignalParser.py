from MatrixChanger import MatrixChanger
import copy


class Signal():
    """Class for making signal in constant combinator"""
    def __init__(self, signals_list: dict, signal_base: dict, height: int, width: int) -> None:
        self.signal_const = signals_list["start_of_virtual_signals"]
        self.signals_list = signals_list["signals"]
        self.signal_base = signal_base
        self.height = height
        self.width = width

    def ParseSignals(self, frame: list) -> list:
        signal_type = None
        signals = []

        frame = MatrixChanger(frame, self.height, self.width)

        for i in range(self.width):
            counter = 0

            signals.append([])

            for j in range(self.height):
                if frame[i][j] == 1:
                    if counter < self.signal_const: signal_type = "item"
                    elif counter >= self.signal_const: signal_type = "virtual"
                    else: print("smth wrong with generate signals")

                    signals[i].append([self.signals_list[str(counter)], signal_type])

                counter += 1

        return signals
    
    def CreateOneSignal(self, signals: list, counter: int) -> dict:
        signal = copy.deepcopy(self.signal_base)

        signal["signal"]["name"] = signals[0]
        signal["signal"]["type"] = signals[1]
        signal["index"] = counter

        return signal