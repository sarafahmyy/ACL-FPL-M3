# LLM Comparison Results

## Performance & Cost Analysis

| Model | Total Time | Avg Time/Run | Total Input Tokens | Total Output Tokens | Avg Input/Run | Avg Output/Run | Total Cost | Avg Cost/Run |
|-------|----------:|-----------:|------------------:|-------------------:|-------------:|-------------:|----------:|------------:|
| LLAMA_70B | 149.14s | 11.47s | 12,786 | 454 | 983.5 | 34.9 | FREE | FREE |
| GPT_35_TURBO | 142.04s | 10.93s | 12,585 | 358 | 968.1 | 27.5 | $0.006830 | $0.000525 |
| GPT_4 | 170.98s | 13.15s | 12,550 | 474 | 965.4 | 36.5 | $0.404940 | $0.031149 |

---

## LLAMA_70B

| Question | Response | Time Taken | Input Tokens | Output Tokens |
|----------|----------|------------|--------------|---------------|
| how many points did  cr7 score in last seasons | I don't know.... | 11.68 seconds | 366 | 6 |
| tell me forwards from the gunners | The forwards from the Gunners (Arsenal) are Folarin Balogun and Pierre-Emerick Aubameyang.... | 11.44 seconds | 364 | 27 |
| Who is Momo Salah? | Mohamed Salah is a midfielder in the Fantasy Premier League.... | 21.26 seconds | 330 | 13 |
| Top forwards in 2022/23 season | The top forwards in the 2022/23 season are:  1. Erling Haaland with 272 points 2. Harry Kane with 26... | 10.71 seconds | 583 | 56 |
| Show me stats and goals for kdb in 2022-23 | For Kevin De Bruyne (kdb) in the 2022-23 season, he scored 7 goals.... | 10.96 seconds | 366 | 25 |
| How many points did Haaland get in GW 3 2022-23? | I don't know.... | 10.38 seconds | 365 | 6 |
| Tell me about spurs | The Spurs have played 38 matches, scoring 130 goals and providing 112 assists, resulting in a total ... | 11.3 seconds | 360 | 29 |
| give me 4 midfielders from arsenal | Based on the context provided, here are 4 midfielders from Arsenal:  1. Bukayo Saka 2. Granit Xhaka ... | 11.14 seconds | 8024 | 43 |
| how did the egyption king perform  | I don't know. The context provided does not contain information about an "Egyptian king" or their pe... | 11.34 seconds | 368 | 44 |
| Show me stats and goals for midfielders in 2022-23 | Based on the context, here are the midfielders' stats for the 2022-23 season:  1. Kevin De Bruyne - ... | 10.82 seconds | 532 | 104 |
| who is halaand? | Erling Haaland is a forward (FWD) player with a total of 272 points in the season.... | 10.96 seconds | 383 | 25 |
| compare between mohamed salah and harry kane performance in 2021-22 season | Based on the provided context, in the 2021-22 season, Harry Kane scored 8 points, while Mohamed Sala... | 10.54 seconds | 370 | 46 |
| ايه هي ارقام صارؤخ ماضيلرا في الموسم اللي فات | لا تتوفر معلومات عن أرقام صاروخ محمد صلاح في الموسم السابق في السياق المُقدم.... | 6.61 seconds | 375 | 30 |

## GPT_35_TURBO

