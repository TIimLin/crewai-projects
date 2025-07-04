#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from my_first_crew.crew import MyFirstCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    # 將 'file_path' 指向您要分析的檔案
    # 這個路徑是相對於容器內 /app/my_first_crew 的路徑
    inputs = {
        'destination': '日本大阪',
        'duration': '7天',
        'interests': '風景、美食、文化',
        'start_date': '2025-07-07',
        'end_date': '2025-07-13',
    }
    
    try:
        MyFirstCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'destination': '日本大阪',
        'duration': '7天',
        'interests': '風景、美食、文化',
        'start_date': '2025-07-10',
        'end_date': '2025-07-13',
    }
    try:
        MyFirstCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        MyFirstCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'destination': '日本大阪',
        'duration': '7天',
        'interests': '風景、美食、文化',
        'start_date': '2025-07-07',
        'end_date': '2025-07-13',
    }
    
    try:
        MyFirstCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
