import time, requests, statistics

URL = "http://127.0.0.1:8000/signal?symbol=XYZ"
times = []

for _ in range(1000):
    t0 = time.perf_counter()
    requests.get(URL)
    times.append((time.perf_counter() - t0)*1000)

mean = statistics.mean(times)
p95 = statistics.quantiles(times, n=100)[94]
print(f"Mean latency: {mean:.2f} ms")
print(f"P95 latency: {p95:.2f} ms")
