import parselmouth as pm
import tgt
from os import listdir, makedirs
from sys import stderr

inputTextGridDirectory = "TextGrid/"
inputWavDirectory = "wav/"
outputTextGridDirectory = "TextGridOutput/"

def number_to_str(num):
    return "{:6f}".format(num)

def add_formants_at_time(formants, time, f1tier, f2tier, f3tier):
    f1freq = formants.get_value_at_time(1, time)
    f2freq = formants.get_value_at_time(2, time)
    f3freq = formants.get_value_at_time(3, time)
    f1tier.add_point(tgt.Point(time, text=number_to_str(f1freq)))
    f2tier.add_point(tgt.Point(time, text=number_to_str(f2freq)))
    f3tier.add_point(tgt.Point(time, text=number_to_str(f3freq)))

def process_sample(textGridFileName, wavFileName, outputTextGridFileName, encoding='utf-16'):
    tg = tgt.read_textgrid(textGridFileName, encoding=encoding)
    sound = pm.Sound(wavFileName)
    formants = sound.to_formant_burg()

    newtg = tgt.TextGrid()

    sentence = tg.tiers[0]
    word = tg.tiers[1]
    vowel = tg.tiers[2]

    start_time = sentence.start_time
    end_time = sentence.end_time

    length = tgt.IntervalTier(start_time, end_time, 'Länge')
    point = tgt.PointTier(start_time, end_time, 'Point')
    f1 = tgt.PointTier(start_time, end_time, 'F1')
    f2 = tgt.PointTier(start_time, end_time, 'F2')
    f3 = tgt.PointTier(start_time, end_time, 'F3')

    for interval in vowel:
        start = interval.start_time
        end = interval.end_time
        mid = start + (end - start) / 2
        left_mid = start + (end - start) / 4
        right_mid = end - (end - start) / 4

        length_interval = tgt.Interval(start, end, text=number_to_str(end - start))
        length.add_interval(length_interval)

        # monophthong
        if len(interval.text) == 1:
            point.add_point(tgt.Point(mid))
            add_formants_at_time(formants, mid, f1, f2, f3)
        # diphthong
        elif len(interval.text) == 2:
            point_point1 = tgt.Point(left_mid)
            point_point2 = tgt.Point(right_mid)
            point.add_point(point_point1)
            point.add_point(point_point2)
            add_formants_at_time(formants, left_mid, f1, f2, f3)
            add_formants_at_time(formants, right_mid, f1, f2, f3)
        # triphthong
        elif len(interval.text) == 3:
            point_point1 = tgt.Point(left_mid)
            point_point2 = tgt.Point(mid)
            point_point3 = tgt.Point(right_mid)
            point.add_point(point_point1)
            point.add_point(point_point2)
            point.add_point(point_point3)
            add_formants_at_time(formants, left_mid, f1, f2, f3)
            add_formants_at_time(formants, mid, f1, f2, f3)
            add_formants_at_time(formants, right_mid, f1, f2, f3)
        else:
            raise Exception("Only monophthongs, diphthongs and triphthongs are implemented")

    # write new file
    newtg.add_tier(sentence)
    newtg.add_tier(word)
    newtg.add_tier(vowel)
    newtg.add_tier(length)
    newtg.add_tier(f1)
    newtg.add_tier(f2)
    newtg.add_tier(f3)

    tgt.io.write_to_file(newtg, outputTextGridFileName, format='long', encoding=encoding)

files = sorted(listdir(inputTextGridDirectory))
print("Processing {} files".format(len(files)))

makedirs(outputTextGridDirectory, exist_ok=True)

for i in range(len(files)):
    textGridFile = files[i]
    if not textGridFile.endswith('.TextGrid'):
        continue
    basename = textGridFile.removesuffix('.TextGrid')
    textGridFileName = inputTextGridDirectory + basename + ".TextGrid"
    wavFileName = inputWavDirectory + basename + ".wav"
    outputTextGridFileName = outputTextGridDirectory + basename + ".TextGrid"
    print(str(i+1) + ". Processing file " + basename)
    try:
        process_sample(textGridFileName, wavFileName, outputTextGridFileName)
    except Exception as e:
        print(str(i+1) + ". Error while processing file: " + str(e), file=stderr)
