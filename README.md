[//]: # (# PRS-Test)
# Human-centered In-building Embodied  Delivery Benchmark
## [PRS Challenge](https://prsorg.github.io/challenge) hosted on [CVPR 2024 Embodied AI Workshop](https://embodied-ai.org/)

## Quick Start

Follow these steps to quickly set up and run the PRS delivery task version:

1. Clone the PRS demo repository:  
```
git clone https://github.com/PRS-Organization/prs-delivery.git
```  
2. Ensure you have a Python virtual environment (Python version >= 3.9) activated.

3. Install the required Python packages:  
```
pip install -r prs_requirements.txt
```
4. Download the Unity executable file (Ubuntu version) from [PRS executable program](https://huggingface.co/datasets/xzq1999/prs-env/tree/main).

5. Extract the `prs_unity_demo.rar` file into the project folder:  
```
unzip PRS_Ubuntu_0.3.0.zip
```   
Note: This should create a `unity` folder. Give it necessary permissions:  
```
sudo chmod 777 -R unity
```
6. Start running the demo:  
```
python prs_demo.py
```     
or start with only unity application: 
``` 
bash start.sh 
```
7. If you encounter a port occupation error, clean up occupied ports:  
```
bash clean_port.sh
```
8. Manual start: ```PrsEnv(start_up_mode=0)``` after running the Python script, you can open another terminal and execute ```unity/start.sh``` or directly run `unity/PRS.x86_64`.

9. Runing on the headless server without rendering initialization ```PrsEnv(rendering=0)```.

10. Wait a few seconds for Unity to render the graphics. In Unity, you can control the camera movement using the keyboard keys W, A, S, D, Q, and E. Robot control using the keyboard keys I R, F J, O P, K L, G H, N M, Z X, V B. Switch perspectives using C, accelerate time using numeric keypad 123456789.

11. To close the demo, first close the Unity program (or press Esc), then stop the Python program (Ctrl+C or Ctrl+Z), and finally run:  
 ```
bash clean_port.sh
 ```  
Note: Or use ```prs.finish_env()``` to end PRS environment in Python script.

12. To get started with the Delivery Task Dataset, simply run the following command in your terminal:

```
python task_evaluation.py
```
This will initiate the evaluation process using the dataset.

If you want to run baseline method, please install ```transformers==4.40.2 ```, ```torch==2.0.1```, ```openai==1.30.5```. And fill in the API-key in the ```robot\llm_process.py```.
We utilize [Grounding DINO](https://github.com/IDEA-Research/GroundingDINO) to achieve zero-shot object detection with text prompt, you can replace it with others, e.g. [Grounded SAM](https://github.com/IDEA-Research/Grounded-Segment-Anything).

Save the result and submit the json to Eval AI leaderboard.

## More API Guidance
[NPC API](document/api.md)

[//]: # (input your API key for LLM service)

[//]: # (download vision model for object detect)

[//]: # (python task evaluation py)

[//]: # (save the result &#40;save=1&#41;)

[//]: # (submit the json to Eval AI leaderboard)

[//]: # (cite us contact us project homepage)

[//]: # (long term leaderboard for delivery)
