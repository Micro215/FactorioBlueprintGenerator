import moviepy.editor as mp
import cv2

from PIL import Image
import numpy as np

import sys, os, shutil
import json


class VideoFormatCreate():
    """This class used to create json with arrays of pixels for every frame of video"""

    def __init__(self, filepath: str, height: int = None, is_resize: bool = False, debug_mode: bool = False, is_invert: bool = False) -> None:
        self.debug_mode = debug_mode
        
        self.filepath = filepath
        if self.debug_mode: print(f"VideoFormatCreate.init: filepath: {self.filepath}")

        self.temp_folder = f"{sys.path[0]}\\temp\\"
        if self.debug_mode: print(f"VideoFormatCreate.init: temp folder path: {self.temp_folder}")

        try:
            os.mkdir(self.temp_folder)
            if self.debug_mode: print("VideoFormatCreate.init: created temp folder")
        except FileExistsError:
            if self.debug_mode: print("VideoFormatCreate.init: temp folder already exist")

        if is_resize:
            self.resizer(height)

        self.slicer()
        self.formating(is_invert=is_invert)

        try:
            shutil.rmtree(self.frames_folder)
            if self.debug_mode: print("VideoFormatCreate.init: deleted frames folder")
        except FileNotFoundError:
            if self.debug_mode: print("VideoFormatCreate.init: folder don't exist")

        if self.debug_mode: print("VideoFormatCreate.init: end of class working")


    def resizer(self, height: int) -> None:
        """Function for resize video"""

        if self.debug_mode: print("VideoFormatCreate.resize: start resizing video")

        clip = mp.VideoFileClip(self.filepath, audio=False)
        clip_resized = clip.resize(height=height)

        self.filepath = self.temp_folder + "resized_video.mp4"
        clip_resized.write_videofile(self.filepath)

        if self.debug_mode: print("VideoFormatCreate.resize: stop resizing video")


    def slicer(self) -> None:
        """Function for slicing by frame"""
        
        if self.debug_mode: print("VideoFormatCreate.slicer: start slicing video")

        self.frames_folder = self.temp_folder + "frames\\"
        try:
            os.mkdir(self.frames_folder)
            if self.debug_mode: print("VideoFormatCreate.slicer: created frames folder")
        except FileExistsError:
            if self.debug_mode: print("VideoFormatCreate.slicer: frames folder already exist")

        capture = cv2.VideoCapture(self.filepath)
        self.frames_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        self.frame_rate = int(capture.get(cv2.CAP_PROP_FPS))

        if self.debug_mode: print(f"VideoFormatCreate.slicer: count of frames: {self.frames_count}")

        counter = 0

        while capture.isOpened():
            ret, frame = capture.read()

            if not ret:
                continue

            cv2.imwrite(self.frames_folder + "/%#09d.jpg" % (counter + 1), frame)
            counter += 1

            if (counter > (self.frames_count - 1)):
                capture.release
                break

        if self.debug_mode: print("VideoFormatCreate.slicer: stop slicing video")

    def formating(self, is_invert: bool) -> None:
        """Function to create json file where every frame is saved as matrix"""

        if self.debug_mode: print("VideoFormatCreate.formating: start formating video")
        if self.debug_mode: counter = 0

        image_paths = []
        matrixes = []

        for i in range(self.frames_count):
            image_paths.append(self.frames_folder + "/%#09d.jpg" % (i + 1))

        image = cv2.imread(image_paths[0])
        height, width, channel = image.shape  # channel not used

        if is_invert:
            x, y = 0, 1
        else:
            x, y = 1, 0
        
        for image_path in image_paths:
            image = Image.open(image_path)

            thresh = 200
            fn = lambda x : 255 if x > thresh else 0
            image = image.convert("L").point(fn, mode="1")
        
            image.thumbnail(size=(width, height))

            image_as_matrix = np.array(image)
            image_as_matrix = image_as_matrix.tolist()

            for i in range(height):
                for j in range(width):
                    if image_as_matrix[i][j]: image_as_matrix[i][j] = x
                    else: image_as_matrix[i][j] = y

            matrixes.append(image_as_matrix)

            if self.debug_mode:
                counter += 1
                print(f"VideoFormatCreate.formating: frame {counter} created")

        data = {"format" : {"frames_count": self.frames_count, "frame_rate": self.frame_rate, "height": height, "width": width, "frames": matrixes}}
        data = json.dumps(data)

        with open(f"{self.temp_folder}video.json", "w") as f:
            f.write(data)

        if self.debug_mode: print("VideoFormatCreate.formating: created video.json")

        if self.debug_mode: print("VideoFormatCreate.formating: stop foramting video")


if __name__ == "__main__":
    filepath = input("filepath: ")

    VideoFormatCreate(filepath, height=64, is_resize=True, debug_mode=True)