# Guide to Fuzz Testing Daml Contracts

Fuzzing, or property-based testing, is a powerful technique for finding bugs and edge cases in your smart contracts. Instead of writing individual examples, you define general properties or invariants that your code should always satisfy. The testing framework then generates hundreds or thousands of random inputs to try and find a counterexample that breaks your property.

This approach is highly effective at uncovering subtle bugs related to ordering, unexpected values, and complex interactions that are difficult to predict and write explicit tests for. This guide will walk you through using the `Testing.Fuzzer` module to write robust property tests for your Daml contracts.

## 1. What is a Property?

A property is a high-level specification about your code's behavior. It's a function that takes randomly generated inputs and asserts that some invariant holds true. If the assertion ever fails, the fuzzer has found a bug and will report the exact inputs that caused the failure.

Good properties often check for invariants like:

-   **Conservation of value:** The total amount of a token in a system should remain constant after an internal transfer.
-   **Idempotence:** Performing the same action twice has the same effect as performing it once.
-   **State machine correctness:** A contract can only transition between valid states.
-   **Absence of deadlocks:** It should never be possible to get contracts into a state where no further actions can be taken.
-   **Symmetry:** If Alice can pay Bob, then Bob should (under similar conditions) be able to pay Alice.

## 2. Setting Up a Fuzz Test

Fuzz tests are written as regular `Daml.Script` tests. This allows you to leverage the full power of the script runner for setting up ledger state, allocating parties, and submitting transactions.

Here's the basic structure of a test file `daml/Test/MyContractFuzz.daml`:

```daml
module Test.MyContractFuzz where

import Daml.Script
import Testing.Fuzzer
import MyProject.MyContract -- Import the contract you want to test

-- Your fuzz tests will be defined as Daml Script actions.
fuzz_iou_transfer_preserves_value : Script ()
fuzz_iou_transfer_preserves_value = script do
  -- 1. Setup: Allocate parties, create initial contracts, etc.
  alice <- allocateParty "Alice"
  bob <- allocateParty "Bob"
  charlie <- allocateParty "Charlie"

  -- 2. Define the property you want to test.
  -- ...

  -- 3. Run the fuzzer.
  fuzz 100 "IOU transfers should preserve total value" do
    -- ...
    return ()
```

You can run this test like any other Daml Script test:

```sh
dpm test --files daml/Test/MyContractFuzz.daml
```

## 3. The `forAll` Function

The core of the fuzzing library is the `forAll` function. It takes two arguments:

1.  A `Gen a`: A **generator** for random values of type `a`.
2.  A property `(a -> Script ())`: A function that takes a generated value of type `a` and runs a script to check an invariant. The script should succeed if the property holds and fail (e.g., with `assert`) if it is violated.

Let's write a simple test for an `Iou` contract. The property we want to check is that after a transfer, the total value held by the issuer and the new owner is the same as the value held by the issuer and the original owner.

```daml
-- In MyProject/MyContract.daml
template Iou
  with
    issuer: Party
    owner: Party
    amount: Decimal
    currency: Text
  where
    signatory issuer, owner

    choice Transfer : ContractId Iou
      with
        newOwner : Party
      controller owner
      do
        create this with owner = newOwner
```

```daml
-- In Test/MyContractFuzz.daml
module Test.MyContractFuzz where

import Daml.Script
import Testing.Fuzzer
import MyProject.MyContract
import DA.Assert

fuzz_iou_transfer_preserves_value : Script ()
fuzz_iou_transfer_preserves_value = script do
  issuer <- allocateParty "Issuer"
  alice <- allocateParty "Alice"
  bob <- allocateParty "Bob"

  let
    -- Generator for a random positive IOU amount up to 1,000,000.
    genAmount = genDecimalRange 0.01 1_000_000.0

    -- The property we want to check.
    -- It takes a randomly generated amount.
    property (initialAmount : Decimal) = do
      -- Setup specific to this test run
      aliceIouCid <- submit alice do createCmd Iou with issuer, owner = alice, amount = initialAmount, currency = "USD"

      -- Exercise the choice to transfer the Iou
      submit alice do exerciseCmd aliceIouCid Transfer with newOwner = bob

      -- Verification: Check that the total value is preserved.
      -- The new IOU should have the same amount.
      [(_, bobIou)] <- query @Iou bob
      assertMsg "Amount should be unchanged after transfer" (bobIou.amount == initialAmount)
      assertMsg "New owner should be Bob" (bobIou.owner == bob)

      -- Check that Alice no longer holds the IOU
      aliceIous <- query @Iou alice
      assertMsg "Alice should have no IOUs" (null aliceIous)

      return ()

  -- Run the fuzzer with the generator and the property.
  -- This will run 100 times with different amounts.
  fuzz 100 "IOU transfers should preserve total value" do
    forAll genAmount property
```

## 4. Built-in Generators

`Testing.Fuzzer` provides a variety of generators for common Daml types.

| Generator               | Description                                           | Example Usage                     |
| ----------------------- | ----------------------------------------------------- | --------------------------------- |
| `genInt`                | Generates any `Int`.                                  | `forAll genInt \i -> ...`          |
| `genIntRange min max`   | Generates an `Int` within the inclusive range.        | `forAll (genIntRange 1 10) \i -> ...` |
| `genDecimal`            | Generates any `Decimal`.                              | `forAll genDecimal \d -> ...`      |
| `genDecimalRange min max` | Generates a `Decimal` within the inclusive range.     | `forAll (genDecimalRange 0.0 1.0) \d -> ...` |
| `genBool`               | Generates `True` or `False`.                          | `forAll genBool \b -> ...`         |
| `genParty parties`      | Picks a random `Party` from a given list.             | `forAll (genParty [alice, bob]) \p -> ...` |
| `genElement elems`      | Picks a random element from a list.                   | `forAll (genElement ["USD", "EUR"]) \c -> ...` |
| `genConstant val`       | Always "generates" the same constant value.           | `forAll (genConstant 42) \i -> ...` |
| `genText len`           | Generates random alphanumeric `Text` of a given length.| `forAll (genText 10) \t -> ...` |

