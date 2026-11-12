# Task 7: ask for three citations on a niche topic and verify them

Task: ask a model for three academic citations on a niche topic, check them, and record how many were invented.

Script: `day-4/tasks/task7_citations.py`. Raw replies and verdicts: `results/task7_citations.json`.
```bash
uv run python tasks/task7_citations.py
uv run python tasks/task7_citations.py --topic "my own niche topic" --models local gemini --prompts plain
```

## 1. Setup
- **Niche topic:** "tokenization efficiency of Gujarati text in multilingual large language models".
- **Models:** local `gemma3:270m`, hosted `gemini-3.1-flash-lite` (small), hosted `gemini-3.6-flash` (larger). Temperature 0.
- **Two prompts per model.**
  - *plain*: "Give me three academic citations on this topic ..."
  - *careful*: "... Only include a paper if you are certain it exists ... If you are not certain, return fewer papers, or an empty list."
  - Both ask for JSON with `authors`, `year`, `title`, `venue`, `doi`, so the answer can be read by code.
- **Automatic check:** for each citation the script searches the title in **Crossref** and **OpenAlex** (public scholarly databases), and looks up the DOI in Crossref. It compares title (similarity of at least 0.85), year and first author.
- **Then I checked by hand.** The script cannot tell "invented" from "a real paper cited with a slightly wrong title", so I searched OpenAlex myself for every citation it did not mark REAL.

## 2. What the models returned, and what I found (all 15 citations)
Local `gemma3:270m`, plain prompt (all three had the same DOI `10.1007/s42844-020-02777-0`):
| # | Citation as given | Finding |
|---|---|---|
| 1 | A.K. Sharma (2023). *Tokenization Efficiency of Gujarati Text in Multilingual Large Language Models*. | **Invented** (it just repeated my topic as a title); DOI does not exist |
| 2 | B.C. Patel (2022). *The Impact of Language Modeling on the Performance of Large Language Models*. | **Invented**; DOI does not exist |
| 3 | D.E. Verma (2021). *Challenges in Handling Multilingual Text in Large Language Models*. | **Invented**; DOI does not exist |

Local `gemma3:270m`, careful prompt (all three had the same DOI `10.1007/jnh147878`, venue "The University of California, Berkeley"):
| # | Citation as given | Finding |
|---|---|---|
| 1 | A.K. Sharma (2023). *Tokenization Efficiency of Gujarati Text ...* | **Invented** |
| 2 | A.K. Sharma (2022). *Challenges in Tokenization of Gujarati Text ...* | **Invented** |
| 3 | A.K. Sharma (2021). *The Impact of Tokenization on Text Comprehension ...* | **Invented** |

`gemini-3.1-flash-lite`, plain prompt:
| # | Citation as given | Finding |
|---|---|---|
| 1 | Murthy, Kunchukuttan, Bhattacharyya (2018). *IndicNLP Suite: Multilingual Resources for Indian Languages*. COLING | **Real paper, wrong details.** The nearest real paper is *IndicNLPSuite: Monolingual Corpora, Evaluation Benchmarks and Pre-trained Multilingual Language Models for Indian Languages* (Kakwani, Kunchukuttan, Golla et al., 2020, Findings of EMNLP). Authors, year, venue and title all differ |
| 2 | Khapra, Kunchukuttan, Kumar (2020). *AI4Bharat: Building Datasets and Models for Indian Languages*. EMNLP, DOI `10.18653/v1/2020.emnlp-main.350` | **Invented.** That DOI is a different paper ("Do sequence-to-sequence VAEs learn global features of sentences?") |
| 3 | Doddapaneni, Ramesh, Kunchukuttan (2023). *Towards Building Large Language Models for Indian Languages*. ACL, DOI `10.18653/v1/2023.acl-long.535` | **Invented.** That DOI is "I2D2: Inductive Knowledge Distillation with NeuroLogic and Self-Imitation" |

`gemini-3.1-flash-lite`, careful prompt:
| # | Citation as given | Finding |
|---|---|---|
| 1 | Kumar, Lahiri, Ojha (2022). *Challenges in Tokenization for Indian Languages: A Case Study of Gujarati*. ICON | **Invented** (no such paper in either database) |
| 2 | Khapra, Kunchukuttan, Kumar (2020). *IndicNLP Suite ...*. COLING, DOI `10.18653/v1/2020.coling-main.272` | **Invented** as written; the DOI is a different paper ("Learning Semantic Correspondences from Noisy Data-text Pairs ...") |
| 3 | Doddapaneni, Ramesh, Krishnan (2023). *Towards Building Large Language Models for Indic Languages*. arXiv:2305.15733 | **Invented.** I looked up the arXiv number: `2305.15733` is "Black hole scalarizations induced by parity violations" |

