import sys, json, math, zlib, base64, shutil

from VideoParser import VideoFormatCreate
from LoadSettings import LoadSettings
from EntityCreator import Creator
from SignalParser import Signal
from MatrixChanger import MatrixChanger


class FactorioVideoBlueprint():
    """Main class"""

    def __init__(self, video_filepath: str,  # main params
                 height: int = None, is_resize: bool = False, is_invert: bool = False,  # params for video
                 settings_folder_name:str = "settings",  # params for settings
                 debug_mode: bool = False, is_frame_print: bool = False, is_echo: bool = False  # params for other
                 ) -> None:
        
        self.debug_mode = debug_mode
        self.is_echo = is_echo
        self.is_frame_print = is_frame_print
        self.path = sys.path[0]
        self.pressets, self.signals = LoadSettings(f"{self.path}\\{settings_folder_name}")  # load settings

        VideoFormatCreate(video_filepath, is_invert=is_invert, is_resize=is_resize, debug_mode=debug_mode, height=height)  # Create json with data about all frames
        self.load_video()

        self.height = self.video["height"]
        self.width = self.video["width"]

        self.constant_combinator_count = math.ceil(height / 20)
        self.counter_pos_delay = 2
        self.substation_delay = 18

        self.creator = Creator(self.pressets["entity-base"], self.pressets["connection-base"], self.pressets["neighbours-base"])
        self.signal = Signal(self.signals, self.pressets["siganl-base"], height=self.height, width=self.width)

        self.blueprint = self.pressets["blueprint"]
        self.entities = self.blueprint["entities"]

        self.entity_counter = 1

    def OneBlueprint(self):
        if self.is_echo: print("start frames create")
        self.FramesCreate()
        if self.is_echo: print("start frames connect")
        self.FramesConnect()
        if self.is_echo: print("start counter create")
        self.CounterCreate()
        if self.is_echo: print("start screen create")
        self.ScreenCreate()
        if self.is_echo: print("start ticker create")
        self.CreateTicker()

        if self.is_echo: print("start blueprint generate")
        blueprint = {"blueprint": self.blueprint}
        
        with open(f"{self.path}\\blueprint.txt", "w") as f:
            f.write(self.GenerateBlueprint(blueprint))

        self.blueprint = self.pressets["blueprint"]

        if self.is_echo: print("blueprint generated")

        try:
            shutil.rmtree(f"{self.path}\\temp\\")
        except FileNotFoundError:
            pass

        
    def GenerateBlueprint(self, data: dict) -> str:
        data = json.dumps(data)
        data = zlib.compress(data.encode())
        data = str(base64.b64encode(data), 'utf-8')

        return f"0{data}"


    def load_video(self) -> None:
        """Load json video from temp folder"""
        with open(f"{self.path}\\temp\\video.json") as f:
            self.video = json.load(f)["format"]


    def FramesCreate(self):
        """Function for create frames"""
        last_neighbour = None
        decider_flag = True

        if self.is_frame_print: frame_counter = 0
        if self.is_frame_print: print(f'frame count: {self.video["frames_count"]}')

        self.x = 0
        self.y = 0

        self.frame_deciders_list = []
        self.connection_deciders_list = []
        self.frame_poles_list = []

        for frame in self.video["frames"]:
            if self.is_frame_print:
                frame_counter += 1
                print(f'frame {frame_counter} / {self.video["frames_count"]} creating')

            signals_list = self.signal.ParseSignals(frame)

            data = []
            entity_ids = []
            closer_constants = []
            closer_deciders = []
            closer_poles = []

            stations = []

            flag = True

            # deciders create
            for counter in range(1, self.width + 1):
                entity = self.creator.EntityCreate(self.entity_counter, "decider-combinator", self.x, self.y)
                entity.update(self.pressets["frame-decider-const"])

                closer_deciders.append(self.entity_counter)

                data.append(entity)

                logical_end = counter
                last_decider = self.entity_counter
                self.entity_counter += 1
                self.x += 1

            self.y += 1
            self.x -= self.width

            # constant create
            for counter in range(self.constant_combinator_count):
                entity_ids.append([])

                for i in range(1, self.width + 1):
                    entity = self.creator.EntityCreate(self.entity_counter, "constant-combinator", self.x, self.y)

                    signals = signals_list[i - 1]

                    if len(signals_list) != 0:
                        entity.update({'control_behavior': {'filters': []}})

                        for signal_count in range(1, 21):
                            if len(signals) != 0:
                                entity["control_behavior"]["filters"].append(
                                    self.signal.CreateOneSignal(signals=signals[0], counter=signal_count)
                                    )
                                signals.pop(0)

                    data.append(entity)

                    entity_ids[counter].append(self.entity_counter)
                    if flag: closer_constants.append(self.entity_counter)

                    self.entity_counter += 1
                    self.x += 1

                falg = False

                self.x -= self.width
                self.y += 1

            entity_ids = MatrixChanger(entity_ids, height=self.constant_combinator_count, width=self.width)

            # constant connect
            for i in range(logical_end, len(data)):
                a, b = self.find_index(entity_ids, data[i]["entity_number"])
                self.creator.ConnectionCreate(data[i])
                
                if b > 0: self.creator.ConnectionAdd(data[i], entity_ids[a][b-1], "1", "red")
                if b < self.constant_combinator_count - 1: self.creator.ConnectionAdd(data[i], entity_ids[a][b+1], "1", "red")
            
            # deciders connect
            for i in range(self.width):
                self.creator.ConnectionCreate(data[i])

                self.creator.ConnectionAdd(data[i], closer_constants[i], "1", "red")
                if i != self.width - 1: self.creator.ConnectionAdd(data[i], closer_deciders[i + 1], "1", "green", circuit_id=1)

            # poles create
            for i in range(self.width):
                entity = self.creator.EntityCreate(self.entity_counter, "medium-electric-pole", self.x, self.y)
                self.creator.ConnectionCreate(entity)

                closer_poles.append(self.entity_counter)

                data.append(entity)

                self.entity_counter += 1
                self.x += 1

            self.x -= self.width
            self.y += 2
            

            # substations create
            for i in range((self.width // self.substation_delay) + 2):
                entity = self.creator.EntityCreate(self.entity_counter, "substation", self.x + 1, self.y)

                stations.append(self.entity_counter)

                self.entity_counter += 1
                self.x += self.substation_delay

                data.append(entity)

            self.x -= ((self.width // self.substation_delay) + 2) * self.substation_delay
            self.y += 1

            if last_neighbour is not None:
                stations.append(last_neighbour)

            # substation connect
            for i in range((self.width // self.substation_delay) + 2):
                self.creator.NeighboursConnect(data[len(data) - 1 - i], stations)

            if last_neighbour is None:
                last_neighbour = stations[len(stations) - 1]
                self.first_substation = last_neighbour
            else:
                last_neighbour = stations[len(stations) - 2]

            self.y += 1 

            if decider_flag:
                self.output_side = closer_deciders
                decider_flag = False

            # save data
            self.connection_deciders_list.append(last_decider)
            self.frame_deciders_list.append(closer_deciders)
            self.frame_poles_list.append(closer_poles)

            for upd in data:
                self.entities.append(upd)


    def find_index(self, l: list, value: int) -> tuple:
        """Function for finding indexes in matrix"""
        for row, sublist in enumerate(l):
            if (bool(set(sublist) & {value})): 
                return (row, sublist.index(value))   


    def FramesConnect(self):
        """Function for connect frames"""
        self.frame_deciders_list = MatrixChanger(self.frame_deciders_list, len(self.frame_deciders_list), len(self.frame_deciders_list[0]))
        self.frame_poles_list = MatrixChanger(self.frame_poles_list, len(self.frame_poles_list), len(self.frame_poles_list[0]))

        connection_queue = []

        for y in range(len(self.frame_deciders_list)):
            connection_queue.append([])
            for i in range(len(self.frame_deciders_list[0])):
                connection_queue[y].append(self.frame_deciders_list[y][i])
                connection_queue[y].append(self.frame_poles_list[y][i])

        for i in connection_queue:
            for j in range(len(connection_queue[0]) - 1):
                self.creator.ConnectionAdd(self.entities[i[j] - 1], i[j + 1], "2", "green")
                self.creator.ConnectionAdd(self.entities[i[j] - 1], i[j - 1], "2", "green")


    def CounterCreate(self):
        """Function for create counter with signals for frames"""
        last_pole = None
        self.x = 0
        self.y = 0

        first_pole_flag = True

        for frame in range(self.video["frames_count"]):
            self.x = self.width + self.counter_pos_delay

            data = []

            entity = self.creator.EntityCreate(self.entity_counter, "decider-combinator", self.x, self.y)
            self.creator.ConnectionCreate(entity)

            entity.update({'direction': 4, 'control_behavior': {'decider_conditions':
                                                                {'first_signal': {'type': 'virtual', 'name': 'signal-dot'},
                                                                 'constant': frame + 1, 'comparator': '=', 'output_signal':
                                                                 {'type': 'virtual', 'name': 'signal-green'}, 'copy_count_from_input': False}}})

            if last_pole is not None:
                self.creator.ConnectionAdd(entity, last_pole, "1", "red")

            self.creator.ConnectionAdd(entity, self.entity_counter + 1, "1", "red")
            self.creator.ConnectionAdd(entity, self.connection_deciders_list[frame], "2", "green", circuit_id=1)

            data.append(entity)

            self.entity_counter += 1
            self.y += self.constant_combinator_count + 1

            entity = self.creator.EntityCreate(self.entity_counter, "medium-electric-pole", self.x, self.y)
            last_pole = self.entity_counter

            if first_pole_flag:
                self.first_pole = last_pole
                first_pole_flag = False

            data.append(entity)

            self.entity_counter += 1
            self.y += 4

            for upd in data:
                self.entities.append(upd)


    def ScreenCreate(self):
        """Function for creating screen"""
        self.x = 0
        self.y = -4

        data = []
        stations = []
        stations_cords = []

        last_neighbour = None
        connected_flag = True

        decider_counter = 0

        # substation create
        for j in range((self.height // self.substation_delay) + 2):
            for i in range((self.width // self.substation_delay) + 2):
                entity = self.creator.EntityCreate(self.entity_counter, "substation", self.x + 1, self.y - j * self.substation_delay)
                stations_cords.append([self.x + 1, self.y - j * self.substation_delay])

                stations.append(self.entity_counter)

                self.entity_counter += 1
                self.x += self.substation_delay

                data.append(entity)

            self.x -= ((self.width // self.substation_delay) + 2) * self.substation_delay

            if connected_flag:
                stations.append(self.first_substation)
                connected_flag = False  
            
            if last_neighbour is not None:
                stations.append(last_neighbour)

            # substation connect
            for i in range((self.width // self.substation_delay) + 2):
                self.creator.NeighboursConnect(data[len(data) - i - 1], stations)

            if last_neighbour is None:
                last_neighbour = stations[len(stations) - 1]
            else:
                last_neighbour = stations[len(stations) - 2]
        
        # lamps create
        for x in range(self.width):
            counter = self.height - 1
            last_lamp = None
            flag2 = False
            flag3 = False

            for y in range(self.height):
                flag = True
                
                for i in stations_cords:
                    if (i[0] == self.x and i[1] == self.y) or (i[0] == self.x + 1 and i[1] == self.y) or \
                        (i[0] == self.x and i[1] == self.y + 1) or (i[0] == self.x + 1 and i[1] == self.y + 1):
                        flag = False
                        flag3 = True

                        if y == 0:
                            flag2 = True

                        counter -= 1

                if flag3 and y == 3:
                    self.creator.ConnectionAdd(connection_lamp, self.output_side[decider_counter], "1", "green", circuit_id=2)
                    decider_counter += 1

                if flag:
                    entity = self.creator.EntityCreate(self.entity_counter, "small-lamp", self.x, self.y)
                    signal = self.signals["signals"][str(counter)]

                    self.creator.ConnectionCreate(entity)

                    if counter < self.signals["start_of_virtual_signals"]: signal_type = "item"
                    elif counter >= self.signals["start_of_virtual_signals"]: signal_type = "virtual"
                        
                    entity.update({"control_behavior": {"circuit_condition": {"first_signal":
                                                                            {"type": signal_type, "name": signal},
                                                                            "constant": 0, "comparator": ">"}}})

                    if last_lamp is not None:
                        self.creator.ConnectionAdd(entity, last_lamp, "1", "green")

                    if self.height - y == self.height - 1:
                        self.creator.ConnectionAdd(entity, self.output_side[decider_counter], "1", "green", circuit_id=2)
                        decider_counter += 1

                    last_lamp = self.entity_counter

                    if flag2:
                        connection_lamp = entity
                        flag2 = False

                    data.append(entity)

                    self.entity_counter += 1
                    counter -= 1

                self.y -= 1

            self.x += 1
            self.y += self.height

        for upd in data:
            self.entities.append(upd)

    def CreateTicker(self):
        self.x = self.width + self.counter_pos_delay + 2
        self.y = 1

        self.entity_counter -= 1

        ticker = [
            {"entity_number": self.entity_counter + 1, "name": "decider-combinator", "position": {"x": self.x, "y": self.y - 0.5}, "direction": 2, "control_behavior": {"decider_conditions": {"first_signal": {"type": "virtual", "name": "signal-dot"}, "constant": 60 // self.video["frame_rate"], "comparator": "\u2264", "output_signal": {"type": "virtual", "name": "signal-dot"}, "copy_count_from_input": True}}, "connections": {"1": {"green": [{"entity_id": self.entity_counter + 1, "circuit_id": 2}, {"entity_id": self.entity_counter + 2}]}, "2": {"red": [{"entity_id": self.entity_counter + 8, "circuit_id": 1}], "green": [{"entity_id": self.entity_counter + 1, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 2, "name": "constant-combinator", "position": {"x": self.x + 0.5, "y": self.y - 1.5}, "control_behavior": {"filters": [{"signal": {"type": "virtual", "name": "signal-dot"}, "count": 1, "index": 1}]}, "connections": {"1": {"green": [{"entity_id": 1, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 3, "name": "constant-combinator", "position": {"x": self.x + 2.5, "y": self.y - 1.5}, "direction": 4, "control_behavior": {"filters": [{"signal": {"type": "virtual", "name": "signal-S"}, "count": 1, "index": 1}, {"signal": {"type": "virtual", "name": "signal-T"}, "count": 1, "index": 2}, {"signal": {"type": "virtual", "name": "signal-A"}, "count": 1, "index": 3}, {"signal": {"type": "virtual", "name": "signal-R"}, "count": 1, "index": 4}, {"signal": {"type": "virtual", "name": "signal-T"}, "count": 1, "index": 5}, {"signal": {"type": "virtual", "name": "signal-green"}, "count": 1, "index": 20}], "is_on": False}, "connections": {"1": {"red": [{"entity_id": self.entity_counter + 5}, {"entity_id": self.entity_counter + 10, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 4, "name": "arithmetic-combinator", "position": {"x": self.x + 2, "y": self.y - 0.5}, "direction": 2, "control_behavior": {"arithmetic_conditions": {"first_signal": {"type": "virtual", "name": "signal-dot"}, "second_constant": -1, "operation": "*", "output_signal": {"type": "virtual", "name": "signal-dot"}}}, "connections": {"1": {"red": [{"entity_id": 6, "circuit_id": 2}]}, "2": {"green": [{"entity_id": 9, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 5, "name": "constant-combinator", "position": {"x": self.x + 3.5, "y": self.y - 1.5}, "direction": 4, "control_behavior": {"filters": [{"signal": {"type": "virtual", "name": "signal-S"}, "count": 1, "index": 1}, {"signal": {"type": "virtual", "name": "signal-T"}, "count": 1, "index": 2}, {"signal": {"type": "virtual", "name": "signal-O"}, "count": 1, "index": 3}, {"signal": {"type": "virtual", "name": "signal-P"}, "count": 1, "index": 4}, {"signal": {"type": "virtual", "name": "signal-red"}, "count": 1, "index": 20}], "is_on": False}, "connections": {"1": {"red": [{"entity_id": self.entity_counter + 3}]}}},
            {"entity_number": self.entity_counter + 6, "name": "decider-combinator", "position": {"x": self.x + 4, "y": self.y - 0.5}, "direction": 2, "control_behavior": {"decider_conditions": {"first_signal": {"type": "virtual", "name": "signal-anything"}, "constant": 0, "comparator": ">", "output_signal": {"type": "virtual", "name": "signal-anything"}, "copy_count_from_input": True}}, "connections": {"1": {"green": [{"entity_id": self.entity_counter + 6, "circuit_id": 2}, {"entity_id": self.entity_counter + 7, "circuit_id": 2},{"entity_id": self.entity_counter + 9, "circuit_id": 2}]}, "2": {"red": [{"entity_id": self.entity_counter + 4, "circuit_id": 1}, {"entity_id": self.entity_counter + 11, "circuit_id": 1}], "green": [{"entity_id": self.entity_counter + 6, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 7, "name": "decider-combinator", "position": {"x": self.x, "y": self.y + 1.5}, "direction": 2, "control_behavior": {"decider_conditions": {"first_signal": {"type": "virtual", "name": "signal-each"}, "constant": 0, "comparator": ">", "output_signal": {"type": "virtual", "name": "signal-dot"}, "copy_count_from_input": False}}, "connections": {"1": {"green": [{"entity_id": self.entity_counter + 8, "circuit_id": 2}]}, "2": {"green": [{"entity_id": self.entity_counter + 6, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 8, "name": "arithmetic-combinator", "position": {"x": self.x, "y": self.y + 0.5}, "direction": 2, "control_behavior": {"arithmetic_conditions": {"first_signal": {"type": "virtual", "name": "signal-each"}, "second_constant": 60 // self.video["frame_rate"], "operation": "/", "output_signal": {"type": "virtual", "name": "signal-each"}}}, "connections": {"1": {"red": [{"entity_id": self.entity_counter + 1, "circuit_id": 2}]}, "2": {"green": [{"entity_id": self.entity_counter + 7, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 9, "name": "decider-combinator", "position": {"x": self.x + 2, "y": self.y + 0.5}, "direction": 6, "control_behavior": {"decider_conditions": {"first_signal": {"type": "virtual", "name": "signal-green"}, "constant": 1, "comparator": "<", "output_signal": {"type": "virtual", "name": "signal-everything"}, "copy_count_from_input": True}}, "connections": {"1": {"red": [{"entity_id": self.entity_counter + 10, "circuit_id": 2}], "green": [{"entity_id": self.entity_counter + 4, "circuit_id": 2}]}, "2": {"green": [{"entity_id": self.entity_counter + 6, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 10, "name": "decider-combinator", "position": {"x": self.x + 2, "y": self.y + 1.5}, "direction": 2, "control_behavior": {"decider_conditions": {"first_signal": {"type": "virtual", "name": "signal-green"}, "second_signal": {"type": "virtual", "name": "signal-red"}, "comparator": ">", "output_signal": {"type": "virtual", "name": "signal-green"}, "copy_count_from_input": False}}, "connections": {"1": {"red": [{"entity_id": self.entity_counter + 3}], "green": [{"entity_id": self.entity_counter + 10, "circuit_id": 2}]}, "2": {"red": [{"entity_id": self.entity_counter + 9, "circuit_id": 1}], "green": [{"entity_id": self.entity_counter + 10, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 11, "name": "arithmetic-combinator", "position": {"x": self.x + 3.5, "y": self.y + 1}, "direction": 4, "control_behavior": {"arithmetic_conditions": {"first_signal": {"type": "virtual", "name": "signal-each"}, "second_constant": self.video["frames_count"], "operation": "%", "output_signal": {"type": "virtual", "name": "signal-dot"}}}, "connections": {"1": {"red": [{"entity_id": self.entity_counter + 6, "circuit_id": 2}]}, "2": {"red": [{"entity_id": self.entity_counter + 12, "circuit_id": 1}]}}},
            {"entity_number": self.entity_counter + 12, "name": "arithmetic-combinator", "position": {"x": self.x + 4.5, "y": self.y + 1}, "direction": 4, "control_behavior": {"arithmetic_conditions": {"first_signal": {"type": "virtual", "name": "signal-dot"}, "second_constant": 1, "operation": "+", "output_signal": {"type": "virtual", "name": "signal-dot"}}}, "connections": {"1": {"red": [{"entity_id": self.entity_counter + 11, "circuit_id": 2}]}, "2": {"red": [{"entity_id": self.first_pole, "circuit_id": 1}]}}}
                  ]

        for upd in ticker:
            self.entities.append(upd)

if __name__ == "__main__":
    video = input("video path: ")

    x = FactorioVideoBlueprint(video, height=64, is_invert=True, is_resize=True, is_frame_print=True, is_echo=True)

    x.OneBlueprint()