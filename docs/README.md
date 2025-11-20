
# Overview
This dashboard displays various metrics related to an investment portfolio. It consists of multiple statistics cards and charts that provide insights into portfolio performance.

## Sections
### Portfolio Value Card
Displays the total value of the investment portfolio based on current prices.

Footer Stats:
- Cost of the portfolio.
- Unrealized profit and percentage.

### Realized Gains Card (Closed Positions)
Shows the realized profit from closed positions.

Footer Stats:
- Realized gains year-to-date (YTD).
- (Commented-out) Average gain per position.

### Total P/L Card
Displays the total profit/loss, including both open and closed positions.
Calculated as total_wallet_value + total_gain - total_invested.

Footer Stats:
- Return on Investment (ROI).
- Realized profit percentage.

### Available Fiat Card
Displays the available fiat currency in the account.

Footer Stats:
- Liquidity ratio.

## Charts

### Portfolio Distribution Chart
Displays the distribution of wallet funds across brokers and exchanges using a Pie chart

Data: Brokers, exchanges and fiat.

### Distribution by Account Chart
Displays how the portfolio is distributed among different accounts using a Pie chart

Data: Each account's virtual balance.

### Total Portfolio Chart
Visualizes the total distribution of assets in the portfolio using a Pie chart

Data: Proportion of total wallet value.

### Investment Distribution Chart
Displays how investments are distributed across different brokers.

Data: Brokers and Percentage of each broker's virtual balance in the total wallet.

### Wallet Distribution by Account (Bar Chart)

Purpose: Displays the wallet distribution among different accounts using a bar chart.

Chart Type: Bar chart.

Title: "Wallet Distribution by Account".

Data: Account-wise wallet distribution.

### Portfolio Growth Over Time

Purpose: Shows the performance of the portfolio over time.

Chart Type: Line chart.

Title: "Portfolio Growth Over Time".

Data: Time-series data of portfolio value.