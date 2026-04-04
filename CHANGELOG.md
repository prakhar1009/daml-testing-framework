# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-05-21

### Added

- **Initial Project Scaffolding:** Set up the basic `daml.yaml`, directory structure, and `.gitignore`.
- **Property-Based Testing Module (`Daml.Test.Property`):**
  - Introduced `forAll` function to generate random test data.
  - Added basic generators for `Int`, `Decimal`, `Text`, `Party`, and `Time`.
  - Implemented `property` and `runProperty` functions to execute property tests within Daml Script.
- **Party Mocking Utilities (`Daml.Test.Mock`):**
  - `createMockParty`: Function to create a new `Party` for testing purposes without needing explicit allocation on a real ledger.
  - `submitAsMock`: A wrapper around `submit` that allows a test runner to submit commands on behalf of a mocked party.
- **Time Simulation (`Daml.Test.Time`):**
  - `setTime`: Sets the ledger's effective time to a specific `Time`.
  - `passTime`: Advances the ledger's effective time by a given duration (`RelTime`).
  - These functions are built on top of the Daml Script time functions for a more ergonomic testing API.
- **Fixture Management (`Daml.Test.Fixture`):**
  - `setup`: A higher-order function to encapsulate common contract and party setup logic, returning a record of created entities.
  - Example fixtures for common use cases like setting up user roles.
- **GitHub Actions Integration:**
  - Added a `.github/workflows/ci.yml` file.
  - The workflow automatically installs the Daml SDK, builds the project (`daml build`), and runs all tests (`daml test`).
- **Test Coverage Reporter (Experimental):**
  - Included a shell script (`scripts/coverage.sh`) to parse Daml test output and generate a simple text-based coverage summary.