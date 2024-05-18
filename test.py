import requests


def test():
    response = requests.post('http://localhost:10006/generate', json={"prompt": "a", "seed": 0, "pipeline_type": "txt2img"})
    print(response.json())

def run_concurrently():
    import threading
    for _ in range(100):
        threading.Thread(target=test).start()

if __name__ == "__main__":
    run_concurrently()