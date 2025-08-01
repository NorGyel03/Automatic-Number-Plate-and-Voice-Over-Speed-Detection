import ast

import cv2
import numpy as np
import pandas as pd

from util import extract_numeric_values

car_speeds_dict = {}
MAX_REASONABLE_SPEED = 300  # in km/h


def draw_border(img, top_left, bottom_right, color=(0, 255, 0), thickness=10, line_length_x=200, line_length_y=200):
    x1, y1 = top_left
    x2, y2 = bottom_right

    cv2.line(img, (x1, y1), (x1, y1 + line_length_y), color, thickness)  # -- top-left
    cv2.line(img, (x1, y1), (x1 + line_length_x, y1), color, thickness)

    cv2.line(img, (x1, y2), (x1, y2 - line_length_y), color, thickness)  # -- bottom-left
    cv2.line(img, (x1, y2), (x1 + line_length_x, y2), color, thickness)

    cv2.line(img, (x2, y1), (x2 - line_length_x, y1), color, thickness)  # -- top-right
    cv2.line(img, (x2, y1), (x2, y1 + line_length_y), color, thickness)

    cv2.line(img, (x2, y2), (x2, y2 - line_length_y), color, thickness)  # -- bottom-right
    cv2.line(img, (x2, y2), (x2 - line_length_x, y2), color, thickness)

    return img


results = pd.read_csv('./speed_test_interpolated.csv')

# load video
video_path = './sample.mp4'
cap = cv2.VideoCapture(video_path)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Specify the codec
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter('./out.mp4', fourcc, fps, (width, height))

license_plate = {}
for car_id in np.unique(results['car_id']):
    max_ = np.amax(results[results['car_id'] == car_id]['license_number_score'])
    license_plate[car_id] = {'license_crop': None,
                             'license_plate_number': results[(results['car_id'] == car_id) &
                                                             (results['license_number_score'] == max_)][
                                 'license_number'].iloc[0]}
    cap.set(cv2.CAP_PROP_POS_FRAMES, results[(results['car_id'] == car_id) &
                                             (results['license_number_score'] == max_)]['frame_nmr'].iloc[0])
    ret, frame = cap.read()

    x1, y1, x2, y2 = ast.literal_eval(results[(results['car_id'] == car_id) &
                                              (results['license_number_score'] == max_)]['license_plate_bbox'].iloc[
                                          0].replace('[ ', '[').replace('   ', ' ').replace('  ', ' ').replace(' ',
                                                                                                               ','))

    license_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
    license_crop = cv2.resize(license_crop, (int((x2 - x1) * 400 / (y2 - y1)), 400))

    license_plate[car_id]['license_crop'] = license_crop

frame_nmr = -1

cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

# read frames
ret = True
while ret:
    ret, frame = cap.read()
    frame_nmr += 1
    if ret:
        df_ = results[results['frame_nmr'] == frame_nmr]
        for row_indx in range(len(df_)):
            # draw car
            car_x1, car_y1, car_x2, car_y2 = ast.literal_eval(
                df_.iloc[row_indx]['car_bbox'].replace('[ ', '[').replace('   ', ' ').replace('  ', ' ').replace(' ',
                                                                                                                 ','))
            draw_border(frame, (int(car_x1), int(car_y1)), (int(car_x2), int(car_y2)), (0, 255, 0), 25,
                        line_length_x=200, line_length_y=200)

            # Get the car ID
            car_id = df_.iloc[row_indx]['car_id']

            # Extract numeric values from the 'car_speed' column
            car_speed = str(df_.iloc[row_indx]['car_speed'])
            speed_values = extract_numeric_values(car_speed)

            # Filter unrealistic speed
            speed_values = [speed for speed in speed_values if speed <= MAX_REASONABLE_SPEED]

            # Update the dictionary with the car's speed values
            if car_id not in car_speeds_dict:
                car_speeds_dict[car_id] = []
            car_speeds_dict[car_id].extend(speed_values)

            # Convert average speed to a string and draw it on the frame
            if car_id in car_speeds_dict:
                average_speed = sum(car_speeds_dict[car_id]) / len(car_speeds_dict[car_id]) if len(
                    car_speeds_dict[car_id]) > 0 else 0

                if average_speed != 0:
                    average_speed_str = f" Speed: {average_speed:.2f} km/h"
                    # Adjust the font parameters for better appearance
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 1.5
                    font_thickness = 5
                    font_color = (255, 255, 255)  # White color

                    # Get the size of the text to center it properly
                    text_size = cv2.getTextSize(average_speed_str, font, font_scale, font_thickness)[0]
                    text_x = int(car_x1 - text_size[0] / 2)
                    text_y = int(car_y1 - 50)

                    # Draw the text with the updated font parameters
                    cv2.putText(frame, average_speed_str, (text_x, text_y), font, font_scale, font_color, font_thickness)


            # draw license plate
            x1, y1, x2, y2 = ast.literal_eval(
                df_.iloc[row_indx]['license_plate_bbox'].replace('[ ', '[').replace('   ', ' ').replace('  ',
                                                                                                        ' ').replace(
                    ' ', ','))
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 12)

            # crop license plate
            license_crop = license_plate[df_.iloc[row_indx]['car_id']]['license_crop']

            H, W, _ = license_crop.shape

            try:
                frame[int(car_y1) - H - 100:int(car_y1) - 100,
                int((car_x2 + car_x1 - W) / 2):int((car_x2 + car_x1 + W) / 2), :] = license_crop

                frame[int(car_y1) - H - 400:int(car_y1) - H - 100,
                int((car_x2 + car_x1 - W) / 2):int((car_x2 + car_x1 + W) / 2), :] = (255, 255, 255)

                (text_width, text_height), _ = cv2.getTextSize(
                    license_plate[df_.iloc[row_indx]['car_id']]['license_plate_number'],
                    cv2.FONT_HERSHEY_SIMPLEX,
                    4.3,
                    17)

                cv2.putText(frame,
                            license_plate[df_.iloc[row_indx]['car_id']]['license_plate_number'],
                            (int((car_x2 + car_x1 - text_width) / 2), int(car_y1 - H - 250 + (text_height / 2))),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            4.3,
                            (0, 0, 0),
                            17)

            except:
                pass

        out.write(frame)
        frame = cv2.resize(frame, (1280, 720))

        # cv2.imshow('frame', frame)
        # cv2.waitKey(0)

out.release()
cap.release()
