# src/cli.py
import json, time
from src.banker import is_safe_sequence
from src.dynamic_banker import dynamic_banker_loop

def load_input(path):
    with open(path) as f:
        return json.load(f)

def simple_request_generator(requests):
    # returns generator that yields next request or None
    for r in requests:
        yield r
    while True:
        yield None

def main():
    data = load_input("sample_inputs/sample1.json")
    alloc = data['allocation']
    maxm = data['max']
    avail = data['available']

    print("Safe sequence (standard):", is_safe_sequence(alloc, maxm, avail.copy()))

    # simulate dynamic: provide a list of requests arriving at checks
    # Example: single new process arrives with max [4,3,3]
    requests = [[4,3,3]]  # change as needed
    gen = simple_request_generator(requests)
    seq = dynamic_banker_loop(alloc.copy(), maxm.copy(), avail.copy(), gen)
    print("Safe sequence (dynamic):", seq)

if __name__ == "__main__":
    main()
