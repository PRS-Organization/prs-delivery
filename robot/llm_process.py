# import openai
from matplotlib import pyplot as plt
from openai import OpenAI
# from zhipuai import ZhipuAI
import cv2
import base64
import io
from PIL import Image, ImageDraw
from robot.object_detection import *


client = OpenAI(
#     api_key=os.environ.get("OPENAI_API_KEY")
)
grounding_dino = GroundingDino()


def object_detect_module(image, text='the human'):
    if text[-1] != '.':
        text = text + '.'
    result = grounding_dino.predict(image, text)
    return result


def lmm_interaction(content, image):
    image = Image.fromarray(image)
    image_file = io.BytesIO()
    image.save(image_file, format='PNG')
    encoded_string = base64.b64encode(image_file.getvalue()).decode()
    response = client.chat.completions.create(
        model="gpt-4o",  # Fill in the name of the model that needs to be called
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": content
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_string}"
                      }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    res = response.choices[0].message.content
    return res


def llm_interaction(content='Hello World!', temperature=0.9):
    response = client.chat.completions.create(
        model="gpt-4-turbo",  #   gpt-3.5-turbo-0125
        messages=[
            {"role": "user", "content": content}
        ],
    )
    res = response.choices[0].message.content
    return res


if __name__ == '__main__':
    im = cv2.imread('example.jpg')
    # print(im.shape)
    mat = object_detect_module(im, 'the water bottle.')
    plt.imshow(mat)
    plt.show()