# test_video_reader.py - Simple working version

from modules.input.video_reader import get_frame, preprocess_frame
import cv2

print('🚀 Starting Video Input Test... Press q to quit')

frame_count = 0

while True:
    raw_frame = get_frame()
    if raw_frame is None:
        print('✅ Video finished!')
        break
    
    processed_frame = preprocess_frame(raw_frame)
    frame_count += 1
    
    cv2.imshow('Preprocessed Frame (for Developer 2)', processed_frame)
    print(f'Frame {frame_count} | Shape: {processed_frame.shape}')
    
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
print(f'✅ Test completed! {frame_count} frames processed.')
