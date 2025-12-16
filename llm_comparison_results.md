# LLM Comparison Results

## Performance & Cost Analysis

| Model | Total Time | Avg Time/Run | Total Input Tokens | Total Output Tokens | Avg Input/Run | Avg Output/Run | Total Cost | Avg Cost/Run |
|-------|----------:|-----------:|------------------:|-------------------:|-------------:|-------------:|----------:|------------:|
| LLAMA_70B | 137.24s | 10.56s | 12,865 | 535 | 989.6 | 41.2 | FREE | FREE |
| GPT_35_TURBO | 136.11s | 10.47s | 12,553 | 423 | 965.6 | 32.5 | $0.006911 | $0.000532 |
| GPT_4 | 161.12s | 12.39s | 12,546 | 584 | 965.1 | 44.9 | $0.411420 | $0.031648 |

---

## LLAMA_70B

| Question | Response | Time Taken | Input Tokens | Output Tokens |
|----------|----------|------------|--------------|---------------|
| how many points did  cr7 score in last seasons | I don't know.... | 11.27 seconds | 370 | 6 |
| tell me forwards from the gunners | The forwards from the Gunners are Folarin Balogun and Pierre-Emerick Aubameyang.... | 11.33 seconds | 364 | 23 |
| Who is Momo Salah? | Mohamed Salah is a midfielder in the Fantasy Premier League.... | 10.43 seconds | 376 | 13 |
| Top forwards in 2022/23 season | The top forwards in the 2022/23 season are:  1. Erling Haaland with 272 points 2. Harry Kane with 26... | 10.63 seconds | 583 | 59 |
| Show me stats and goals for kdb in 2022-23 | Based on the available context, Kevin De Bruyne's stats for the 2022-23 season are:  - Goals: 7 - As... | 10.54 seconds | 366 | 42 |
| How many points did Haaland get in GW 3 2022-23? | I don't know.... | 10.39 seconds | 365 | 6 |
| Tell me about spurs | Spurs have played 38 matches, scored 130 goals, and had 112 assists, earning a total of 3132 points.... | 11.57 seconds | 361 | 74 |
| give me 4 midfielders from arsenal | Based on the provided context, here are 4 midfielders from Arsenal:  1. Bukayo Saka 2. Granit Xhaka ... | 11.66 seconds | 8024 | 43 |
| how did the egyption king perform  | The Egyptian player, Mohamed Salah, performed well, scoring 19 goals, providing 13 assists, and earn... | 10.52 seconds | 395 | 32 |
| Show me stats and goals for midfielders in 2022-23 | Based on the provided context, here are the stats for midfielders in the 2022-23 season:  1. Kevin D... | 11.27 seconds | 532 | 133 |
| who is halaand? | Erling Haaland is a forward (FWD) player with 272 total points for the season.... | 10.78 seconds | 383 | 23 |
| compare between mohamed salah and harry kane performance in 2021-22 season | Based on the provided context, in the 2021-22 season, Harry Kane scored 8 points, while Mohamed Sala... | 10.72 seconds | 370 | 55 |
| ايه هي ارقام صارؤخ ماضيلرا في الموسم اللي فات | لا تتوفر المعلومات حول أرقام صاروخ ماضيلرا في السياق المُقدم.... | 6.13 seconds | 376 | 26 |

## GPT_35_TURBO

