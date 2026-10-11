# Business context and value

## How business banking works

Businesses use banking services to collect customer payments, pay suppliers and
employees, manage cash, and fund operations or investment. This project represents
six product categories:

| Product | Business need |
|---|---|
| Deposit accounts | Hold operating cash and receive or make payments. |
| Loans | Finance working capital or investment. |
| Credit cards | Support business purchases and short-term payment flexibility. |
| Merchant services | Accept customer payments. |
| Payroll services | Support employee payments. |
| Treasury services | Support cash and liquidity management. |

A banking relationship can involve several products. Understanding the customer's
operating cycle helps an RM discuss appropriate services and interpret changes.

Banks earn interest income and fees and incur funding, servicing, and credit
costs. The FDIC reports these categories in its
[bank income and expense tables](https://www.fdic.gov/analysis/quarterly-banking-profile/fdic-quarterly/2023-vol17-1/fdic-v17n1-4q2022.pdf).
The project's customer-level allocations are fictional teaching assumptions,
rather than a reproduction of bank accounting or pricing policies.

## What a relationship manager does

For this project, an RM is the person responsible for coordinating a portfolio
of business customer relationships. Responsibilities and authority vary by bank.
The workflow represented here includes:

- Understanding a business's operations, cash cycle, and financing needs.
- Preparing for customer conversations using relationship history.
- Investigating changes in balances, activity, and relationship economics.
- Discussing relevant services and coordinating with product specialists.
- Coordinating lending discussions with credit specialists and following up on
  customer concerns.

Commercial lending involves examining business finances and guiding applicants
through lending processes; see the
[BLS description of loan officer duties](https://www.bls.gov/OOH/business-and-financial/loan-officers.htm).
An RM's relationship role is broader than lending. This hub supports preparation
and prioritization; it does not assign credit approval authority.

## How the hub supports the business

| Page | Business question | Supported RM activity |
|---|---|---|
| Portfolio Overview | How is my portfolio performing? | Review balances, monthly bank profitability, concentration, product adoption, and deposit-decline indicators. |
| Customer 360 | What is changing in this relationship? | Prepare for a meeting using the customer's profile, product holdings, and financial history. |
| RM Opportunities | Which relationships deserve a conversation, and why? | Review explainable retention indicators and missing-product signals, then investigate customer needs. |

The potential value is a consistent view across products, quicker meeting
preparation, and a clearer starting point for customer outreach. The project
does not demonstrate measured revenue uplift, reduced attrition, or time savings.

## Reading the financial measures

Customer operating revenue means the fictional business's sales. Customer
operating profit is sales minus operating expenses, before finance charges.
These measures are distinct from revenue and profit earned by the bank.

In the simulation:

- Average deposit balances influence deposit-related bank revenue through an
  invented interest spread. Deposit interest expense is already netted in that
  component and is not deducted a second time.
- Average loan balances and fictional interest rates influence lending revenue.
- Card balances, purchases, and product holdings influence card and service revenue.
- Total bank revenue minus allocated expenses equals relationship profitability.

Balances describe a point in time; revenue, expenses, and profitability describe
a monthly period. Adding monthly balances would not produce annual revenue.
Full equations and thresholds are in
[simulation assumptions](simulation_assumptions.md), with field definitions in
[the data dictionary](data_dictionary.md).

## Example RM workflows

### Investigate a deposit decline

An invented business's deposits fall from USD 100,000 to USD 90,000, USD 80,000,
and USD 70,000 across four monthly observations. This meets the demonstration
rule: three consecutive declines, at least 20% cumulative decline, and a
starting balance of at least USD 10,000.

The RM reviews Customer 360 and asks about seasonality, investment, operating
pressures, or changes in banking arrangements. The indicator identifies a
conversation to have; it does not establish that the customer will leave.
These numbers are an illustrative example, not a claim about a generated row.

### Discuss a potential service need

A fictional business has monthly sales above the demonstration merchant-services
threshold but no merchant-services holding. The opportunity worklist identifies
the missing product and the trigger. The RM confirms how the business accepts
payments and whether a service discussion is useful. The business may already
use another provider or have no need for the bank's offering.

### Review portfolio performance

The RM selects a reporting month and their portfolio, reviews changes in
balances and bank profitability, and examines industry concentration. Customer
360 then provides context for individual relationships. RM Opportunities
provides a list of signals for follow-up. Multiple signals can belong to one
customer, so signal counts and unique-customer counts answer different questions.

## Scope and interpretation

All customers, identifiers, observations, parameters, and examples are fictional.
The fixed January 2024 to December 2025 dataset is reproducible and is not
calibrated against public or internal banking data. External links above provide
general background only; the generator does not download or ingest their data.

Opportunity rules use observable information through the selected month, rather
than later observations or generator scenario labels. They are transparent
demonstration rules, not predictions or confidential business rules.

The app does not implement outreach tracking, underwriting, customer consent,
or a production CRM workflow. Suitability, credit decisions, and actual outreach
remain professional processes outside this demonstration.

Return to the [project README](../README.md) for installation and usage.