`gemini-3.6-flash`, plain prompt:
| # | Citation as given | Finding |
|---|---|---|
| 1 | Ahia, Marchio, Kreutzer (2023). *Do All Languages Cost the Same? Tokenization in the Era of Commercial Language Models*. EMNLP, DOI `...emnlp-main.621` | **Real paper, wrong details.** Title, year, venue and first author are right. Real authors are Ahia, **Kumar, Gonen** and others (not Marchio, Kreutzer). The real DOI is `...emnlp-main.614`; `.621` is "Rethinking the Evaluation for Conversational Recommendation ..." |
| 2 | Khan, Shah, Kumar et al. (2024). *IndicLLMSuite: In-Domain Pre-trained Models and Datasets for Indian Languages*. TACL, DOI `10.1162/tacl_a_00672` | **Real paper, wrong details.** Real: *IndicLLMSuite: A Blueprint for Creating Pre-training and Fine-Tuning Datasets for Indian Languages*, ACL 2024, authors Khan, Mehta, Sankar et al., DOI `...2024.acl-long.843`. The TACL DOI belongs to a speech paper |
| 3 | Doddapaneni, Aralikatte, Ramesh et al. (2023). *Towards Leaving No Indic Language Behind: Analyzing Tokenization and Modeling Inefficiencies ...*. ACL | **Real paper, wrong details.** Real subtitle: *Building Monolingual Corpora, Benchmark and Models for Indic Languages*, DOI `...2023.acl-long.693`. The given `.682` is a different paper. First three authors are right |

`gemini-3.6-flash`, careful prompt: the model replied `[]`, an empty list. It declined to name any paper.

## 3. The count
| Model and prompt | Citations given | Fully correct | Real paper, details wrong | Invented |
|---|---|---|---|---|
| `gemma3:270m` plain | 3 | 0 | 0 | **3** |
| `gemma3:270m` careful | 3 | 0 | 0 | **3** |
| `gemini-3.1-flash-lite` plain | 3 | 0 | 1 | **2** |
| `gemini-3.1-flash-lite` careful | 3 | 0 | 0 | **3** |
| `gemini-3.6-flash` plain | 3 | 0 | 3 | 0 |
| `gemini-3.6-flash` careful | 0 (empty list) | 0 | 0 | 0 |
| **Total** | **15** | **0** | **4** | **11** |

**Answer for the task: 11 of 15 citations were invented, 4 were real papers cited with wrong details, and 0 were fully correct.** For the plain prompt only: 5 of 9 were invented and the other 4 had wrong details, so none of the 9 could be used as written.

## 4. What I learned
- **Every model failed on the plain prompt.** Not one of the 15 citations was right in every detail. Even the best case (the larger Gemini) had wrong authors or wrong DOIs on all three.
- **Bigger helped, but did not fix it.** `gemma3:270m` invented everything. The small Gemini mixed made-up papers with real-looking names. The larger Gemini found three papers that really exist, but still got authors, venue or DOI wrong.
- **The wrong parts are exactly the parts a reader trusts.** Titles and author names are the easiest to recall; DOIs and numbers are hard. Four DOIs pointed to completely unrelated real papers, and one arXiv number was a physics paper. The DOI looks official, so it makes a false citation look verified.
- **A citation can be partly right.** The IndicNLP and IndicLLMSuite cases show a real paper that was remembered blurred: right topic and group of authors, wrong year, venue and title. This is harder to catch than a pure invention, because a quick search finds "something similar".
- **The careful prompt helped only the larger model.** `gemini-3.6-flash` returned `[]` when allowed to say "not certain", which is the best behaviour here. The small Gemini and the local model ignored the instruction and still invented three each. A small model cannot judge its own certainty.
- **The local model repeated itself.** Same DOI for all three papers and the same invented author "A.K. Sharma"; it even used my topic as a paper title. That is a sign of a model with almost nothing stored, filling a template.
- **Temperature 0 did not help.** All answers were at temperature 0, so being deterministic does not make them true.
- **Fluent and confident.** None of the answers hedged. The invented ones look exactly like the real ones.
- **My own checker had a hole.** At first the script marked the Ahia citation REAL because the title matched, although its DOI was wrong. I fixed it so that a DOI pointing to another paper is flagged "real but details wrong". The saved `results/task7_citations.json` was made before that fix, so its Ahia verdict still says REAL; the table above uses the corrected, hand-checked classification.

## 5. How to verify a citation (what I did)
1. Search the **exact title** in Crossref or OpenAlex (or Google Scholar). No match means suspect.
2. Check **authors, year, venue** against the record, not just the title.
3. **Open the DOI** (`https://doi.org/...`) and read the title it lands on. A DOI that resolves is not proof; it must resolve to the same paper.
4. For arXiv, open the number and read the title.
5. Check the paper really says what the model claims.
6. Count three groups: correct, real but misdescribed, invented.

## 6. Cautions
- One topic, one run, temperature 0: the pattern is clear, the exact counts would change with another topic or model.
- The automatic search can miss a real paper that is not in Crossref or OpenAlex, and a similar title can fool it; that is why I checked by hand.
- The topic is niche on purpose. A famous paper (for example "Attention Is All You Need") would be recalled much better. Hallucination is worst where the training data is thin.
- For real work, give the model the sources (retrieval) or a search tool instead of asking it to remember them.

## Quick check
- Why was a DOI the least trustworthy part of a citation?
- What does it mean that a citation is "real but misdescribed", and why is that harder to catch?
- Why did only the larger model obey the "return fewer papers" instruction?
- Why does temperature 0 not make an answer true?
- What are the steps to verify a citation?
