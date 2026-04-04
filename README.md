# Daml Testing Framework

A comprehensive testing framework for Daml smart contracts with property-based
testing, scenario runners, and CI integration.

## Features
- Property-based testing (QuickCheck-style) for Daml contracts
- Scenario test runner with parallel execution
- Contract state assertion library
- Fuzz testing for edge cases
- HTML test report generation
- GitHub Actions integration

## Quick Start
```bash
daml build
daml test --all
# Or with the extended framework:
python3 -m dtf run tests/
```
