import requests
import time
from concurrent.futures import ProcessPoolExecutor

url = "http://httpbin.org/post"

def single_login(i):
    data = {"username": f"player_{i}", "password": "123456"}
    start = time.time()
    try:
        r = requests.post(url, json=data, timeout=10)
        end = time.time()
        return {"id": i, "status": r.status_code, "time": end - start}
    except Exception as e:
        return {"id": i, "status": "error", "time": -1}

def concurrent_login(n=100):
    results = []
    start = time.time()
    with ProcessPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(single_login, i) for i in range(n)]
        for f in futures:
            results.append(f.result())
    end = time.time()

    success = [r for r in results if r["status"] == 200]
    times = [r["time"] for r in success]

    print(f"[多进程] 成功: {len(success)}, 总耗时: {end - start:.2f}秒")
    if times:
        print(f"平均响应时间: {sum(times) / len(times):.3f}秒")
        print(f"最大响应时间: {max(times):.3f}秒")
        print(f"最小响应时间: {min(times):.3f}秒")
if __name__ == "__main__":
    concurrent_login(100)
