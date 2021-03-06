# coding=utf-8
import os,sys
import glob
import json
import numpy as np
import cv2
import fileinput

reload(sys) 
sys.setdefaultencoding("utf8")

# label_dir = "/Users/lairf/Documents/RefineData/OcrTestLabelElse/"
# image_dir = "/Users/lairf/Documents/RefineData/OcrTestDataElse/"
# output_dir = "/Users/lairf/Documents/RefineData/xml/"

# label_dir = "/Users/lairf/Documents/LinkfaceTrainingData/VechileLicense2017/JPEGImages/label/"
# image_dir = "/Users/lairf/Documents/LinkfaceTrainingData/VechileLicense2017/JPEGImages/TestImages/"
# output_dir = "/Users/lairf/Documents/LinkfaceTrainingData/VechileLicense2017/output/"
# annotation_file = '/Users/lairf/Documents/LinkfaceTrainingData/VechileLicense2017/results/comp4_c95a72a1-eb26-4bed-955a-5bb13396e181_det_test_text.txt'

label_dir = sys.argv[1]
image_dir = sys.argv[2]
output_dir = sys.argv[3]

def iou(BBGT, bb):
    ixmin = np.maximum(BBGT[:, 0], bb[0])
    iymin = np.maximum(BBGT[:, 1], bb[1])
    ixmax = np.minimum(BBGT[:, 2], bb[2])
    iymax = np.minimum(BBGT[:, 3], bb[3])
    iw = np.maximum(ixmax - ixmin + 1., 0.)
    ih = np.maximum(iymax - iymin + 1., 0.)
    inters = iw * ih

    # union
    uni = ((bb[2] - bb[0] + 1.) * (bb[3] - bb[1] + 1.) +
            (BBGT[:, 2] - BBGT[:, 0] + 1.) *
            (BBGT[:, 3] - BBGT[:, 1] + 1.) - inters)

    overlaps = inters / uni
    ovmax = np.max(overlaps)
    jmax = np.argmax(overlaps)

    return ovmax, jmax

def subImage(image_file_name, boxes, texts):
    image_path = image_dir + image_file_name + '.jpg'
    img = cv2.imread(image_path)
    for i, box in enumerate(boxes):
        output_image = output_dir + image_file_name + str(i) + '.jpg'
        output_text = output_dir + image_file_name + str(i) + '.txt'

        left, top, right, bottom = box
        dest = img[top:bottom, left:right]#截取top:bottom行,left:right列
        res = cv2.resize(dest,(int((right-left)*28/(bottom-top)),28),interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(output_image, res)#dest)
        with open(output_text,"wt") as f:
            f.write(texts[i])

regions = {}
for line in fileinput.input(annotation_file):
    image_name, score, left, top, right, bottom = line.split()
    # print(image_name)
    if float(score) > 0.99:
        if regions.has_key(image_name):
            regions[image_name].append([int(float(left)), int(float(top)), int(float(right)), int(float(bottom))])
        else:
            regions[image_name] = [[int(float(left)), int(float(top)), int(float(right)), int(float(bottom))]]

print("Regions: {}".format(len(regions)))
print(regions['3999917_0'])

total_lines = 0
labeled_lines = 0
detected_lines = 0
true_detected_lines = 0

in_path = label_dir +  "*.json"
for json_file in glob.glob(in_path):
    removeFile = True
    with open(json_file) as file:
        text = file.read().decode("utf-8").strip()
        data = json.loads(text)
        imageFileName = data['image']['rawFilename']
        imagePath = image_dir + imageFileName
        lines = data['objects']['ocr']
        if os.path.exists(imagePath) and len(lines) >= 10:
            total_lines += len(lines)
            if regions.has_key(imageFileName[:-4]):
                removeFile = False
                boxes = regions[imageFileName[:-4]]
                detected_lines += len(boxes)
                outboxes = []
                outtexts= []
                for line in lines:
                    if line.has_key('attributes') and line['attributes'].has_key('content'):
                        text = line['attributes']['content']['value']
                        left = int(line['position']['left'])
                        top = int(line['position']['top'])
                        right = int(line['position']['right'])
                        bottom = int(line['position']['bottom'])

                        labeled_lines += 1
                        percent, pos = iou(np.asarray(boxes), [left, top, right, bottom])
                        if percent < 0.3:
                            print(line)
                        else:
                            outboxes.append(boxes[pos])
                            outtexts.append(text)
                            true_detected_lines += 1
                # subImage(imageFileName[:-4], outboxes, outtexts)
    if removeFile:
        os.remove(json_file)

print("total:", total_lines)
print("labeled:", labeled_lines)
print("detected:", detected_lines)
print("true_detected:", true_detected_lines)
print("precise:", true_detected_lines*1.0/detected_lines)
print("recall:", true_detected_lines*1.0/labeled_lines)
                    