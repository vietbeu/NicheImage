import requests
import httpx
import time


def test():
    start = time.time()
    with httpx.Client(timeout=100) as client:
        response = client.post('http://localhost:10006/generate', json={"prompt": "a", "seed": 0, "pipeline_type": "txt2img", "pipeline_params": {"num_inference_steps": 15}})
    end = time.time()
    print(f"Time taken: {end-start}")

def run_concurrently():
    import threading
    threads = []
    for i in range(10):
        thread = threading.Thread(target=test)
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
if __name__ == "__main__":
    run_concurrently()