## 5. Creating Custom Generators

You can easily combine simple generators to build complex ones for your custom data types. This is done using `do` notation, just like in `Script`.

Imagine you have a `TradeProposal` data type:

```daml
data TradeProposal = TradeProposal
  with
    buyer: Party
    seller: Party
    price: Decimal
    quantity: Int
```

You can create a generator for it like this:

```daml
genTradeProposal : Party -> [Party] -> Gen TradeProposal
genTradeProposal seller counterparties = do
  buyer <- genParty counterparties
  price <- genDecimalRange 10.0 1000.0
  quantity <- genIntRange 1 100
  return TradeProposal with ..
```

Here's how you'd use it in a test:

```daml
fuzz_trade_proposal : Script ()
fuzz_trade_proposal = script do
  exchange <- allocateParty "Exchange"
  traders <- mapA (\i -> allocateParty ("Trader" <> show i)) [1..5]

  fuzz 100 "Trade proposals are valid" do
    forAll (genTradeProposal exchange traders) \proposal -> do
      -- script to test the proposal
      assert (proposal.buyer /= proposal.seller)
      -- ... more interesting tests
      return ()
```

## 6. Reproducibility and Shrinking

When a fuzz test fails, the framework does two important things:

1.  **Reports the Seed:** It prints the random seed used for the run. You can use `fuzzWith` and provide this seed to reproduce the exact same failing run locally for debugging.

    ```daml
    let config = FuzzConfig with numRuns = 100, seed = Some 12345
    fuzzWith config "My test description" do
      -- ...
    ```

2.  **Shrinks the Input:** The framework automatically tries to find the *simplest possible input* that still causes the failure. For example, if a test fails with a list of 50 elements, the shrinker might find that the failure actually occurs with a specific list of just 2 elements. This makes debugging dramatically easier.

## 7. Stateful Fuzzing

The most powerful application of fuzzing is for testing complex, multi-step workflows. This is known as stateful or model-based property testing.

The idea is to:

1.  Define a set of possible **actions** a user can take in your system.
2.  Create a generator that produces a random *sequence* of these actions.
3.  Write a property that executes this sequence of actions against the ledger.
4.  After each step, or at the very end, check that the system-wide invariants still hold.

### Example: A Simple Auction

Consider a simple auction workflow: `Open` auction, `PlaceBid`, `Close` auction.

```daml
-- 1. Define the actions
data Action
  = OpenAuction { seller : Party, item : Text, startingPrice : Decimal }
  | PlaceBid { bidder : Party, bidPrice : Decimal }
  | CloseAuction { closer : Party }

-- 2. Create a generator for a sequence of actions
genActions : [Party] -> [Text] -> Gen [Action]
genActions parties items =
  genList (genAction parties items)

genAction : [Party] -> [Text] -> Gen Action
genAction parties items =
  -- Use genElement to choose which type of action to generate
  genElement
    [ do
        seller <- genParty parties
        item <- genElement items
        price <- genDecimalRange 1.0 100.0
        return $ OpenAuction with seller, item, startingPrice = price
    , do
        bidder <- genParty parties
        price <- genDecimalRange 100.0 1000.0
        return $ PlaceBid with bidder, bidPrice = price
    , do
        closer <- genParty parties
        return $ CloseAuction with closer
    ]

-- 3. Write the property to execute the actions
fuzz_auction_workflow : Script ()
fuzz_auction_workflow = script do
  -- Setup parties
  auctioneer <- allocateParty "Auctioneer"
  bidders <- mapA (\i -> allocateParty ("Bidder" <> show i)) [1..3]
  let parties = auctioneer :: bidders
  let items = ["Painting", "Vase", "Car"]

  fuzz 50 "Auction workflow invariants" do
    forAll (genActions parties items) \actions -> do
      -- This is the "model" of our state, kept locally in the script
      mutable mayAuctionCid : Optional (ContractId Auction) <- return None
      mutable highestBid : Decimal <- return 0.0

      -- Execute the sequence of actions
      forA_ actions \action ->
        case action of
          OpenAuction{..} -> do
            -- Try to open an auction. This may or may not succeed.
            -- We use `submitMustFail` or checks to handle expected failures.
            when (isNone mayAuctionCid) do
              cid <- submit seller do createCmd Auction with ..
              mayAuctionCid := Some cid
              highestBid := startingPrice
            return ()

          PlaceBid{..} -> do
            case mayAuctionCid of
              None -> return () -- Cannot bid if no auction
              Some cid ->
                -- We only submit a valid bid to avoid testing trivial failures.
                -- Fuzzing is for finding *unexpected* failures.
                when (bidPrice > highestBid) do
                  submit bidder do exerciseCmd cid PlaceBid with ..
                  highestBid := bidPrice
                return ()

          CloseAuction{..} -> do
            -- ... similar logic for closing

      -- 4. Final Verification
      -- After the sequence, check system-wide invariants.
      -- e.g., query all contracts and check for consistency.
      -- For example, there should be at most one `Auction` contract active.
      allAuctions <- query @Auction auctioneer
      assertMsg "At most one active auction is allowed" (length allAuctions <= 1)
```

This stateful approach can uncover incredibly complex bugs, such as race conditions or invariant violations that only occur after a very specific sequence of operations.