---
name: energy-markets
description: Primer on European short-term electricity markets (day-ahead, intraday, balancing) and how they map onto odys. Use before writing docs, examples or model features that involve markets, bidding, scenarios or stage-fixed decisions, so every claim about timing and about what is known when is right.
---

# Energy markets

odys plans a portfolio that trades on electricity markets. Its readers are energy traders and planners: a wrong claim about when a market closes, or what is known when a bid goes in, breaks their trust in the whole page. This playbook holds the facts the docs rely on, and the rules for using them.

## Checklist

- [ ] For every market a page uses, say when the decision is taken and what is known at that point (§2).
- [ ] Check each price in each `Scenario` against that: a price that's uncertain when the bid goes in differs between scenarios (§3).
- [ ] Check every timing word ("tonight", "tomorrow morning", "before it clears") against §1.
- [ ] State a modelling limit only as odys's limit (§4), never as how the market works.
- [ ] For any fact not in this playbook, find a source (an exchange, the NEMO Committee, ENTSO-E, ACER) or ask the maintainer. Never fill a gap with a guess.

## 1. The sequence of markets

European power is traded in a sequence of markets, each closing closer to delivery. Times are CET/CEST, for delivery day D.

| Market | What it is | Gate closure | What you learn |
| ------ | ---------- | ------------ | -------------- |
| Day-ahead (SDAC) | One coupled auction for every hour of D, in 15-minute steps since delivery day 1 October 2025 | 12:00 on D-1 | The clearing prices and your accepted volumes. Preliminary results are published no earlier than 12:55, and by the 14:20 full-decoupling deadline at the latest |
| Intraday auctions (SIDC IDAs) | Three coupled auctions | IDA1 at 15:00 on D-1 and IDA2 at 22:00 on D-1, both covering all of D; IDA3 at 10:00 on D, covering 12:00 to 24:00 | Prices and volumes of each auction |
| Continuous intraday (SIDC) | Bilateral, order-by-order trading up to shortly before delivery | Rolling, per delivery period. Cross-zonal continuous trading pauses around each IDA gate closure | Each trade's price, as it happens |
| Balancing and imbalance settlement | The TSO balances the system in real time; deviations from your position are settled at the imbalance price | After delivery | The imbalance price, after the fact |

Sources: [SDAC 15-minute MTU go-live](https://bsp-southpool.com/2025/09/12/market-coupling-steering-committee-confirms-go-live-15-minute-mtu-sdac-delivery-day-1), [SDAC timings (EPEX SPOT)](https://www.epexspot.com/sites/default/files/download_center_files/Day-Ahead%20MRC%20Processes%20(02.07.2019).pdf), [SDAC fallback manual (NEMO Committee)](https://www.nemo-committee.eu/assets/files/sdac-fallback-manual.pdf), [SIDC intraday auctions (Nord Pool)](https://support.nordpoolgroup.com/support/solutions/articles/8000111575-about-the-sidc-intraday-auctions-idas-), [SIDC (OTE)](https://ote-cr.cz/en/short-term-markets/market-coupling-intraday-market/sidc).

National details differ (local intraday auctions, balancing products, imbalance pricing). Don't generalize from one country to Europe, or the other way round.

## 2. What is known at each decision point

A plan is made at one moment, and what's uncertain depends on that moment:

- **Before the day-ahead gate closure** (D-1 morning): the day-ahead prices, the intraday prices and tomorrow's wind and solar are all uncertain, and they move together: a windy day usually brings lower prices on both markets. The day-ahead volume is the decision. Intraday trades and dispatch come later, so they can adapt to the future that happens.
- **After day-ahead clearing**: the day-ahead prices and your accepted volumes are known. The day-ahead position is no longer a decision, it's a fixed input. What remains is intraday trading and dispatch, against forecasts that keep improving up to delivery.
- **On the day**: forecasts are close to the outcome. What's left is continuous intraday, and the imbalance against your final position.

A bid is never placed with knowledge of its own market's clearing price. "The day-ahead prices are known" and "we bid day-ahead" can't both be true for the same run.

## 3. How this maps onto odys

- **One run is one decision point.** The scenarios describe what's uncertain at that point, and each one is a full possible future.
- **`stage_fixed=True` marks a decision taken before the uncertainty resolves**, typically day-ahead in a run made before its gate closure. Its trades are the same in every scenario ([NA-1](../../../docs/formulation/non_anticipativity.md)). Every other decision is second-stage: it adapts to each scenario, as if the future were known.
- **Every price that's uncertain at the decision point varies by scenario.** A `PriceProfile` that's identical in every scenario says that price is known when you plan. For a stage-fixed market, that contradicts §2, unless the page says why (for example, a deliberate simplification to isolate another effect).
- **odys is a price taker.** Prices are inputs: the volume you trade doesn't move them.
- **Trades are powers.** A market volume is MW, held for the whole step, like every other power in odys.

## 4. Modelling limits to state honestly

These are odys's limits, not features of the markets. Say them where they matter, on the formulation page that owns the rule:

- **A stage-fixed trade is a price-independent bid**: one volume per step, accepted whatever price the market clears at. Real day-ahead bids are price-quantity curves, and odys doesn't model them.
- **No input for an existing position.** A run after day-ahead clearing can't take the day-ahead position as a fixed input yet.
- **No balancing markets** ([#166](https://github.com/ramirocrc/odys/issues/166)), **and no imbalance**: second-stage decisions meet every scenario exactly, so there is no imbalance price or penalty.
- **One price per market and step**, for buying and selling alike: no spreads or fees ([#169](https://github.com/ramirocrc/odys/issues/169)).
- **Generator commitment is second-stage**: a unit can be on in one scenario and off in another ([#153](https://github.com/ramirocrc/odys/issues/153)).

## 5. Writing about markets

- Name the moment: "before the day-ahead gate closure", "once day-ahead has cleared". Avoid loose times like "tonight" or "tomorrow morning", which don't match the market clock.
- Make prices consistent with the story: if the wind drives the scenarios, it drives both markets' prices too.
- When an example simplifies a market (one hour, a single intraday market, perfect information on the day), say so in one sentence.
- Use the market names as traders do: day-ahead (SDAC), intraday (SIDC), balancing. Write them out the first time on a page.

When in doubt about any market fact, ask the maintainer before writing it.
