# Kedge business plan

Built with [cfo.ai](https://cfo.ai) (Ari, AI CFO) on Oct 10, 2026, during neatHack. The 24-month operating model runs Oct 2026 – Sep 2028. Every figure below comes from cfo.ai's exported model: [Base](business-plan-base.xlsx) and [Upside](business-plan-upside.xlsx).

## What we sell

Kedge supervises AI coding agents that fix failing Dependabot/Renovate dependency PRs. When the agent cheats (deletes or skips tests, edits files outside the plan, claims success it didn't earn), Kedge rolls back to the last good commit and makes it retry. Customers pay only when a PR goes green.

## Pricing

**$10 per green PR**, usage-based. Failed attempts are free to the customer.

## Unit costs

| Item | Per green PR | Source |
|---|---|---|
| Model spend | **$0.45** | Batch runs: 62,391 tokens per green PR on average (3 green PRs: 29,658 / 78,258 / 79,257 tokens). Priced on Claude Sonnet 5.5 ($2 / $10 per M tokens, about 95% input) ≈ $0.15, plus a Haiku 4.5 planning call ≈ $0.005. Grossed up for failed attempts at the batch's ~60% green rate |
| Payment processing | $0.30 (3%) | cfo.ai default |
| Infrastructure | $0 | Runs on the customer's own CI |
| **Gross margin** | **92.5%** | |

## Assumptions

- 60% of submitted PRs go green, and only green PRs are billed.
- 2 founders, unpaid for the first 6 months, then $4,000/month each from Apr 2027.
- Software and tools: $200/month.
- Starting cash: $0.

## Scenarios

| | Base | Upside |
|---|---|---|
| Teams | 5 → 50 by Sep 2027 | 5 → 200 by Mar 2028 |
| PRs per team per month | 20 | 30 |
| Green PRs per month at full ramp | 600 | 3,600 |
| Revenue in final month | **$6,000** | **$36,000** |
| Gross margin | 92.5% | 92.5% |
| Operating income after founder salaries | −$2,650/month at full ramp | Positive every month |
| Break-even | Not within 24 months (needs 74 active teams) | Profitable from Apr 2027, the first salaried month |
| Raise needed | **$60k in Apr 2027** (minimum $45,570) | None |
| Lowest cash point | $355 (Oct 2026) | $632 (Oct 2026) |
| Cash at month 24 (Sep 2028) | $14,430 | $358,192 |
| Runway at month 24 | 5 months | Self-funding |

## What the numbers say

1. **The unit economics work.** Each green PR earns $10 and costs about $0.75 to deliver, so gross margin is 92.5%.
2. **Volume decides the business, not price.** At 50 teams, Kedge covers its tools but not two salaries. Break-even needs 74 teams at 20 PRs/month. The Upside case clears that in its first salaried month.
3. **The Base case needs a small raise.** $60k in Apr 2027 carries it through Sep 2028 with 5 months of runway left. That gives us time to reach the 74-team break-even, or to raise prices for larger teams.

## What would change the plan

- **Lower model cost.** The batch ran on a free model. Every paid-model number here is an estimate from measured token counts, and it gets replaced once paid runs exist.
- **Green rate.** At 60%, only green PRs are billed, so a higher green rate raises revenue with no extra cost.
- **Price.** $10 is a placeholder from the plan. A human fixing one failing dependency PR costs far more in engineer time.
