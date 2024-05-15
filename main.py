from BlueprintMaker import FactorioVideoBlueprint

filepath = input("Etner video file path: ")

resize = input("Do you want resize video? [Y/N]: ")

if resize.upper() == "Y": resize = True
else: resize = False

if resize: height = int(input("Enter new height of video in pixels: "))
else: height = None

invert = input("Do you want invert video? [Y/N]: ")

if invert.upper() == "Y": invert = True
else: invert = False

BlueprintMaker = FactorioVideoBlueprint(filepath, height=height, is_resize=resize,
                                        is_invert=invert, is_frame_print=True, is_echo=True)

BlueprintMaker.OneBlueprint()