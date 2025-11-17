"""Simple performance test that measures response times for dashboard and transactions endpoints.
Run after bulk_load to simulate load.
"""
import time
import requests
BASE = 'http://127.0.0.1:5000'
ENDPOINTS = ['/dashboard', '/transactions?page=1&per_page=50']


def measure():
    times = {}
    for e in ENDPOINTS:
        t0 = time.time()
        r = requests.get(BASE + e)
        t1 = time.time()
        times[e] = {'status': r.status_code, 'elapsed': t1 - t0}
    return times


if __name__ == '__main__':
    print('Measuring endpoints on', BASE)
    for i in range(5):
        print(measure())