| Question | Response | Time Taken | Input Tokens | Output Tokens |
|----------|----------|------------|--------------|---------------|
| how many points did  cr7 score in last seasons | I don't know.... | 10.74 seconds | 344 | 5 |
| tell me forwards from the gunners | Forwards from the Gunners in Fantasy Premier League are Folarin Balogun and Pierre-Emerick Aubameyan... | 10.53 seconds | 342 | 26 |
| Who is Momo Salah? | I don't know.... | 10.91 seconds | 308 | 5 |
| Top forwards in 2022/23 season | Top forwards in the 2022/23 season based on points are:  1. Erling Haaland - 272 points 2. Harry Kan... | 11.58 seconds | 561 | 65 |
| Show me stats and goals for kdb in 2022-23 | Kevin De Bruyne has scored 7 goals and provided 18 assists in the 2022-23 season, accumulating a tot... | 11.65 seconds | 344 | 35 |
| How many points did Haaland get in GW 3 2022-23? | Haaland got 6 points in GW 3 of the 2022-23 season.... | 10.85 seconds | 379 | 19 |
| Tell me about spurs | Spurs scored 130 goals, made 112 assists, totaling 3132 points over 38 matches. Some midfield player... | 11.03 seconds | 338 | 43 |
| give me 4 midfielders from arsenal | The four midfielders from Arsenal are Bukayo Saka, Emile Smith Rowe, Granit Xhaka, and Thomas Partey... | 10.99 seconds | 8005 | 28 |
| how did the egyption king perform  | I don't have specific information on the performance of the Egyptian king in Fantasy Premier League ... | 6.91 seconds | 346 | 48 |
| Show me stats and goals for midfielders in 2022-23 | I don't have specific goal data available for midfielders in the 2022-23 season in the provided cont... | 11.7 seconds | 510 | 70 |
| who is halaand? | I don't know.... | 10.85 seconds | 364 | 5 |
| compare between mohamed salah and harry kane performance in 2021-22 season | In the 2021-22 season, Harry Kane scored 8 points, while Mohamed Salah scored 4 points in Fantasy Pr... | 12.22 seconds | 349 | 69 |
| ايه هي ارقام صارؤخ ماضيلرا في الموسم اللي فات | I don't know.... | 6.15 seconds | 363 | 5 |

## GPT_4

| Question | Response | Time Taken | Input Tokens | Output Tokens |
|----------|----------|------------|--------------|---------------|
| how many points did  cr7 score in last seasons | I'm sorry, but the provided context does not include information on the number of points Cristiano R... | 11.94 seconds | 343 | 30 |
| tell me forwards from the gunners | The forwards from the Gunners (Arsenal FC) are Folarin Balogun and Pierre-Emerick Aubameyang.... | 12.11 seconds | 342 | 27 |
| Who is Momo Salah? | "Momo Salah" is a nickname for Mohamed Salah, who is a midfielder in the Fantasy Premier League.... | 11.8 seconds | 309 | 21 |
| Top forwards in 2022/23 season | The top forwards in the 2022/23 season are:  1. Erling Haaland with 272 points 2. Harry Kane with 26... | 13.15 seconds | 561 | 64 |
| Show me stats and goals for kdb in 2022-23 | In the 2022-23 season, Kevin De Bruyne, who plays in the MID position, scored 7 goals and provided 1... | 11.55 seconds | 344 | 39 |
| How many points did Haaland get in GW 3 2022-23? | I'm sorry, but I don't have the specific information on the number of points Erling Haaland scored i... | 11.37 seconds | 343 | 35 |
| Tell me about spurs | Spurs, also known as Tottenham Hotspur, had played 38 matches with a total of 130 goals and 112 assi... | 13.83 seconds | 339 | 57 |
| give me 4 midfielders from arsenal | The four midfielders from Arsenal are Bukayo Saka, Emile Smith Rowe, Fábio Ferreira Vieira, and Gabr... | 13.03 seconds | 8005 | 31 |
| how did the egyption king perform  | Mohamed Salah, often referred to as the "Egyptian King", performed impressively. He scored 19 goals ... | 12.03 seconds | 373 | 37 |
| Show me stats and goals for midfielders in 2022-23 | I'm sorry, but the provided context does not include specific goal statistics for midfielders in the... | 14.62 seconds | 510 | 96 |
| who is halaand? | The player referred to as "Halaand" is likely Erling Haaland. He is a forward player and has scored ... | 12.82 seconds | 364 | 35 |
| compare between mohamed salah and harry kane performance in 2021-22 season | In the 2021-22 season, Harry Kane scored 8 points while Mohamed Salah scored 4 points. Salah plays i... | 11.74 seconds | 349 | 35 |
| ايه هي ارقام صارؤخ ماضيلرا في الموسم اللي فات | I'm sorry but I'll need more specific information to help properly. Your question seems to be asking... | 11.13 seconds | 364 | 77 |

