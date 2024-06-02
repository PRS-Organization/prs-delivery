from matplotlib import pyplot as plt
from transformers import AutoProcessor, GroundingDinoForObjectDetection
from PIL import Image
import requests
import torch
import numpy as np
import cv2


class GroundingDino(object):
    def __init__(self):
        self.processor = AutoProcessor.from_pretrained("IDEA-Research/grounding-dino-tiny")
        self.model = GroundingDinoForObjectDetection.from_pretrained("IDEA-Research/grounding-dino-tiny")

    def predict(self, rgb_image, text):
        image = Image.fromarray(rgb_image)
        inputs = self.processor(images=image, text=text, return_tensors="pt")
        outputs = self.model(**inputs)
        # convert outputs (bounding boxes and class logits) to COCO API
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.image_processor.post_process_object_detection(
            outputs, threshold=0.35, target_sizes=target_sizes
        )[0]
        item, score_max = None, 0
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [round(i, 2) for i in box.tolist()]
            # print(f"Detected {label.item()} with confidence " f"{round(score.item(), 3)} at location {box}")
            if round(score.item(), 3) > score_max:
                score_max = round(score.item(), 3)
                item = box
        if item is None:
            return None
        h, w = rgb_image.shape[0], rgb_image.shape[1]
        box = item
        top_left = (round(box[0]), round(box[1]))
        bottom_right = (round(box[2]), round(box[3]))
        # print(bottom_right, top_left, h, w)
        cv2.rectangle(rgb_image, top_left, bottom_right, (255, 0, 0), 2)
        mat = np.zeros((h, w))
        mat[top_left[1]:bottom_right[1] + 1, top_left[0]:bottom_right[0] + 1] = 1
        return mat


if __name__ == "__main__":
    grounding_dino = GroundingDino()
    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    pil_image = Image.open(requests.get(url, stream=True).raw)
    image = np.array(pil_image)
    res = grounding_dino.predict(image, 'cat.')
    plt.imshow(res)
    plt.show()
    print(np.sum(res) / (480 * 640))