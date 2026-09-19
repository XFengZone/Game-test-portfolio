import requests
import time
from concurrent.futures import ThreadPoolExecutor

url = "http://httpbin.org/post"

def singleLogin(i):
    data={"username":f"test_{i}","password":"114514"}
    start=time.time()
    try:
        r=requests.post(url=url,json=data)
        end=time.time()
        return {"id":i,"status":r.status_code,"time": end - start}
    except Exception as e:
        return {"id": i, "status": "error", "time": -1}
def concurrent_login(n=100):
    result=[]
    start=time.time()
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures=[executor.submit(singleLogin,i) for i in range(n)]
        for f in futures:
            result.append(f.result())

    end=time.time()
    success = [r for r in result if r["status"] == 200]
    fail = [r for r in result if r["status"] != 200]

    times = [r["time"] for r in success]
    print(f"总请求数: {n}")
    print(f"成功数: {len(success)}, 失败数: {len(fail)}")
    print(f"总耗时: {end - start:.2f}秒")
    if times:
        print(f"平均响应时间: {sum(times) / len(times):.3f}秒")
        print(f"最大响应时间: {max(times):.3f}秒")
        print(f"最小响应时间: {min(times):.3f}秒")

concurrent_login(100)
