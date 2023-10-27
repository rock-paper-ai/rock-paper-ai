import cv2
import cvzone

# cap = cv2.VideoCapture(0) #id number 0?
# while True:
#     success, img = cap.read()
#     cv2.imshow("Image", img)
#     cv2.waitKey(1) #delay of 1 milisecond

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)

rval, frame = vc.read()

while True:

  if frame is not None:
     cv2.imshow("preview", frame)
  rval, frame = vc.read()

  if cv2.waitKey(1) & 0xFF == ord('q'):
     break

