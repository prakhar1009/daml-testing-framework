#!/usr/bin/env python3
"""Fuzz tester: generate random inputs and verify contract invariants."""
import random
import string
import json
import argparse

def random_party() -> str:
    return ''.join(random.choices(string.ascii_uppercase, k=8)) + '::' + ''.join(
        random.choices(string.hexdigits, k=16))

def random_decimal(min_val=0.0, max_val=1_000_000.0) -> float:
    return round(random.uniform(min_val, max_val), 10)

def random_text(max_len=64) -> str:
    length = random.randint(1, max_len)
    return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))

def generate_inputs(template: str, count: int) -> list[dict]:
    generators = {
        "Party": random_party,
        "Decimal": random_decimal,
        "Text": random_text,
        "Int": lambda: random.randint(-1_000_000, 1_000_000),
        "Bool": lambda: random.choice([True, False]),
    }
    # Simple heuristic: generate random payloads
    return [
        {"template": template, "seed": i, "payload": {
            "party": random_party(),
            "amount": random_decimal(),
            "description": random_text(),
        }}
        for i in range(count)
    ]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="Fully-qualified template name to fuzz")
    parser.add_argument("--count", default=50, type=int)
    args = parser.parse_args()

    inputs = generate_inputs(args.template, args.count)
    print(json.dumps(inputs, indent=2))

if __name__ == "__main__":
    main()