| Question | Response | Time Taken | Input Tokens | Output Tokens |
|----------|----------|------------|--------------|---------------|
| how many points did  cr7 score in last seasons | I don't know.... | 10.67 seconds | 348 | 5 |
| tell me forwards from the gunners | The forwards from the Gunners are Folarin Balogun and Pierre-Emerick Aubameyang.... | 11.01 seconds | 342 | 22 |
| Who is Momo Salah? | Mohamed Salah is a midfielder in the Fantasy Premier League.... | 10.71 seconds | 308 | 12 |
| Top forwards in 2022/23 season | Top forwards in the 2022/23 season based on points are Erling Haaland with 272 points, followed by H... | 11.28 seconds | 561 | 41 |
| Show me stats and goals for kdb in 2022-23 | Kevin De Bruyne has scored 7 goals and provided 18 assists in the 2022-23 season, accumulating a tot... | 11.04 seconds | 344 | 33 |
| How many points did Haaland get in GW 3 2022-23? | Erling Haaland received 6 points in Gameweek 3 of the 2022-23 season.... | 11.34 seconds | 379 | 24 |
| Tell me about spurs | Spurs scored 130 goals and provided 112 assists in 38 matches, accumulating a total of 3132 points i... | 11.19 seconds | 338 | 55 |
| give me 4 midfielders from arsenal | The 4 midfielders from Arsenal are: 1. Bukayo Saka 2. Emile Smith Rowe 3. Granit Xhaka 4. Thomas Par... | 11.59 seconds | 8005 | 36 |
| how did the egyption king perform  | The Egyptian king, Mohamed Salah, had an impressive performance with 19 goals, 13 assists, and a tot... | 10.69 seconds | 373 | 30 |
| Show me stats and goals for midfielders in 2022-23 | I don't have the specific stats and goals data for midfielders in the 2022-23 season based on the pr... | 13.61 seconds | 510 | 27 |
| who is halaand? | I don't know.... | 10.73 seconds | 364 | 5 |
| compare between mohamed salah and harry kane performance in 2021-22 season | In the 2021-22 season, Harry Kane scored 8 points, while Mohamed Salah scored 4 points. Kane plays a... | 11.11 seconds | 349 | 63 |
| ايه هي ارقام صارؤخ ماضيلرا في الموسم اللي فات | I don't know.... | 7.07 seconds | 364 | 5 |

## GPT_4

| Question | Response | Time Taken | Input Tokens | Output Tokens |
|----------|----------|------------|--------------|---------------|
| how many points did  cr7 score in last seasons | I'm sorry, but the provided context doesn't give information about the number of points Cristiano Ro... | 11.53 seconds | 348 | 32 |
| tell me forwards from the gunners | The forwards from the Gunners (Arsenal) are Folarin Balogun and Pierre-Emerick Aubameyang.... | 12.54 seconds | 342 | 26 |
| Who is Momo Salah? | "Momo Salah" is likely referring to Mohamed Salah, a midfielder in the Premier League.... | 11.16 seconds | 308 | 18 |
| Top forwards in 2022/23 season | The top forwards in the 2022/23 season were Erling Haaland with 272 points, Harry Kane with 263 poin... | 13.23 seconds | 561 | 54 |
| Show me stats and goals for kdb in 2022-23 | Kevin De Bruyne (KDB) scored 7 goals and provided 18 assists in the 2022-23 season. He earned a tota... | 11.53 seconds | 344 | 35 |
| How many points did Haaland get in GW 3 2022-23? | I don't know.... | 11.25 seconds | 343 | 5 |
| Tell me about spurs | Spurs, also known as Tottenham Hotspur, is a team in the Premier League. In the last season, they pl... | 23.55 seconds | 338 | 79 |
| give me 4 midfielders from arsenal | The four midfielders from Arsenal are Bukayo Saka, Emile Smith Rowe, Fábio Ferreira Vieira, and Gabr... | 13.56 seconds | 8006 | 31 |
| how did the egyption king perform  | Mohamed Salah, often referred to as the "Egyptian King," had a fantastic performance. He scored 19 g... | 11.96 seconds | 373 | 38 |
| Show me stats and goals for midfielders in 2022-23 | I'm sorry, but the provided context does not include specific stats and goals for midfielders in the... | 13.83 seconds | 510 | 29 |
| who is halaand? | The player referred to as 'halaand' is presumably Erling Haaland, who plays as a forward. As of the ... | 13.77 seconds | 364 | 39 |
| compare between mohamed salah and harry kane performance in 2021-22 season | In the 2021-22 season, Harry Kane had a performance score of 8 points, while Mohamed Salah scored 4 ... | 14.54 seconds | 349 | 41 |
| ايه هي ارقام صارؤخ ماضيلرا في الموسم اللي فات | I'm sorry, but your question seems incomplete. It appears you're asking for past performance numbers... | 8.53 seconds | 364 | 47 |

