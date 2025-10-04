# chatGPT code

import cv2
import numpy as np

# Load segmented image (each object has a unique integer label)
segmented_img = cv2.imread("segmented.png", cv2.IMREAD_GRAYSCALE)

# Find contours
contours, hierarchy = cv2.findContours(segmented_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

# hierarchy has shape (1, num_contours, 4): [Next, Previous, First_Child, Parent]
hierarchy = hierarchy[0]  # simplify

objects = []

for idx, (cnt, hier) in enumerate(zip(contours, hierarchy)):
    obj = {
        "id": idx,
        "contour": cnt,
        "parent": int(hier[3]) if hier[3] != -1 else None,
        "children": []
    }
    objects.append(obj)

# Assign children
for obj in objects:
    if obj["parent"] is not None:
        objects[obj["parent"]]["children"].append(obj["id"])

# Example: print relationships
for obj in objects:
    print(f"Object {obj['id']} -> parent: {obj['parent']}, children: {obj['children']}")

import matplotlib.pyplot as plt

img_color = cv2.cvtColor(segmented_img, cv2.COLOR_GRAY2BGR)

for obj in objects:
    color = (0, 255, 0) if obj["parent"] is None else (0, 0, 255)
    cv2.drawContours(img_color, [obj["contour"]], -1, color, 2)

plt.imshow(cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB))
plt.show()
