# import necessary packages
from imutils.video import VideoStream
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2

# build the argument parser
ap = argparse.ArgumentParser()
ap.add_argument("-e", "--encodings", required=True, help="path to serialized db of facial encodings")
ap.add_argument("-o", "--output", type=str, help="path to output video")
ap.add_argument("-y", "--display", type=int, default=1, help="whether or not to display output frame to screen")
ap.add_argument("-d", "--detection-method", type=str, default="cnn", help="detection model to use: either `hog` or `cnn`")
args = vars(ap.parse_args())

# load known faces and encodings
print("[INFO] loading encodings")
data  = pickle.loads(open(args["encodings"],"rb").read())

# initialise video stream and pointer
# allow the camera to warm up
print("[INFO] starting video stream")
vs = VideoStream(src=0).start()
writer = None
time.sleep(2)

# loop over the frames from the video file stream
while True:
    
	# grab the frame from the threaded video stream
	frame = vs.read()
	
	# convert the input frame from BGR to RGB 
    # resize it to have a width of 750px (to speedup processing)
	rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	rgb = imutils.resize(frame, width=750)
	r = frame.shape[1] / float(rgb.shape[1])
 
	# detect the (x, y) coordinates of the bounding boxes
	# corresponding to each face in the input frame
    # compute the facial embeddings for each face
	boxes = face_recognition.face_locations(rgb, model=args["detection_method"])
	encodings = face_recognition.face_encodings(rgb, boxes)
 
    # initialise the list of names
	names = []
 
    # loop over the facial embeddings
	for encoding in encodings:
     
		# attempt to match each face in the input image to our known encodings
		matches = face_recognition.compare_faces(data["encodings"], encoding)
		name = "unknown"
  
		# check to see if we have found a match
		if True in matches:
      
			# find the indexes of all matched faces
            # then initialize a dictionary 
            # to count the number of times 
            # each face was matched
			matchedIdxs = [i for (i, b) in enumerate(matches) if b]
			counts = {}
   
			# loop over the matched indexes
            # maintain a count for each recognized face
			for i in matchedIdxs:
				name = data["names"][i]
				counts[name] = counts.get(name, 0) + 1
    
			# determine the recognized face with the largest number of votes 
            # (note: in the event of an unlikely tie python will select first entry in the dictionary)
			name = max(counts, key=counts.get)
		
		# update the list of names
		names.append(name)
  
		# loop over the recognised faces
		for ((top, right, bottom, left), name) in zip(boxes, names):
			
			# rescale face coordinates
			top = int(top * r)
			right = int(right * r)
			bottom = int(bottom * r)
			left = int(left * r)

			# draw the predicted face name on the image
			cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
			y = top - 15 if top - 15 > 15 else top + 15
			cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 0), 2)
 
			# if the video writer is none and 
   			# we are supposed to write video to disk
			# then initialise the writer
			if writer is None and args["output"] is not None:
				fourcc = cv2.VideoWriter_fourcc(*"MJPG")
				writer = cv2.VideoWriter(args["output"], fourcc, 20, (frame.shape[1], frame.shape[0]), True)
    
   			# if the writer is not none
      		# then write the frame with recognized faces to disk
			if writer is not None:
				writer.write(frame)
    
			# check to see if we are supposed to display the output frame to the screen
			if args["display"] > 0:
				cv2.imshow("Frame", frame)
				key = cv2.waitKey(1) & 0xFF
		
  				# if the 'q' key was pressed, break from the loop
				if key == ord("q"):
					break

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()

# check to see if the video writer point needs to be released
if writer is not None:
	writer.release()