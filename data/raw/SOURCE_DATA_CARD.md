# Layoffs Dataset 2019–2026: Global, India, US, UK: findings, method and data card

*Fliar Research · released October 2026 · licence CC BY-NC 4.0*

**How this dataset was acquired.** Every row comes from the [Radar API](https://github.com/fliarbi/radar-api-mcp), Fliar's company-data API and MCP server. Radar reads
business news continuously in many countries and languages, picks out sentences that report job cuts, and extracts the company, the
number of jobs cut, the share of the workforce and the country. Each company is linked to its website in a database of five million
companies, which adds its home country, headquarters state or city and sector. Repeated reports of one layoff round are merged into a
single row (same company within 45 days), sector-wide or unnamed employers are dropped, and every headcount and percentage is kept only
when it appears in the news sentence. The data covers January 2019 to June 2026 worldwide, with India, the United Kingdom and the rest of
the world outside the US given dedicated tables. The full, continuously updated event timeline for any company is served by
`POST /v1/companies/events` ([reference](https://github.com/fliarbi/radar-api-mcp/blob/main/docs/reference/get_company_events.md)) and the `get_company_events` MCP tool.

> **This file is a 26% sample: 5,000 of 19,208 layoff events.** It keeps every record for a fixed subset of companies.
> The subset is chosen by a hash, so it stays the same from one release to the next. The findings and tables below were computed
> on the **full** data. For the rest, the withheld fields and monthly updates, [get a Radar API key](https://fliarbi.com/radar-api/developer) ([docs](https://github.com/fliarbi/radar-api-mcp)).
> Each row's `fliar_profile_url` opens the company's full profile on Fliar.

## Key findings

1. **19,208 layoff events at 13,303 companies in 169 countries, January 2019 to June 2026.** 57% of events with a known country happened outside the United States.
2. **Layoff events peaked in 2020** (3,780 events); 2023 had 3,391 and 2025 had 2,977, against 1,759 in 2019.
3. **India: 971 layoff events**, peaking in 2023 (219); the United Kingdom has 2,198. 9,541 events state a verified headcount, together 10,929,045 jobs; the median cut is 195.
4. **The largest single permanent cut is Amazon** (99,000 jobs, July 2022, United States); 540 events are furloughs or temporary lay-offs, flagged in `is_furlough`.
5. **2,768 companies had more than one layoff round**; 371 had five or more.
6. **Retail has the most layoff events** (1,008), followed by Food and Agriculture (795) and Consumer Goods (773).

![Layoff events per year by country](figures/layoffs_by_year.png)

![Top 15 countries for layoffs outside the US](figures/layoffs_outside_us.png)

![Sectors with the most layoff events](figures/layoffs_by_sector.png)

### Layoffs by year

2026 covers January to June. Jobs cut sums only verified headcounts.

| Year      | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | United States   | India   | United Kingdom   | Outside US share   |
|:----------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:----------------|:--------|:-----------------|:-------------------|
| 2019      | 1,759           | 1,562       | 873              | 764,478                | 200          | 617             | 84      | 261              | 61.8%              |
| 2020      | 3,780           | 3,331       | 1,849            | 3,122,163              | 262          | 1,447           | 164     | 561              | 57.9%              |
| 2021      | 1,032           | 958         | 413              | 448,334                | 244          | 301             | 32      | 127              | 67.7%              |
| 2022      | 2,008           | 1,755       | 934              | 846,889                | 144          | 779             | 139     | 169              | 58.2%              |
| 2023      | 3,391           | 2,965       | 1,784            | 1,822,899              | 170          | 1,483           | 219     | 309              | 51.7%              |
| 2024      | 3,011           | 2,603       | 1,517            | 1,440,648              | 166          | 1,148           | 149     | 305              | 57.9%              |
| 2025      | 2,977           | 2,569       | 1,529            | 1,734,556              | 193          | 1,233           | 134     | 326              | 54.9%              |
| 2026 (H1) | 1,250           | 1,188       | 642              | 749,078                | 160          | 493             | 50      | 140              | 56.7%              |

### Layoff events by quarter

| Year   | Q1    | Q2    | Q3   | Q4   | Total   | Jobs cut (disclosed)   |
|:-------|:------|:------|:-----|:-----|:--------|:-----------------------|
| 2019   | 456   | 384   | 439  | 480  | 1,759   | 764,478                |
| 2020   | 953   | 1,384 | 914  | 529  | 3,780   | 3,122,163              |
| 2021   | 416   | 221   | 220  | 175  | 1,032   | 448,334                |
| 2022   | 263   | 430   | 605  | 710  | 2,008   | 846,889                |
| 2023   | 1,096 | 871   | 662  | 762  | 3,391   | 1,822,899              |
| 2024   | 937   | 695   | 672  | 707  | 3,011   | 1,440,648              |
| 2025   | 789   | 702   | 829  | 657  | 2,977   | 1,734,556              |
| 2026   | 829   | 421   | 0    | 0    | 1,250   | 749,078                |

### Layoffs by month, July 2024 to June 2026

News volume thins after May 2026, so the last months may undercount.

| Month   | Layoff events   | Jobs cut (disclosed)   | United States   | India   | United Kingdom   | Rest of world   |
|:--------|:----------------|:-----------------------|:----------------|:--------|:-----------------|:----------------|
| 2024-07 | 230             | 66,883                 | 68              | 18      | 41               | 91              |
| 2024-08 | 224             | 104,314                | 87              | 12      | 17               | 82              |
| 2024-09 | 218             | 120,083                | 95              | 9       | 21               | 78              |
| 2024-10 | 272             | 94,406                 | 90              | 10      | 30               | 115             |
| 2024-11 | 232             | 98,750                 | 98              | 7       | 18               | 93              |
| 2024-12 | 203             | 124,560                | 64              | 19      | 17               | 89              |
| 2025-01 | 256             | 140,386                | 101             | 11      | 27               | 97              |
| 2025-02 | 289             | 146,983                | 127             | 10      | 24               | 104             |
| 2025-03 | 244             | 154,269                | 99              | 10      | 31               | 81              |
| 2025-04 | 259             | 160,485                | 106             | 20      | 25               | 82              |
| 2025-05 | 251             | 174,668                | 101             | 11      | 22               | 101             |
| 2025-06 | 192             | 74,011                 | 76              | 6       | 20               | 74              |
| 2025-07 | 277             | 138,257                | 119             | 15      | 39               | 81              |
| 2025-08 | 267             | 104,038                | 133             | 8       | 28               | 80              |
| 2025-09 | 285             | 180,297                | 107             | 18      | 42               | 97              |
| 2025-10 | 259             | 248,843                | 100             | 12      | 27               | 98              |
| 2025-11 | 229             | 115,496                | 89              | 7       | 29               | 77              |
| 2025-12 | 169             | 96,823                 | 75              | 6       | 12               | 68              |
| 2026-01 | 239             | 208,275                | 91              | 10      | 33               | 85              |
| 2026-02 | 322             | 180,296                | 132             | 12      | 31               | 123             |
| 2026-03 | 268             | 154,928                | 87              | 10      | 34               | 104             |
| 2026-04 | 303             | 168,414                | 119             | 14      | 33               | 108             |
| 2026-05 | 29              | 6,873                  | 18              | 0       | 2                | 7               |
| 2026-06 | 89              | 30,292                 | 46              | 4       | 7                | 28              |

### Top 50 largest layoffs worldwide, 2019–2026

Verified headcounts only; one row per layoff round; furloughs and temporary lay-offs excluded.

| #   | Date       | Company                 | Country        | Sector                          | Jobs cut   | % of workforce   | News reports   |
|:----|:-----------|:------------------------|:---------------|:--------------------------------|:-----------|:-----------------|:---------------|
| 1   | 2022-07-29 | Amazon                  | United States  | Retail                          | 99,000     | 3%               | 536            |
| 2   | 2023-04-22 | Bt Group                | United Kingdom |                                 | 55,000     |                  | 94             |
| 3   | 2026-03-10 | Volkswagen Group        | Germany        | Auto                            | 50,000     |                  | 66             |
| 4   | 2025-10-28 | United Parcel Service   | United States  | Business Services               | 48,000     |                  | 208            |
| 5   | 2023-12-26 | Citi                    | United States  | Financial Services              | 40,000     |                  | 22             |
| 6   | 2020-07-08 | United Airlines         | United States  | Travel and Hospitality          | 36,000     | 45%              | 86             |
| 7   | 2023-03-21 | Credit Suisse           | Switzerland    |                                 | 36,000     | 33%              | 8              |
| 8   | 2020-02-18 | HSBC                    | United Kingdom | Financial Services              | 35,000     | 15%              | 136            |
| 9   | 2024-12-13 | Volkswagen              | Germany        | Auto                            | 35,000     |                  | 25             |
| 10  | 2025-01-28 | Volkswagen              | Germany        | Auto                            | 35,000     |                  | 6              |
| 11  | 2020-08-03 | HSBC                    | United Kingdom | Financial Services              | 35,000     |                  | 2              |
| 12  | 2020-11-25 | Disney                  | United States  | Media & Entertainment           | 32,000     |                  | 99             |
| 13  | 2026-01-21 | Oracle                  | United States  | Enterprise Infrastructure       | 30,000     |                  | 178            |
| 14  | 2023-07-27 | Yellow                  | United States  | Fintech                         | 30,000     |                  | 103            |
| 15  | 2026-01-09 | United Parcel Service   | United States  | Business Services               | 30,000     |                  | 53             |
| 16  | 2022-01-05 | Future Retail           | India          | Retail                          | 29,000     |                  | 1              |
| 17  | 2020-09-29 | The Walt Disney Company | United States  | Media & Entertainment           | 28,000     | 67%              | 253            |
| 18  | 2020-03-17 | BritishAirways          | United Kingdom | Travel and Hospitality          | 28,000     | 80%              | 228            |
| 19  | 2024-06-21 | Tesla                   | United States  | Environment Tech                | 28,000     | 10%              | 8              |
| 20  | 2024-03-01 | Boeing                  | United States  | Aerospace, Maritime and Defense | 28,000     | 20%              | 2              |
| 21  | 2025-05-09 | Daimler Truck           | Germany        | Transportation and Logistics    | 28,000     |                  | 1              |
| 22  | 2024-03-01 | AT&T                    | United States  | Telecom                         | 27,400     | 13%              | 5              |
| 23  | 2022-02-15 | Amazon.com Inc          | United States  |                                 | 27,000     |                  | 27             |
| 24  | 2020-03-27 | Lufthansa               | Germany        | Travel and Hospitality          | 27,000     | 60%              | 19             |
| 25  | 2020-03-20 | United Airlines         | United States  | Travel and Hospitality          | 27,000     | 60%              | 4              |
| 26  | 2020-11-18 | Boeing                  | United States  | Aerospace, Maritime and Defense | 26,000     |                  | 3              |
| 27  | 2024-04-30 | Infosys                 | India          | Business Services               | 26,000     |                  | 3              |
| 28  | 2023-07-26 | Amazon                  | United States  | Retail                          | 25,000     |                  | 11             |
| 29  | 2024-12-20 | Google                  | United States  | High Tech                       | 25,000     | 10%              | 8              |
| 30  | 2025-04-18 | B Laban                 | Egypt          |                                 | 25,000     |                  | 1              |
| 31  | 2025-11-19 | VW                      | Germany        |                                 | 25,000     |                  | 1              |
| 32  | 2025-10-08 | Wipro Consumer Care     | India          | Consumer Goods                  | 24,516     |                  | 2              |
| 33  | 2023-11-06 | Citi                    | United States  | Financial Services              | 24,000     | 10%              | 23             |
| 34  | 2026-04-09 | TCS                     | India          | Business Services               | 23,460     | 2%               | 19             |
| 35  | 2025-08-09 | HP                      | United States  | Consumer Goods                  | 22,700     |                  | 1              |
| 36  | 2026-02-05 | Technology              |                | Business Services               | 22,291     |                  | 1              |
| 37  | 2020-05-25 | Lufthansa               | Germany        | Travel and Hospitality          | 22,000     | 25%              | 93             |
| 38  | 2022-10-12 | Intel                   | United States  | Semiconductors                  | 22,000     | 20%              | 46             |
| 39  | 2025-10-08 | Intel                   | United States  | Semiconductors                  | 22,000     |                  | 4              |
| 40  | 2019-12-20 | France Telecom          | France         |                                 | 22,000     |                  | 1              |
| 41  | 2025-04-23 | Intel                   | United States  | Semiconductors                  | 21,000     | 20%              | 37             |
| 42  | 2020-07-23 | Schlumberger            | United States  |                                 | 21,000     | 20%              | 21             |
| 43  | 2023-01-14 | Wells Fargo             | United States  | Financial Services              | 21,000     |                  | 1              |
| 44  | 2023-04-28 | Reality Labs            |                |                                 | 21,000     |                  | 1              |
| 45  | 2025-04-29 | United Parcel Service   | United States  | Business Services               | 20,000     | 4%               | 152            |
| 46  | 2025-07-28 | TCS                     | United Kingdom | Real Estate and Construction    | 20,000     | 2%               | 62             |
| 47  | 2020-05-16 | Air Canada              | Canada         | Travel and Hospitality          | 20,000     | 50%              | 12             |
| 48  | 2026-03-19 | HSBC                    | United Kingdom | Financial Services              | 20,000     | 10%              | 10             |
| 49  | 2023-07-27 | Meta                    | United States  | High Tech                       | 20,000     |                  | 7              |
| 50  | 2020-06-19 | Daimler                 | Germany        |                                 | 20,000     | 10%              | 6              |

### Layoffs by country worldwide (top 40)

| Country              | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | 2023   | 2025   | Largest layoffs                                       |
|:---------------------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:-------|:-------|:------------------------------------------------------|
| United States        | 7,501           | 5,116       | 4,211            | 4,343,018              | 150          | 1,483  | 1,233  | Disney, Amazon, Kohl                                  |
| United Kingdom       | 2,198           | 1,556       | 1,095            | 1,335,487              | 250          | 309    | 326    | Bt Group, HSBC, BritishAirways                        |
| India                | 971             | 645         | 530              | 655,836                | 200          | 219    | 134    | Future Retail, Infosys, Wipro Consumer Care           |
| Germany              | 834             | 551         | 388              | 855,910                | 450          | 101    | 194    | Volkswagen Group, Volkswagen, Daimler Truck           |
| Canada               | 768             | 572         | 373              | 251,069                | 131          | 154    | 118    | Air Canada, Martinrea, Rogers                         |
| Australia            | 553             | 410         | 262              | 187,754                | 168          | 104    | 81     | Crown Casino, MIER, Telstra                           |
| France               | 526             | 394         | 214              | 223,548                | 301          | 49     | 91     | France Telecom, Airbus, Renault                       |
| Switzerland          | 353             | 262         | 156              | 162,143                | 120          | 49     | 52     | Credit Suisse, Nestle, NestlÃ©                        |
| Spain                | 286             | 198         | 143              | 229,848                | 400          | 30     | 50     | El Corte Inglés, Caixabank, Sabadell                  |
| China                | 284             | 230         | 95               | 167,712                | 500          | 44     | 25     | Cathay Pacific, Google, Gaotu                         |
| Brazil               | 230             | 182         | 83               | 104,511                | 206          | 72     | 21     | Brasília Post Offices, Correios, Casas Bahia          |
| Singapore            | 155             | 130         | 70               | 54,028                 | 114          | 21     | 19     | Challenger, Sea, Singapore’s Sea                      |
| Ireland              | 150             | 122         | 74               | 33,748                 | 160          | 24     | 17     | Meta, Avoca, AIB                                      |
| Sweden               | 149             | 92          | 81               | 97,400                 | 400          | 35     | 22     | SAS, Ericsson, Autoliv                                |
| Netherlands          | 141             | 100         | 75               | 132,761                | 750          | 26     | 26     | Extensive, Inter Ikea, Shell                          |
| Japan                | 136             | 93          | 75               | 193,422                | 562          | 16     | 14     | Nissan Motor, Japan’s ANA, Nissan                     |
| Israel               | 133             | 109         | 74               | 26,538                 | 100          | 27     | 16     | Hewlett Packard, Teva Pharmaceuticals, EL AL          |
| Finland              | 124             | 67          | 71               | 53,387                 | 135          | 16     | 22     | Nokia, Finnar, STORA ENSO                             |
| Austria              | 121             | 99          | 59               | 26,672                 | 190          | 14     | 23     | MAN Truck & Bus, OMV Group, Kika/Leiner               |
| Nigeria              | 111             | 92          | 41               | 25,709                 | 100          | 13     | 15     | Gokada, Kimberly-Clark, Procter & Gamble              |
| New Zealand          | 108             | 89          | 52               | 30,237                 | 125          | 15     | 10     | Air NZ, Fletcher Building, Fonterra                   |
| South Africa         | 106             | 82          | 48               | 76,893                 | 600          | 12     | 12     | Sibanye-Stillwater, Eskom, Implats                    |
| Italy                | 90              | 62          | 53               | 100,705                | 769          | 17     | 11     | Intesa Sanpaolo, UniCredit, TIM                       |
| South Korea          | 90              | 74          | 22               | 24,612                 | 254          | 14     | 9      | Samsung, Citibank Korea, CGV                          |
| Indonesia            | 86              | 72          | 37               | 57,303                 | 500          | 25     | 11     | Sritex, Shopee, Twa3D                                 |
| Kenya                | 85              | 67          | 36               | 13,382                 | 211          | 12     | 8      | Telkom, Equity Group, Samasource Impact Sourcing Inc  |
| Denmark              | 83              | 58          | 46               | 103,318                | 575          | 11     | 11     | DSV, Mita, Maersk                                     |
| Belgium              | 64              | 52          | 31               | 10,070                 | 135          | 8      | 4      | Renault, Sonaca, GlaxoSmithKline                      |
| Russia               | 61              | 57          | 16               | 38,111                 | 566          | 3      | 10     | Mercedes, Rostselmash, Gazprom                        |
| Hong Kong            | 47              | 41          | 16               | 16,031                 | 225          | 10     | 6      | Cathay Pacific, Cathay Dragon, Nagacorp               |
| Mexico               | 45              | 40          | 18               | 15,490                 | 275          | 4      | 5      | Safran, Mexico’s Pemex, Aviva                         |
| Argentina            | 44              | 39          | 21               | 12,263                 | 190          | 4      | 11     | Eternal, Aerolíneas Argentinas, Globant               |
| Malaysia             | 43              | 35          | 13               | 13,260                 | 200          | 8      | 8      | Genting Malaysia, Genting Malaysia Bhd, AirAsia       |
| United Arab Emirates | 40              | 31          | 21               | 20,609                 | 400          | 4      | 2      | Emirates, United Furniture, Abu Dhabi Commercial Bank |
| Norway               | 39              | 31          | 18               | 20,468                 | 254          | 7      | 6      | Norwegian Air Shuttle, Norwegian Air, Telia           |
| Vietnam              | 38              | 32          | 18               | 63,257                 | 2,000        | 16     | 1      | Citibank, Regina Miracle, PouYuen Vietnam             |
| Poland               | 37              | 30          | 16               | 19,345                 | 120          | 5      | 4      | TUI, Pkp Cargo, Provident                             |
| Philippines          | 29              | 25          | 19               | 24,582                 | 300          | 5      | 4      | ABS‑CBN Corporation, ABS-CBN Corp, PAL Holdings       |
| Luxembourg           | 29              | 15          | 19               | 22,623                 | 400          | 4      | 7      | BCE, ArcelorMittal, Subsea 7                          |
| Ghana                | 26              | 25          | 10               | 8,331                  | 275          | 4      | 5      | Groupe Nduom, Gn Bank, Neoplan                        |

### Layoff events by country and year (top 30)

| Country        | 2019   | 2020   | 2021   | 2022   | 2023   | 2024   | 2025   | 2026 (H1)   | Total   |
|:---------------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|:------------|:--------|
| United States  | 617    | 1,447  | 301    | 779    | 1,483  | 1,148  | 1,233  | 493         | 7,501   |
| United Kingdom | 261    | 561    | 127    | 169    | 309    | 305    | 326    | 140         | 2,198   |
| India          | 84     | 164    | 32     | 139    | 219    | 149    | 134    | 50          | 971     |
| Germany        | 91     | 102    | 51     | 47     | 101    | 170    | 194    | 78          | 834     |
| Canada         | 59     | 156    | 27     | 85     | 154    | 133    | 118    | 36          | 768     |
| Australia      | 42     | 135    | 22     | 57     | 104    | 79     | 81     | 33          | 553     |
| France         | 56     | 106    | 51     | 44     | 49     | 82     | 91     | 47          | 526     |
| Switzerland    | 38     | 82     | 24     | 24     | 49     | 65     | 52     | 19          | 353     |
| Spain          | 25     | 46     | 57     | 21     | 30     | 34     | 50     | 23          | 286     |
| China          | 43     | 24     | 21     | 67     | 44     | 55     | 25     | 5           | 284     |
| Brazil         | 16     | 41     | 16     | 38     | 72     | 20     | 21     | 6           | 230     |
| Singapore      | 15     | 32     | 7      | 28     | 21     | 23     | 19     | 10          | 155     |
| Ireland        | 24     | 37     | 12     | 15     | 24     | 13     | 17     | 8           | 150     |
| Sweden         | 12     | 20     | 4      | 17     | 35     | 26     | 22     | 13          | 149     |
| Netherlands    | 10     | 26     | 5      | 21     | 26     | 22     | 26     | 5           | 141     |
| Japan          | 15     | 30     | 10     | 15     | 16     | 28     | 14     | 8           | 136     |
| Israel         | 6      | 8      | 1      | 51     | 27     | 16     | 16     | 8           | 133     |
| Finland        | 9      | 23     | 8      | 9      | 16     | 26     | 22     | 11          | 124     |
| Austria        | 12     | 12     | 5      | 11     | 14     | 34     | 23     | 10          | 121     |
| Nigeria        | 8      | 25     | 4      | 10     | 13     | 28     | 15     | 8           | 111     |
| New Zealand    | 10     | 31     | 5      | 17     | 15     | 14     | 10     | 6           | 108     |
| South Africa   | 10     | 29     | 5      | 3      | 12     | 26     | 12     | 9           | 106     |
| Italy          | 15     | 11     | 7      | 15     | 17     | 11     | 11     | 3           | 90      |
| South Korea    | 7      | 20     | 13     | 3      | 14     | 13     | 9      | 11          | 90      |
| Indonesia      | 1      | 9      | 6      | 23     | 25     | 8      | 11     | 3           | 86      |
| Kenya          | 17     | 15     | 3      | 9      | 12     | 15     | 8      | 6           | 85      |
| Denmark        | 6      | 21     | 4      | 6      | 11     | 13     | 11     | 11          | 83      |
| Belgium        | 6      | 15     | 7      | 2      | 8      | 14     | 4      | 8           | 64      |
| Russia         | 1      | 3      | 1      | 37     | 3      | 5      | 10     | 1           | 61      |
| Hong Kong      | 4      | 9      | 9      | 2      | 10     | 7      | 6      | 0           | 47      |

### Layoffs by sector (top 30)

| Sector                             | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | 2023   | 2025   | Largest layoffs                                         |
|:-----------------------------------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:-------|:-------|:--------------------------------------------------------|
| Retail                             | 1,008           | 572         | 549              | 953,276                | 225          | 168    | 145    | Amazon, Kohl, Gap                                       |
| Food and Agriculture               | 795             | 513         | 434              | 315,284                | 159          | 90     | 150    | Cheesecake Factory, Craftworks Holdings, Nestle         |
| Consumer Goods                     | 773             | 503         | 407              | 308,107                | 185          | 107    | 139    | Wipro Consumer Care, HP, Arcadia Group                  |
| Consumer                           | 769             | 479         | 400              | 207,730                | 150          | 159    | 75     | Boohoo, Google Korea, TUI                               |
| Business Services                  | 756             | 550         | 336              | 517,824                | 200          | 138    | 133    | United Parcel Service, Infosys, TCS                     |
| Financial Services                 | 755             | 423         | 430              | 766,616                | 300          | 128    | 100    | Citi, HSBC, Wells Fargo                                 |
| Media & Entertainment              | 610             | 392         | 294              | 356,651                | 132          | 124    | 96     | Disney, The Walt Disney Company, Procter & Gamble       |
| Auto                               | 599             | 338         | 358              | 723,566                | 477          | 69     | 110    | Volkswagen Group, Volkswagen, Chrysler                  |
| Fintech                            | 599             | 434         | 289              | 174,097                | 111          | 177    | 47     | Yellow, Novo Nordisk, Paytm                             |
| Enterprise Applications            | 550             | 390         | 277              | 173,038                | 123          | 154    | 71     | SAP, Salesforce, Sap Se                                 |
| Healthcare                         | 499             | 296         | 284              | 167,163                | 154          | 90     | 82     | Bsnl, Tenet Healthcare, Viatris                         |
| Travel and Hospitality             | 478             | 263         | 272              | 629,509                | 600          | 26     | 39     | United Airlines, BritishAirways, Lufthansa              |
| Energy                             | 420             | 269         | 198              | 196,067                | 214          | 35     | 85     | Shell, Coal India, Eskom                                |
| Life Sciences                      | 408             | 320         | 183              | 34,716                 | 81           | 130    | 61     | Grifols, Olympus, NGM Biopharmaceuticals                |
| Food and Agriculture Tech          | 299             | 191         | 173              | 85,198                 | 165          | 78     | 35     | Getir, Zomato, Eternal                                  |
| High Tech                          | 295             | 182         | 159              | 217,869                | 130          | 75     | 39     | Google, Meta, Peloton                                   |
| Real Estate and Construction       | 294             | 205         | 141              | 130,043                | 217          | 50     | 46     | TCS, CRH, Premier Retail Solutions                      |
| Telecom                            | 283             | 160         | 162              | 292,117                | 541          | 41     | 36     | AT&T, Verizon Communications, MTNL                      |
| Enterprise Infrastructure          | 281             | 152         | 165              | 286,636                | 247          | 94     | 39     | Oracle, Extensive, VMware                               |
| Healthtech                         | 244             | 168         | 122              | 37,756                 | 110          | 63     | 27     | Eon, IPG, Canopy Growth                                 |
| Industrial Goods and Manufacturing | 221             | 152         | 117              | 85,387                 | 124          | 31     | 50     | Renault, Siemens, TAL                                   |
| Gaming                             | 206             | 137         | 91               | 27,195                 | 60           | 47     | 37     | Embracer Group, Blizzard Entertainment, Electronic Arts |
| Transportation and Logistics       | 201             | 136         | 115              | 186,570                | 162          | 21     | 48     | Daimler Truck, Correios, DSV                            |
| Energy Tech                        | 198             | 128         | 107              | 55,964                 | 200          | 42     | 34     | Mita, Northvolt, OVO Energy                             |
| Chemicals and Materials            | 170             | 113         | 92               | 58,346                 | 265          | 26     | 32     | DOW, Union Carbide, Tata Steel                          |
| Semiconductors                     | 163             | 96          | 96               | 144,080                | 310          | 29     | 38     | Intel, STMicroelectronics, Micron                       |
| Aerospace, Maritime and Defense    | 155             | 74          | 104              | 230,915                | 423          | 14     | 21     | Boeing, Airbus, Rolls-Royce                             |
| Edtech                             | 144             | 92          | 86               | 58,894                 | 150          | 47     | 9      | BYJU'S, WhiteHat Jr, Unacademy                          |
| Investment Industry                | 142             | 66          | 76               | 163,395                | 540          | 30     | 31     | Accenture, UBS Social Innovators, HHS                   |
| Mining                             | 139             | 88          | 69               | 85,785                 | 258          | 19     | 27     | Alcoa, Sibanye-Stillwater, Caterpillar                  |

### Companies with repeated layoffs (top 50)

Companies with two or more separate layoff rounds.

| #   | Company         | Country        | Sector                             | Layoff events   | Years with layoffs   | Jobs cut (disclosed, sum)   | Largest single cut   | First   | Latest   |
|:----|:----------------|:---------------|:-----------------------------------|:----------------|:---------------------|:----------------------------|:---------------------|:--------|:---------|
| 1   | General Motors  | United States  | Auto                               | 22              | 7                    | 35,278                      | 7,000                | 2019-01 | 2026-03  |
| 2   | Stellantis      | Netherlands    | Auto                               | 22              | 5                    | 24,552                      | 4,000                | 2021-02 | 2025-10  |
| 3   | Microsoft       | United Kingdom | Enterprise Infrastructure          | 21              | 8                    | 49,589                      | 15,000               | 2019-07 | 2026-06  |
| 4   | Amazon          | United States  | Retail                             | 20              | 7                    | 177,282                     | 99,000               | 2019-02 | 2026-03  |
| 5   | Wells Fargo     | United States  | Financial Services                 | 20              | 8                    | 59,765                      | 21,000               | 2019-01 | 2026-03  |
| 6   | Boeing          | United States  | Aerospace, Maritime and Defense    | 18              | 7                    | 116,570                     | 28,000               | 2019-01 | 2026-02  |
| 7   | Nestle          | Switzerland    | Food and Agriculture               | 18              | 8                    | 17,422                      | 16,000               | 2019-01 | 2026-04  |
| 8   | Walmart         | United States  | Retail                             | 18              | 7                    | 9,099                       | 2,000                | 2019-02 | 2026-03  |
| 9   | Citi            | United States  | Financial Services                 | 17              | 7                    | 90,126                      | 40,000               | 2019-08 | 2026-02  |
| 10  | Google          | United States  | High Tech                          | 17              | 7                    | 40,125                      | 25,000               | 2019-11 | 2026-01  |
| 11  | IBM             | United States  | Enterprise Infrastructure          | 17              | 7                    | 37,005                      | 9,000                | 2019-01 | 2026-01  |
| 12  | Bosch           | Germany        | Conglomerates                      | 17              | 7                    | 27,836                      | 11,500               | 2019-01 | 2026-04  |
| 13  | Volkswagen      | Germany        | Auto                               | 16              | 7                    | 46,729                      | 35,000               | 2019-01 | 2025-06  |
| 14  | Intel           | United States  | Semiconductors                     | 16              | 7                    | 32,727                      | 22,000               | 2019-03 | 2026-02  |
| 15  | FedEx Corp      | United States  |                                    | 16              | 5                    | 10,726                      | 6,300                | 2021-01 | 2026-04  |
| 16  | Novartis        | Switzerland    | Healthcare                         | 16              | 6                    | 3,208                       | 680                  | 2019-10 | 2026-03  |
| 17  | Nissan          | Japan          | Auto                               | 15              | 6                    | 66,849                      | 12,000               | 2019-03 | 2026-05  |
| 18  | GM              | United States  |                                    | 15              | 7                    | 21,980                      | 10,000               | 2019-02 | 2026-04  |
| 19  | Salesforce      | United States  | Enterprise Applications            | 15              | 6                    | 20,423                      | 8,000                | 2020-02 | 2026-04  |
| 20  | Pfizer          | India          | Healthcare                         | 15              | 8                    | 13,369                      | 8,000                | 2019-01 | 2026-04  |
| 21  | Infosys         | India          | Business Services                  | 14              | 6                    | 79,809                      | 26,000               | 2019-11 | 2025-10  |
| 22  | Oracle          | United States  | Enterprise Infrastructure          | 14              | 6                    | 58,097                      | 30,000               | 2019-03 | 2026-06  |
| 23  | Ford            | United Kingdom | Auto                               | 14              | 7                    | 35,565                      | 12,000               | 2019-01 | 2025-12  |
| 24  | UBS Group AG    | Switzerland    | Investment Industry                | 14              | 5                    | 19,849                      | 11,000               | 2019-08 | 2025-11  |
| 25  | Tyson Foods     | United States  | Food and Agriculture               | 14              | 7                    | 11,764                      | 3,212                | 2020-02 | 2026-04  |
| 26  | Meta            | United States  | High Tech                          | 13              | 5                    | 54,634                      | 11,000               | 2021-08 | 2026-06  |
| 27  | HSBC            | United Kingdom | Financial Services                 | 13              | 7                    | 40,940                      | 35,000               | 2019-08 | 2026-06  |
| 28  | Airbus          | France         | Aerospace, Maritime and Defense    | 13              | 7                    | 24,253                      | 15,000               | 2019-02 | 2025-01  |
| 29  | Cisco           | United States  | Enterprise Infrastructure          | 13              | 6                    | 21,958                      | 5,600                | 2019-08 | 2025-08  |
| 30  | Nokia           | Finland        | Telecom                            | 13              | 7                    | 19,941                      | 14,000               | 2020-01 | 2026-03  |
| 31  | Qantas          | Australia      | Travel and Hospitality             | 13              | 7                    | 14,150                      | 6,000                | 2020-03 | 2026-02  |
| 32  | Chevron         | United States  | Investment Industry                | 13              | 5                    | 8,755                       | 6,750                | 2019-08 | 2025-09  |
| 33  | EY              | United Kingdom | Financial Services                 | 13              | 8                    | 3,204                       | 3,000                | 2019-11 | 2026-02  |
| 34  | Continental     | Germany        | Food and Agriculture               | 12              | 6                    | 47,370                      | 13,000               | 2019-09 | 2025-11  |
| 35  | VW Group        | Germany        |                                    | 12              | 6                    | 46,318                      | 25,000               | 2019-03 | 2026-03  |
| 36  | Tesla           | United States  | Environment Tech                   | 12              | 7                    | 43,850                      | 28,000               | 2019-01 | 2026-04  |
| 37  | AT&T            | United States  | Telecom                            | 12              | 7                    | 33,955                      | 27,400               | 2019-01 | 2025-12  |
| 38  | Deutsche Bank   | Germany        | Financial Services                 | 12              | 6                    | 24,860                      | 18,000               | 2019-02 | 2024-11  |
| 39  | Marks & Spencer | United Kingdom |                                    | 12              | 7                    | 18,381                      | 8,000                | 2019-01 | 2026-02  |
| 40  | Starbucks       | India          | Food and Agriculture               | 12              | 5                    | 9,450                       | 6,700                | 2022-02 | 2026-04  |
| 41  | STORA ENSO      | Finland        | Real Estate and Construction       | 12              | 6                    | 4,602                       | 2,000                | 2019-02 | 2025-02  |
| 42  | KPMG            | United States  | Fintech                            | 12              | 6                    | 2,990                       | 1,400                | 2019-07 | 2026-03  |
| 43  | Morrisons       | United Kingdom | Retail                             | 12              | 7                    | 2,684                       | 1,300                | 2019-08 | 2026-01  |
| 44  | Bayer           | Germany        | Healthcare                         | 12              | 5                    | 2,164                       | 1,500                | 2019-01 | 2026-04  |
| 45  | United Airlines | United States  | Travel and Hospitality             | 11              | 4                    | 88,983                      | 36,000               | 2019-05 | 2022-01  |
| 46  | Renault         | France         | Industrial Goods and Manufacturing | 11              | 6                    | 36,824                      | 15,000               | 2020-03 | 2025-12  |
| 47  | Accenture       | United States  | Investment Industry                | 11              | 5                    | 32,989                      | 19,000               | 2020-06 | 2025-09  |
| 48  | Cognizant       | United States  | Financial Services                 | 11              | 5                    | 31,500                      | 7,600                | 2019-03 | 2026-04  |
| 49  | Telstra         | Australia      | Telecom                            | 11              | 7                    | 17,513                      | 10,000               | 2019-01 | 2026-02  |
| 50  | Morgan Stanley  | United States  |                                    | 11              | 7                    | 15,590                      | 4,800                | 2020-01 | 2026-01  |

### Top 50 largest layoffs in India, 2019–2026

| #   | Date       | Company                           | Country   | Sector                    | Jobs cut   | % of workforce   | News reports   |
|:----|:-----------|:----------------------------------|:----------|:--------------------------|:-----------|:-----------------|:---------------|
| 1   | 2022-01-05 | Future Retail                     | India     | Retail                    | 29,000     |                  | 1              |
| 2   | 2024-04-30 | Infosys                           | India     | Business Services         | 26,000     |                  | 3              |
| 3   | 2025-10-08 | Wipro Consumer Care               | India     | Consumer Goods            | 24,516     |                  | 2              |
| 4   | 2026-04-09 | TCS                               | India     | Business Services         | 23,460     | 2%               | 19             |
| 5   | 2020-09-05 | Bharat Sanchar Nigam Limited      | India     |                           | 20,000     |                  | 1              |
| 6   | 2025-10-14 | Infosys                           | India     | Business Services         | 18,506     |                  | 2              |
| 7   | 2020-07-04 | Cognizant                         | India     | Financial Services        | 18,000     |                  | 5              |
| 8   | 2020-04-06 | MTNL                              | India     | Telecom                   | 14,378     |                  | 2              |
| 9   | 2020-04-07 | Mahanagar Telephone Nigam         | India     |                           | 14,378     | 60%              | 1              |
| 10  | 2025-10-14 | Tech Mahindra                     | India     | Business Services         | 13,308     | 8%               | 2              |
| 11  | 2023-10-09 | BYJU'S                            | India     | Edtech                    | 13,000     |                  | 5              |
| 12  | 2025-07-28 | Tata Consultancy Service          | India     |                           | 12,200     | 2%               | 3              |
| 13  | 2020-05-16 | Oracle                            | India     | Enterprise Infrastructure | 12,000     |                  | 42             |
| 14  | 2019-11-05 | Infosys                           | India     | Business Services         | 12,000     | 10%              | 4              |
| 15  | 2022-01-11 | BYJU'S                            | India     | Edtech                    | 12,000     | 25%              | 3              |
| 16  | 2025-08-18 | A Software Services Company       | India     |                           | 12,000     |                  | 1              |
| 17  | 2025-09-26 | India’s Tata Consultancy Services | India     |                           | 12,000     |                  | 1              |
| 18  | 2026-04-15 | ORECLE                            | India     |                           | 12,000     |                  | 1              |
| 19  | 2025-07-16 | Tech Mahindra                     | India     | Business Services         | 10,669     | 12.6%            | 5              |
| 20  | 2024-09-23 | Coal India                        | India     | Energy                    | 10,349     |                  | 2              |
| 21  | 2019-10-16 | Parle Biscuits                    | India     |                           | 10,000     |                  | 1              |
| 22  | 2024-09-23 | State Bank Of India               | India     |                           | 8,392      |                  | 1              |
| 23  | 2023-10-12 | Infosys                           | India     | Business Services         | 7,530      |                  | 9              |
| 24  | 2023-05-04 | Go First                          | India     | Travel and Hospitality    | 7,000      |                  | 3              |
| 25  | 2024-04-25 | Tech Mahindra                     | India     | Business Services         | 6,945      |                  | 4              |
| 26  | 2023-10-12 | TCS                               | India     | Business Services         | 6,333      |                  | 26             |
| 27  | 2024-01-11 | Infosys                           | India     | Business Services         | 6,101      |                  | 6              |
| 28  | 2025-03-01 | SKODA                             | India     | Auto                      | 6,000      |                  | 2              |
| 29  | 2021-07-26 | PVR Cinemas                       | India     | Media & Entertainment     | 6,000      |                  | 1              |
| 30  | 2025-01-09 | TCS                               | India     | Business Services         | 5,000      |                  | 11             |
| 31  | 2020-06-09 | OYO                               | India     | Consumer                  | 5,000      |                  | 3              |
| 32  | 2024-09-17 | Paytm                             | India     | Fintech                   | 5,000      |                  | 2              |
| 33  | 2019-05-29 | Reliance Jio Infocomm             | India     |                           | 5,000      |                  | 1              |
| 34  | 2020-08-17 | Zomato                            | India     | Food and Agriculture Tech | 5,000      | 13%              | 1              |
| 35  | 2026-01-05 | Zomato                            | India     | Food and Agriculture Tech | 5,000      |                  | 1              |
| 36  | 2023-06-01 | Ranbaxy Laboratories              | India     | Healthcare                | 4,867      |                  | 1              |
| 37  | 2023-10-12 | HCL Technologies                  | India     | Business Services         | 4,800      |                  | 7              |
| 38  | 2025-08-07 | Paytm                             | India     | Fintech                   | 4,600      |                  | 3              |
| 39  | 2024-03-05 | Infosys                           | India     | Business Services         | 4,521      |                  | 11             |
| 40  | 2022-07-21 | Air India                         | India     | Travel and Hospitality    | 4,500      |                  | 2              |
| 41  | 2022-12-13 | BYJU'S                            | India     | Edtech                    | 4,000      |                  | 70             |
| 42  | 2023-09-27 | Think & Learn Private Limited     | India     |                           | 4,000      |                  | 1              |
| 43  | 2025-04-25 | HCL Technologies                  | India     | Business Services         | 4,000      |                  | 1              |
| 44  | 2023-04-13 | Infosys                           | India     | Business Services         | 3,611      |                  | 3              |
| 45  | 2023-06-19 | BYJU'S                            | India     | Edtech                    | 3,500      | 5%               | 9              |
| 46  | 2026-03-10 | Tech Mahindra                     | India     | Business Services         | 3,500      |                  | 7              |
| 47  | 2024-05-23 | One97 Communications              | India     | Fintech                   | 3,500      |                  | 6              |
| 48  | 2022-03-08 | Better                            | India     | Enterprise Applications   | 3,000      | 34%              | 46             |
| 49  | 2019-08-02 | Maruti Suzuki India               | India     | Auto                      | 3,000      | 6%               | 23             |
| 50  | 2026-04-25 | Axis Bank                         | India     | Financial Services        | 3,000      |                  | 11             |

### India layoffs by sector (top 25)

| Sector                       | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | 2023   | 2025   | Largest layoffs                                           |
|:-----------------------------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:-------|:-------|:----------------------------------------------------------|
| Consumer                     | 100             | 61          | 62               | 20,630                 | 190          | 22     | 9      | OYO, ByteDance, Truevalue                                 |
| Retail                       | 74              | 42          | 44               | 52,110                 | 200          | 19     | 6      | Future Retail, Udaan, OLA                                 |
| Edtech                       | 69              | 38          | 48               | 51,301                 | 200          | 31     | 2      | BYJU'S, WhiteHat Jr, Unacademy                            |
| Business Services            | 61              | 26          | 37               | 167,420                | 800          | 10     | 13     | Infosys, TCS, Tech Mahindra                               |
| Fintech                      | 59              | 43          | 31               | 21,384                 | 150          | 17     | 7      | Paytm, One97 Communications, BIJU                         |
| Food and Agriculture Tech    | 50              | 25          | 34               | 21,331                 | 300          | 20     | 4      | Zomato, Whole Foods, JioMart                              |
| Consumer Goods               | 36              | 21          | 17               | 29,898                 | 300          | 3      | 13     | Wipro Consumer Care, Atlas Cycles, Amway                  |
| Media & Entertainment        | 35              | 27          | 19               | 16,424                 | 125          | 5      | 9      | Star Entertainment Group, PVR Cinemas, SITI Networks      |
| Auto                         | 34              | 26          | 14               | 20,668                 | 943          | 3      | 4      | SKODA, Maruti Suzuki India, Ford India                    |
| Healthtech                   | 32              | 23          | 20               | 3,364                  | 105          | 10     | 2      | Cure.Fit, Phable, Pristyn Care                            |
| Financial Services           | 30              | 17          | 14               | 29,068                 | 500          | 2      | 7      | Cognizant, Axis Bank, Bank of Baroda                      |
| Travel and Hospitality       | 28              | 11          | 16               | 22,108                 | 600          | 3      | 2      | Go First, Air India, OYO Hotels                           |
| Enterprise Applications      | 28              | 19          | 21               | 7,612                  | 125          | 9      | 4      | Better, Jungheinrich India, Zaggle                        |
| Healthcare                   | 24              | 19          | 9                | 7,505                  | 125          | 3      | 3      | Ranbaxy Laboratories, Pfizer, Novartis healthcare pvt ltd |
| Food and Agriculture         | 20              | 12          | 10               | 2,277                  | 100          | 2      | 3      | Starbucks, McVitie's, Subway                              |
| Energy Tech                  | 16              | 9           | 10               | 4,435                  | 225          | 1      | 4      | Ola Electric, Euler Motors, Switch Mobility               |
| Telecom                      | 9               | 5           | 2                | 15,378                 | 7,689        | 0      | 1      | MTNL, Aircel, Jio                                         |
| Life Sciences                | 9               | 3           | 7                | 1,006                  | 97           | 3      | 1      | Thermo Fisher Scientific, Mojocare, Cochlear              |
| High Tech                    | 9               | 5           | 6                | 860                    | 145          | 3      | 1      | Bolt, Practically, Krutrim                                |
| Mobile                       | 9               | 6           | 5                | 935                    | 170          | 1      | 5      | Gameskraft, Zupee, SuperGaming                            |
| Chemicals and Materials      | 7               | 3           | 3                | 338                    | 50           | 4      | 1      | Rieter, SRF, Tata Steel                                   |
| Gaming                       | 7               | 4           | 5                | 806                    | 100          | 4      | 2      | MPL, Loco, Quizy                                          |
| Energy                       | 7               | 7           | 3                | 10,899                 | 500          | 1      | 1      | Coal India, ZEE, Gensol                                   |
| Real Estate and Construction | 6               | 5           | 0                | 0                      |              | 0      | 0      | Legacy, Doka, JLL                                         |
| Education                    | 6               | 4           | 4                | 410                    | 105          | 1      | 0      | Udayy, Aakash Educational Services, Chegg                 |

### India layoffs by company HQ state (top 25)

HQ location from the company database.

| Indian state   | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | 2023   | 2025   | Largest layoffs                                      |
|:---------------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:-------|:-------|:-----------------------------------------------------|
| Karnataka      | 265             | 133         | 177              | 190,731                | 200          | 80     | 27     | Infosys, Wipro Consumer Care, BYJU'S                 |
| Maharashtra    | 156             | 101         | 67               | 129,411                | 300          | 30     | 24     | Future Retail, TCS, MTNL                             |
| Haryana        | 102             | 59          | 68               | 46,935                 | 200          | 27     | 14     | PVR Cinemas, Zomato, OYO                             |
| Delhi          | 52              | 33          | 27               | 14,261                 | 130          | 13     | 10     | Air India, Maruti Suzuki India, Whole Foods          |
| Uttar Pradesh  | 40              | 25          | 21               | 28,041                 | 450          | 6      | 7      | Paytm, HCL Technologies, One97 Communications        |
| Tamil Nadu     | 22              | 15          | 14               | 4,242                  | 180          | 3      | 2      | Aircel, Wheels India, OTTO                           |
| Gujarat        | 11              | 10          | 5                | 3,082                  | 200          | 3      | 2      | Bank of Baroda, Lendingkart, L&T Technology Services |
| West Bengal    | 10              | 8           | 4                | 10,874                 | 200          | 1      | 3      | Coal India, PokerBaazi, MoonShine Technologies       |
| Rajasthan      | 6               | 5           | 1                | 200                    | 200          | 0      | 1      | CarDekho, ApnaGodam, TONGWEI                         |
| Telangana      | 5               | 5           | 3                | 464                    | 190          | 0      | 0      | Calibre, Practically, Cyient                         |
| Goa            | 4               | 1           | 3                | 520                    | 250          | 2      | 0      | Bolt                                                 |
| Uttarakhand    | 2               | 2           | 0                | 0                      |              | 0      | 0      | Medbros, Farmako                                     |
| Madhya Pradesh | 2               | 2           | 1                | 75                     | 75           | 1      | 1      | Gramophone, Embibe Education                         |
| California     | 1               | 1           | 1                | 80                     | 80           | 1      | 0      | Chegg                                                |
| Jharkhand      | 1               | 1           | 1                | 38                     | 38           | 1      | 0      | Tata Steel                                           |
| Kerala         | 1               | 1           | 0                | 0                      |              | 0      | 0      | Muthoot Finance                                      |
| Punjab         | 1               | 1           | 0                | 0                      |              | 0      | 0      | Superlearn                                           |

### Top 50 largest layoffs in the United States, 2019–2026

| #   | Date       | Company                   | Country       | Sector                          | Jobs cut   | % of workforce   | News reports   |
|:----|:-----------|:--------------------------|:--------------|:--------------------------------|:-----------|:-----------------|:---------------|
| 1   | 2022-07-29 | Amazon                    | United States | Retail                          | 99,000     | 3%               | 536            |
| 2   | 2025-10-28 | United Parcel Service     | United States | Business Services               | 48,000     |                  | 208            |
| 3   | 2023-12-26 | Citi                      | United States | Financial Services              | 40,000     |                  | 22             |
| 4   | 2020-07-08 | United Airlines           | United States | Travel and Hospitality          | 36,000     | 45%              | 86             |
| 5   | 2020-11-25 | Disney                    | United States | Media & Entertainment           | 32,000     |                  | 99             |
| 6   | 2026-01-21 | Oracle                    | United States | Enterprise Infrastructure       | 30,000     |                  | 178            |
| 7   | 2023-07-27 | Yellow                    | United States | Fintech                         | 30,000     |                  | 103            |
| 8   | 2026-01-09 | United Parcel Service     | United States | Business Services               | 30,000     |                  | 53             |
| 9   | 2020-09-29 | The Walt Disney Company   | United States | Media & Entertainment           | 28,000     | 67%              | 253            |
| 10  | 2024-06-21 | Tesla                     | United States | Environment Tech                | 28,000     | 10%              | 8              |
| 11  | 2024-03-01 | Boeing                    | United States | Aerospace, Maritime and Defense | 28,000     | 20%              | 2              |
| 12  | 2024-03-01 | AT&T                      | United States | Telecom                         | 27,400     | 13%              | 5              |
| 13  | 2022-02-15 | Amazon.com Inc            | United States |                                 | 27,000     |                  | 27             |
| 14  | 2020-03-20 | United Airlines           | United States | Travel and Hospitality          | 27,000     | 60%              | 4              |
| 15  | 2020-11-18 | Boeing                    | United States | Aerospace, Maritime and Defense | 26,000     |                  | 3              |
| 16  | 2023-07-26 | Amazon                    | United States | Retail                          | 25,000     |                  | 11             |
| 17  | 2024-12-20 | Google                    | United States | High Tech                       | 25,000     | 10%              | 8              |
| 18  | 2023-11-06 | Citi                      | United States | Financial Services              | 24,000     | 10%              | 23             |
| 19  | 2025-08-09 | HP                        | United States | Consumer Goods                  | 22,700     |                  | 1              |
| 20  | 2022-10-12 | Intel                     | United States | Semiconductors                  | 22,000     | 20%              | 46             |
| 21  | 2025-10-08 | Intel                     | United States | Semiconductors                  | 22,000     |                  | 4              |
| 22  | 2025-04-23 | Intel                     | United States | Semiconductors                  | 21,000     | 20%              | 37             |
| 23  | 2020-07-23 | Schlumberger              | United States |                                 | 21,000     | 20%              | 21             |
| 24  | 2023-01-14 | Wells Fargo               | United States | Financial Services              | 21,000     |                  | 1              |
| 25  | 2025-04-29 | United Parcel Service     | United States | Business Services               | 20,000     | 4%               | 152            |
| 26  | 2023-07-27 | Meta                      | United States | High Tech                       | 20,000     |                  | 7              |
| 27  | 2020-05-05 | Sysco                     | United States | Retail                          | 20,000     | 33%              | 3              |
| 28  | 2024-02-27 | Chrysler                  | United States | Auto                            | 20,000     |                  | 3              |
| 29  | 2026-02-05 | Citi                      | United States | Financial Services              | 20,000     | 10%              | 2              |
| 30  | 2023-10-20 | large US bank             | United States |                                 | 20,000     |                  | 1              |
| 31  | 2023-01-06 | Accenture                 | United States | Investment Industry             | 19,000     | 2.5%             | 141            |
| 32  | 2022-11-23 | Amazon.com Inc            | United States |                                 | 18,000     |                  | 113            |
| 33  | 2020-07-28 | MGM Resorts International | United States | Travel and Hospitality          | 18,000     |                  | 28             |
| 34  | 2020-04-01 | Craftworks Holdings       | United States | Food and Agriculture            | 18,000     |                  | 6              |
| 35  | 2020-05-30 | Amtrak                    | United States | Travel and Hospitality          | 18,000     |                  | 1              |
| 36  | 2023-05-10 | Toyota                    | United States | Auto                            | 18,000     |                  | 1              |
| 37  | 2020-06-05 | Cinemark Holdings         | United States |                                 | 17,500     |                  | 1              |
| 38  | 2024-10-10 | Boeing                    | United States | Aerospace, Maritime and Defense | 17,000     | 10%              | 319            |
| 39  | 2020-07-14 | Southwest Airlines        | United States | Travel and Hospitality          | 17,000     | 14%              | 5              |
| 40  | 2023-10-02 | VMware                    | United States | Enterprise Infrastructure       | 17,000     |                  | 1              |
| 41  | 2020-08-27 | United Airlines           | United States | Travel and Hospitality          | 16,370     | 21%              | 58             |
| 42  | 2025-12-15 | Amazon                    | United States | Retail                          | 16,000     | 8.5%             | 112            |
| 43  | 2020-03-25 | Boeing                    | United States | Aerospace, Maritime and Defense | 16,000     | 10%              | 96             |
| 44  | 2026-01-31 | Amazon                    | United States | Retail                          | 16,000     |                  | 34             |
| 45  | 2019-02-19 | Payless Shoesource        | United States | Retail                          | 16,000     |                  | 15             |
| 46  | 2025-09-23 | One Company               | United States |                                 | 16,000     |                  | 1              |
| 47  | 2020-07-01 | Bloomin' Brands           | United States | Food and Agriculture            | 15,600     |                  | 1              |
| 48  | 2024-07-31 | Intel                     | United States | Semiconductors                  | 15,000     | 5%               | 314            |
| 49  | 2025-11-13 | Verizon Communications    | United States | Telecom                         | 15,000     | 15%              | 66             |
| 50  | 2025-10-27 | Amazon                    | United States | Retail                          | 14,000     | 10%              | 125            |

### US layoffs by sector (top 25)

| Sector                             | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | 2023   | 2025   | Largest layoffs                                              |
|:-----------------------------------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:-------|:-------|:-------------------------------------------------------------|
| Retail                             | 416             | 220         | 259              | 623,326                | 200          | 64     | 60     | Amazon, Kohl, Gap                                            |
| Food and Agriculture               | 372             | 250         | 223              | 186,053                | 140          | 35     | 81     | Cheesecake Factory, Craftworks Holdings, Bloomin' Brands     |
| Consumer                           | 342             | 203         | 198              | 98,775                 | 140          | 84     | 29     | Google Korea, Davids Bridal, LIDS Sports Group               |
| Media & Entertainment              | 328             | 190         | 170              | 247,937                | 100          | 72     | 39     | Disney, The Walt Disney Company, Sony Pictures Entertainment |
| Healthcare                         | 317             | 198         | 195              | 90,815                 | 150          | 59     | 63     | Tenet Healthcare, Pfizer, Walgreens                          |
| Consumer Goods                     | 315             | 218         | 190              | 142,568                | 161          | 52     | 62     | HP, Eastman Kodak Company, Gymboree                          |
| Life Sciences                      | 310             | 246         | 134              | 21,268                 | 74           | 105    | 45     | NGM Biopharmaceuticals, Dentsply Sirona, Cepheid             |
| Business Services                  | 309             | 231         | 143              | 204,791                | 164          | 65     | 53     | United Parcel Service, Uber Technologies, IRS                |
| Enterprise Applications            | 292             | 209         | 152              | 95,773                 | 152          | 99     | 39     | Salesforce, Assembler, VIA                                   |
| Financial Services                 | 280             | 166         | 165              | 246,279                | 230          | 62     | 35     | Citi, Wells Fargo, Cognizant                                 |
| Fintech                            | 249             | 173         | 131              | 86,567                 | 125          | 82     | 22     | Yellow, PayPal, Intuit                                       |
| Enterprise Infrastructure          | 198             | 108         | 123              | 208,924                | 250          | 69     | 33     | Oracle, VMware, Dell Technologies                            |
| Auto                               | 191             | 120         | 128              | 174,359                | 318          | 30     | 37     | Chrysler, Toyota, Nissan                                     |
| High Tech                          | 187             | 105         | 105              | 164,133                | 170          | 53     | 26     | Google, Meta, Peloton                                        |
| Healthtech                         | 136             | 94          | 69               | 22,076                 | 90           | 34     | 19     | IPG, Cerebral, nThrive                                       |
| Energy                             | 130             | 88          | 74               | 44,284                 | 187          | 8      | 35     | GE, Halliburton, ConocoPhillips                              |
| Travel and Hospitality             | 124             | 71          | 76               | 207,650                | 405          | 2      | 16     | United Airlines, Amtrak, MGM Resorts International           |
| Food and Agriculture Tech          | 118             | 80          | 71               | 25,388                 | 110          | 30     | 14     | Getir, Waitr, Instacart                                      |
| Real Estate and Construction       | 103             | 72          | 52               | 31,570                 | 191          | 13     | 23     | CRH, John Deere, LL Flooring                                 |
| Gaming                             | 100             | 65          | 40               | 10,617                 | 60           | 25     | 13     | Blizzard Entertainment, Electronic Arts, Epic Games          |
| Industrial Goods and Manufacturing | 98              | 64          | 53               | 13,454                 | 112          | 19     | 19     | Emerson, International Paper, ARC                            |
| Semiconductors                     | 90              | 47          | 66               | 125,310                | 310          | 22     | 22     | Intel, Micron, Spansion                                      |
| Transportation and Logistics       | 87              | 63          | 50               | 27,698                 | 118          | 8      | 19     | Express, GE Aviation, Central Freight                        |
| Energy Tech                        | 82              | 53          | 43               | 10,851                 | 150          | 11     | 15     | BlueOval SK, One, Rivian                                     |
| Aerospace, Maritime and Defense    | 80              | 35          | 56               | 148,734                | 357          | 7      | 16     | Boeing, Raytheon, Pan Am Historical Foundation               |

### US layoffs by company HQ state (top 25)

HQ location from the company database.

| US state             | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | 2023   | 2025   | Largest layoffs                                           |
|:---------------------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:-------|:-------|:----------------------------------------------------------|
| California           | 1,485           | 924         | 850              | 959,674                | 150          | 403    | 177    | Disney, Gap, Cheesecake Factory                           |
| New York             | 679             | 406         | 369              | 379,847                | 117          | 147    | 100    | Citi, Accenture, Verizon Communications                   |
| Texas                | 354             | 202         | 200              | 346,928                | 226          | 52     | 65     | Oracle, Tesla, AT&T                                       |
| Massachusetts        | 293             | 210         | 154              | 50,375                 | 129          | 93     | 45     | Raytheon, Encore Boston Harbor, Wayfair                   |
| Illinois             | 208             | 130         | 127              | 144,866                | 200          | 40     | 26     | United Airlines, Walgreens, Allstate                      |
| Washington           | 207             | 119         | 116              | 277,451                | 194          | 39     | 35     | Amazon, Nordstrom, T-Mobile                               |
| Pennsylvania         | 179             | 117         | 95               | 73,927                 | 187          | 36     | 24     | Alcoa, Davids Bridal, Unisys                              |
| Michigan             | 175             | 100         | 102              | 154,327                | 370          | 34     | 38     | Chrysler, Continental, Ford                               |
| Georgia              | 147             | 89          | 79               | 155,219                | 180          | 18     | 27     | United Parcel Service, IPG, Limited Brands                |
| Ohio                 | 143             | 98          | 80               | 45,579                 | 160          | 18     | 29     | GE, GE Aviation, Block Communications                     |
| Florida              | 134             | 94          | 78               | 78,414                 | 158          | 22     | 23     | Bloomin' Brands, Office Depot, Hertz                      |
| North Carolina       | 131             | 77          | 73               | 25,033                 | 160          | 31     | 24     | Sonic Automotive, Golden Corral, Dentsply Sirona          |
| Colorado             | 118             | 88          | 52               | 9,060                  | 96           | 28     | 14     | Western Union, Liberty Energy, ARC                        |
| New Jersey           | 115             | 71          | 70               | 58,763                 | 231          | 24     | 25     | Cognizant, American, Union Carbide                        |
| Minnesota            | 95              | 54          | 50               | 85,584                 | 216          | 19     | 23     | Best Buy, 3M, Target                                      |
| Virginia             | 89              | 52          | 52               | 129,689                | 258          | 13     | 16     | Boeing, Hilton, LL Flooring                               |
| Wisconsin            | 88              | 59          | 54               | 99,392                 | 120          | 11     | 16     | Kohl, Shopko, Daybreak Foods, Inc.                        |
| Maryland             | 71              | 41          | 40               | 20,540                 | 154          | 12     | 14     | Under Armour, Pebblebrook Hotel, Farmers Restaurant Group |
| Connecticut          | 64              | 41          | 38               | 7,284                  | 106          | 9      | 7      | Charter Communications, Pitney Bowes, Lovesac             |
| Missouri             | 64              | 42          | 35               | 18,273                 | 227          | 10     | 14     | Amdocs, Emerson, SSM Health                               |
| District of Columbia | 62              | 36          | 33               | 43,599                 | 200          | 14     | 17     | Amtrak, HHS, IRS                                          |
| Oregon               | 61              | 38          | 35               | 19,132                 | 225          | 5      | 7      | OLA, Nike, Vacasa                                         |
| Indiana              | 55              | 42          | 35               | 21,457                 | 207          | 9      | 6      | LIDS Sports Group, Lowe, Nhk Seating                      |
| Arizona              | 52              | 30          | 29               | 19,450                 | 331          | 11     | 9      | Carvana, ON Semiconductor, GEICO                          |
| Arkansas             | 47              | 16          | 32               | 21,466                 | 253          | 7      | 6      | Tyson Foods, Walmart, Pace Industries                     |

### Top 50 largest layoffs in the United Kingdom, 2019–2026

| #   | Date       | Company          | Country        | Sector                            | Jobs cut   | % of workforce   | News reports   |
|:----|:-----------|:-----------------|:---------------|:----------------------------------|:-----------|:-----------------|:---------------|
| 1   | 2023-04-22 | Bt Group         | United Kingdom |                                   | 55,000     |                  | 94             |
| 2   | 2020-02-18 | HSBC             | United Kingdom | Financial Services                | 35,000     | 15%              | 136            |
| 3   | 2020-08-03 | HSBC             | United Kingdom | Financial Services                | 35,000     |                  | 2              |
| 4   | 2020-03-17 | BritishAirways   | United Kingdom | Travel and Hospitality            | 28,000     | 80%              | 228            |
| 5   | 2025-07-28 | TCS              | United Kingdom | Real Estate and Construction      | 20,000     | 2%               | 62             |
| 6   | 2026-03-19 | HSBC             | United Kingdom | Financial Services                | 20,000     | 10%              | 10             |
| 7   | 2022-06-09 | Swissport        | United Kingdom |                                   | 20,000     |                  | 1              |
| 8   | 2021-03-24 | CIL              | United Kingdom | Financial Services                | 18,600     |                  | 1              |
| 9   | 2020-03-27 | Menzies          | United Kingdom | Financial Services                | 17,500     |                  | 4              |
| 10  | 2026-02-12 | WPP              | United Kingdom | Business Services                 | 17,500     | 8.7%             | 3              |
| 11  | 2019-09-26 | Pearson          | United Kingdom | Education                         | 16,000     |                  | 1              |
| 12  | 2023-05-10 | British Telecom  | United Kingdom |                                   | 15,000     | 40%              | 5              |
| 13  | 2026-01-01 | Microsoft        | United Kingdom | Enterprise Infrastructure         | 15,000     |                  | 3              |
| 14  | 2020-09-10 | BritishAirways   | United Kingdom | Travel and Hospitality            | 13,000     | 33.33%           | 10             |
| 15  | 2025-05-28 | TCS              | United Kingdom | Real Estate and Construction      | 12,200     | 2%               | 416            |
| 16  | 2019-05-13 | Ford             | United Kingdom | Auto                              | 12,000     | 10%              | 127            |
| 17  | 2020-12-01 | Debenhams        | United Kingdom | Retail                            | 12,000     |                  | 44             |
| 18  | 2025-09-29 | TCS              | United Kingdom | Real Estate and Construction      | 12,000     | 2%               | 27             |
| 19  | 2020-04-29 | IAG              | United Kingdom | Financial Services                | 12,000     |                  | 16             |
| 20  | 2020-05-20 | BritishAirways   | United Kingdom | Travel and Hospitality            | 12,000     | 25%              | 9              |
| 21  | 2020-04-29 | BA               | United Kingdom |                                   | 12,000     |                  | 4              |
| 22  | 2021-01-26 | Boohoo           | United Kingdom | Consumer                          | 12,000     |                  | 2              |
| 23  | 2020-09-29 | IAG              | United Kingdom |                                   | 12,000     |                  | 1              |
| 24  | 2026-01-12 | TCS              | United Kingdom | Real Estate and Construction      | 11,150     | 2%               | 28             |
| 25  | 2023-05-15 | Vodafone         | United Kingdom | Telecom                           | 11,000     | 10%              | 141            |
| 26  | 2023-01-05 | Meta             | United Kingdom | High Tech                         | 11,000     | 3%               | 133            |
| 27  | 2023-06-08 | Bt Group         | United Kingdom |                                   | 11,000     |                  | 3              |
| 28  | 2023-01-02 | Microsoft        | United Kingdom | Enterprise Infrastructure         | 10,000     | 5%               | 1,530          |
| 29  | 2020-06-08 | The BP Group     | United Kingdom | Energy                            | 10,000     | 14%              | 25             |
| 30  | 2019-10-06 | HSBC             | United Kingdom | Financial Services                | 10,000     |                  | 20             |
| 31  | 2023-09-27 | Meta             | United Kingdom | High Tech                         | 10,000     |                  | 5              |
| 32  | 2019-01-14 | Debenhams        | United Kingdom | Retail                            | 10,000     |                  | 3              |
| 33  | 2020-03-20 | Bourne Leisure   | United Kingdom |                                   | 10,000     |                  | 1              |
| 34  | 2023-05-09 | British Telecoms | United Kingdom |                                   | 10,000     |                  | 1              |
| 35  | 2023-09-26 | Wilko            | United Kingdom | Retail                            | 10,000     |                  | 1              |
| 36  | 2020-10-30 | BritishAirways   | United Kingdom | Travel and Hospitality            | 9,680      |                  | 1              |
| 37  | 2020-05-01 | Rolls-Royce      | United Kingdom | Aerospace, Maritime and Defense   | 9,000      | 15%              | 116            |
| 38  | 2019-01-27 | Tesco            | United Kingdom | Retail                            | 9,000      |                  | 33             |
| 39  | 2021-12-09 | Rolls-Royce      | United Kingdom | Aerospace, Maritime and Defense   | 8,500      |                  | 1              |
| 40  | 2020-11-05 | Marks & Spencer  | United Kingdom |                                   | 8,000      |                  | 2              |
| 41  | 2024-03-19 | Unilever         | United Kingdom | Conglomerates                     | 7,500      |                  | 106            |
| 42  | 2020-08-18 | M&S              | United Kingdom |                                   | 7,000      |                  | 8              |
| 43  | 2023-05-19 | Asda             | United Kingdom | Retail                            | 7,000      |                  | 1              |
| 44  | 2021-01-08 | Boots            | United Kingdom | Healthcare                        | 6,500      | 11%              | 1              |
| 45  | 2025-08-05 | BP               | United Kingdom |                                   | 6,200      | 15%              | 11             |
| 46  | 2022-10-14 | Royal Mail       | United Kingdom | Transportation and Logistics Tech | 6,000      |                  | 14             |
| 47  | 2024-02-13 | Corus            | United Kingdom | Financial Services                | 6,000      |                  | 2              |
| 48  | 2020-11-13 | Premier Inn      | United Kingdom |                                   | 6,000      |                  | 1              |
| 49  | 2020-12-11 | Rolls-Royce      | United Kingdom | Aerospace, Maritime and Defense   | 5,500      |                  | 1              |
| 50  | 2020-12-29 | Cineworld        | United Kingdom | Generic Company Lists             | 5,500      |                  | 1              |

### UK layoffs by sector (top 25)

| Sector                             | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | 2023   | 2025   | Largest layoffs                                  |
|:-----------------------------------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:-------|:-------|:-------------------------------------------------|
| Retail                             | 192             | 91          | 99               | 111,750                | 310          | 32     | 32     | Debenhams, Wilko, Tesco                          |
| Food and Agriculture               | 153             | 105         | 86               | 53,166                 | 298          | 18     | 21     | Upper Crust, Pret, Revolution Bars Group         |
| Financial Services                 | 143             | 75          | 85               | 199,998                | 400          | 22     | 19     | HSBC, CIL, Menzies                               |
| Consumer Goods                     | 126             | 80          | 71               | 36,415                 | 133          | 15     | 22     | Arcadia Group, Dorothy Perkins, Burberry         |
| Business Services                  | 126             | 102         | 50               | 34,117                 | 150          | 15     | 29     | WPP, PDV, Exertis                                |
| Real Estate and Construction       | 78              | 52          | 42               | 79,867                 | 250          | 15     | 7      | TCS, Premier Retail Solutions, Carillion         |
| Auto                               | 71              | 48          | 48               | 68,170                 | 302          | 6      | 8      | Jaguar Land Rover, Ford, First Brands Group      |
| Travel and Hospitality             | 68              | 42          | 42               | 105,867                | 693          | 3      | 3      | BritishAirways, Swissport, easyJet               |
| Consumer                           | 66              | 47          | 34               | 31,700                 | 304          | 6      | 7      | Boohoo, British Gas, SNAP                        |
| Fintech                            | 59              | 48          | 27               | 12,306                 | 200          | 14     | 4      | SSP Worldwide, Travelex, Capital One             |
| Media & Entertainment              | 56              | 39          | 21               | 10,362                 | 300          | 8      | 12     | SKY, BBC, Reach                                  |
| Energy                             | 39              | 28          | 16               | 23,537                 | 275          | 4      | 8      | The BP Group, Centrica, Applegreen               |
| Enterprise Infrastructure          | 34              | 14          | 18               | 33,608                 | 238          | 9      | 4      | Microsoft, Sophos, Kape                          |
| Enterprise Applications            | 33              | 25          | 15               | 5,034                  | 130          | 9      | 5      | Rio, Aurora, Sumo                                |
| Healthcare                         | 30              | 19          | 19               | 18,614                 | 180          | 9      | 2      | Boots, AstraZeneca, Evoke                        |
| Aerospace, Maritime and Defense    | 25              | 10          | 22               | 38,878                 | 550          | 3      | 1      | Rolls-Royce, GKN Aerospace, Airbus               |
| Gaming                             | 25              | 20          | 7                | 495                    | 40           | 1      | 8      | Ubisoft, Square Enix, Supermassive Games         |
| Energy Tech                        | 22              | 16          | 11               | 6,898                  | 230          | 7      | 2      | OVO Energy, Arrival, Arcadia                     |
| High Tech                          | 22              | 19          | 10               | 23,002                 | 175          | 3      | 4      | Meta, Lloyds, Renishaw                           |
| Conglomerates                      | 21              | 12          | 9                | 14,725                 | 350          | 4      | 4      | Unilever, ALDI, APi Group                        |
| Telecom                            | 18              | 11          | 8                | 12,976                 | 358          | 5      | 4      | Vodafone, OneWeb, CityFibre                      |
| Food and Agriculture Tech          | 18              | 11          | 12               | 6,819                  | 384          | 3      | 2      | Just Eat, Just Eat Takeaway, Ocado Group         |
| Industrial Goods and Manufacturing | 17              | 16          | 12               | 4,349                  | 180          | 3      | 1      | ISG, Liberty Steel, Senior                       |
| Semiconductors                     | 17              | 11          | 9                | 3,512                  | 118          | 2      | 2      | AMD, Arm, Vishay Intertechnology                 |
| Chemicals and Materials            | 15              | 11          | 9                | 14,285                 | 1,500        | 3      | 2      | Tata Steel, Johnson Matthey, LIBERTY Steel Group |

### UK layoffs by company HQ city (top 25)

HQ location from the company database.

| UK city             | Layoff events   | Companies   | With headcount   | Jobs cut (disclosed)   | Median cut   | 2023   | 2025   | Largest layoffs                               |
|:--------------------|:----------------|:------------|:-----------------|:-----------------------|:-------------|:-------|:-------|:----------------------------------------------|
| London              | 535             | 318         | 272              | 400,910                | 300          | 82     | 71     | HSBC, CIL, WPP                                |
| Manchester          | 31              | 21          | 13               | 6,176                  | 160          | 7      | 3      | Revolution Bars Group, Boohoo Group, Timpson  |
| Cambridge           | 31              | 8           | 16               | 38,072                 | 780          | 7      | 5      | Microsoft, AstraZeneca, Arm                   |
| Leeds               | 30              | 11          | 15               | 66,168                 | 638          | 6      | 5      | TCS, Asda, Direct Line                        |
| Edinburgh           | 26              | 17          | 14               | 3,392                  | 250          | 3      | 7      | Harbour Energy, NatWest Group, Abrdn          |
| Birmingham          | 24              | 12          | 15               | 11,345                 | 284          | 4      | 3      | Patisserie-Valerie, GKN Aerospace, Unity      |
| Bristol             | 21              | 17          | 10               | 5,560                  | 141          | 2      | 2      | OVO Energy, Imperial Brands, Atkins           |
| Nottingham          | 20              | 9           | 14               | 15,327                 | 300          | 1      | 2      | Boots, Pendragon, Capital One                 |
| Glasgow             | 19              | 15          | 9                | 1,005                  | 90           | 3      | 1      | ScottishPower, Quiz, North                    |
| Coventry            | 13              | 6           | 9                | 28,629                 | 500          | 1      | 2      | Jaguar Land Rover, JLR, HPL                   |
| Bradford            | 13              | 2           | 7                | 2,684                  | 270          | 3      | 4      | Morrisons, Kaleidoscope                       |
| Liverpool           | 12              | 9           | 4                | 690                    | 125          | 4      | 1      | Pentland Brands, Princes, Real Good Food      |
| Norwich             | 11              | 6           | 9                | 4,044                  | 90           | 2      | 1      | SNAP, Lotus Cars, Jarrold & Sons              |
| Sheffield           | 11              | 10          | 6                | 3,152                  | 172          | 1      | 4      | Tuffnells Parcels, National Timber Group, SIG |
| Leicester           | 11              | 8           | 2                | 555                    | 278          | 0      | 3      | Walkers, Sbs Print Group, Shoe Zone           |
| Crawley             | 10              | 5           | 6                | 8,528                  | 800          | 0      | 1      | Virgin Atlantic, Evans Cycles, Edwards Vacuum |
| Welwyn Garden City  | 10              | 2           | 7                | 18,251                 | 1,816        | 1      | 0      | Tesco, Ramblersholidays.Co                    |
| Solihull            | 10              | 3           | 4                | 627                    | 120          | 1      | 1      | Gymshark, Purplebricks, Tarmac                |
| Scunthorpe          | 10              | 3           | 7                | 8,510                  | 500          | 3      | 1      | British Steel, Clugston, TSC Foods            |
| Holborn             | 9               | 2           | 7                | 10,861                 | 1,500        | 0      | 3      | Sainsbury's, Octopus Investments              |
| Milton Keynes       | 8               | 4           | 5                | 682                    | 120          | 0      | 3      | Monarch Aircraft Engineering, Sodexo, Amscan  |
| Newcastle Upon Tyne | 8               | 7           | 4                | 911                    | 48           | 0      | 0      | Greggs, BEL Valves, Fentimans                 |
| Salford             | 8               | 2           | 5                | 3,780                  | 650          | 1      | 3      | Kier, TalkTalk                                |
| Reading             | 8               | 6           | 2                | 1,650                  | 825          | 0      | 1      | Pretty Green, Thames Water, Bullitt Group     |
| Swindon             | 8               | 7           | 3                | 2,800                  | 1,200        | 1      | 2      | WHSmith, National Trust, Cambria Automobiles  |

## Method

1. **Extraction.** Radar's pipeline reads each news article, finds sentences reporting job cuts and extracts company, headcount, share of workforce and country. Upstream, reports carrying the same event fingerprint are grouped and retrospective mentions are dropped.
2. **Window and dates.** The date is the publication date of the earliest report, read in Indian Standard Time; January 2019 to June 2026. Bulk archive back-fill days (over five times the usual volume) are dropped.
3. **Companies.** Descriptor prefixes are removed ("Tata Motors-owned Jaguar Land Rover" → Jaguar Land Rover). Rows naming a person, an unnamed or generic employer ("the company") or a whole sector ("IT companies") are dropped. A website is kept only when the company record matches the reported name.
4. **One row per layoff round.** Reports of the same company within 45 days of the round's first report (and not in a different stated country) are one event. Exact repeat sentences are removed first.
5. **Headcount and %.** A headcount is kept only when the same number (±2%, including "1.2 lakh", "10k", "a dozen") appears in the sentence; the earliest verified figure of the round is used. Headcounts above 150,000 are blanked. The share of workforce is kept only when the sentence states it (a percentage, "half", "a third").
6. **Countries.** `country` is the country where the cut happens as reported, else the company's home country; names are normalised (USA / US → United States).

7. **Sample.** Each company key is ranked by `sha1(key)`. Keys are taken in rank order until the file holds max(25%, 5,000) rows (capped at 100,000).

8. **Profile links.** Links are built from Fliar's company index and checked against it. A row whose company has no public profile has an empty link.

## Columns

| Column              | Description                                                                                                    |
|:--------------------|:---------------------------------------------------------------------------------------------------------------|
| `layoff_id`         | stable 12-character ID of the layoff event                                                                     |
| `date`              | date of the earliest news report (YYYY-MM-DD)                                                                  |
| `year`              | year                                                                                                           |
| `month`             | month (YYYY-MM)                                                                                                |
| `company_name`      | company (organisations only)                                                                                   |
| `company_domain`    | company website domain (join key for the API; blank when unknown)                                              |
| `country`           | country where the layoff happens as reported, else the company's home country                                  |
| `company_country`   | company headquarters country                                                                                   |
| `company_state`     | HQ state (US state, Indian state or UK nation; blank elsewhere)                                                |
| `company_city`      | HQ city (blank when unknown)                                                                                   |
| `sector`            | Fliar sector label of the company                                                                              |
| `headcount_cut`     | jobs cut, when stated and verified in the sentence                                                             |
| `headcount_status`  | verified / failed_check / not_disclosed                                                                        |
| `pct_workforce`     | share of the workforce cut in %, when stated in the sentence                                                   |
| `is_furlough`       | True when the reports describe furloughs, short-time work or temporary lay-offs rather than permanent job cuts |
| `news_mentions`     | news reports of the layoff                                                                                     |
| `news_source`       | publisher of the article (website domain)                                                                      |
| `news_url`          | link to the article                                                                                            |
| `news_excerpt`      | the sentence the layoff was extracted from (up to 300 characters)                                              |
| `fliar_profile_url` | full company profile on Fliar (financials, funding, team, news)                                                |

**Available only through the [Radar API](https://github.com/fliarbi/radar-api-mcp):** reason for the layoff; affected departments and regions; severance and rehiring details; workforce size before the cut; every article that reported the layoff; the other companies' layoffs; company profile, financials, hiring and contacts.

## Limitations

- Derived from news: unreported layoffs are missing, and coverage favours large companies and English-language media; India and Europe are well covered, many emerging markets thinly.
- ClickHouse shards were partially unavailable at build time (shard 2 down; queries skip unavailable shards), so some layoffs may be missing. Article links resolve for roughly half of the rows because some article-store nodes were down.
- Many reports give no headcount, or a figure that could not be verified; jobs-cut totals sum only verified headcounts and understate the true total.
- Merging is automatic: two separate rounds at one company within 45 days count as one, and a long-running restructuring may be split.
- Sector and HQ location are known only for companies matched to the company database.
- News ingest thins after May 2026; 2026 covers January to June only.

## Citation

Fliar Research (2026). *Layoffs Dataset 2019–2026: Global, India, US, UK* (sample release). Data: Radar API, https://github.com/fliarbi/radar-api-mcp. Licence CC BY-NC 4.0.
