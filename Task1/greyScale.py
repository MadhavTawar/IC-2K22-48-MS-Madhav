import cv2
import matplotlib.pyplot as plt
img = cv2.imread("sample.jpg")
if img is None:
	raise FileNotFoundError("Could not read sample.jpg")
# BGR order, not RGB!
print("shape :", img.shape)
# (height, width, 3)
print("dtype :", img.dtype)
# uint8 → values 0..255
print("min/max:", img.min(), img.max())
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print("gray shape:", gray.shape)
# (height, width) — channel gone
plt.subplot(1, 2, 1); plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); plt.axis('off')
plt.subplot(1, 2, 2); plt.imshow(gray, cmap='gray'); plt.axis('off')
plt.show()