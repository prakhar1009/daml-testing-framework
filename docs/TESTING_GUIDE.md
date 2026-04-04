# Daml Testing Framework — Guide

## Running Built-in Daml Tests
```bash
daml build
daml test --all
```

## Using the Extended Framework Runner
```bash
# Run all tests in a DAR with parallel execution
python3 -m dtf run .daml/dist/myapp.dar --workers 8

# Generate an HTML report
python3 -m dtf run .daml/dist/myapp.dar --json --out results.json
python3 dtf/reporter.py results.json --out report.html
```

## Writing Property Tests in Daml
```haskell
import Framework.PropertyTests

myProp : Script ()
myProp = runProperty $ intProperty
  "amount always positive"
  (\n -> n * n >= 0)
```

## Fuzz Testing
```bash
python3 dtf/fuzzer.py "MyModule:MyTemplate" --count 200
```
