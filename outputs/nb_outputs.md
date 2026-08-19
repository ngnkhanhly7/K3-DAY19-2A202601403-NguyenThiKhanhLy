

## Cell 3
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m327.8/327.8 kB[0m [31m29.9 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m18.8/18.8 MB[0m [31m73.4 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m143.7/143.7 kB[0m [31m12.8 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m2.4/2.4 MB[0m [31m82.3 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m1.0/1.0 MB[0m [31m42.1 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m11.9/11.9 MB[0m [31m102.8 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m1.8/1.8 MB[0m [31m71.6 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m69.4/69.4 kB[0m [31m7.6 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m73.1/73.1 kB[0m [31m7.7 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m1.1/1.1 MB[0m [31m58.3 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m165.0/165.0 kB[0m [31m17.1 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m51.0/51.0 kB[0m [31m5.3 MB/s[0m eta [36m0:00:00[0m
[2K   [90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m [32m166.8/166.8 kB[0m [31m17.4 MB/s[0m eta [36m0:00:00[0m
[?25h[31mERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
ipython 7.34.0 requires jedi>=0.16, which is not installed.
google-colab 1.0.0 requires requests==2.32.4, but you have requests 2.34.2 which is incompatible.[0m[31m
[0m

## Cell 6
Đang kết nối luồng dữ liệu (streaming)...
README.md:   0%|          | 0.00/1.22k [00:00<?, ?B/s]Đang ghi dữ liệu vào: /content/hackernoon_subset.csv
Đang tải (MB):   0%|          | 0/300 [00:00<?, ?MB/s]
[DỪNG] Đã đạt giới hạn số dòng: 5,000 dòng (Dung lượng: 2.92 MB)
✅ Hoàn thành: /content/hackernoon_subset.csv
   Rows: 5,000
   Size: 2.92 MB


## Cell 7
✅ Neo4j connected.
✅ Schema ready.


## Cell 8
Exact dedup: 2,675 -> 2,105
Chunking:   0%|          | 0/1500 [00:00<?, ?it/s]                      chunk_id            article_id  \
0  1a05beb7aa3071be6fd7::c0000  1a05beb7aa3071be6fd7   
1  8e922bc62b578e73e815::c0000  8e922bc62b578e73e815   
2  4bd7afdba71243b0dbcd::c0000  4bd7afdba71243b0dbcd   
3  6633c15d86f5e81f47b8::c0000  6633c15d86f5e81f47b8   
4  4ce72a4490a6a618e2d5::c0000  4ce72a4490a6a618e2d5   

                                                                                     title  \
0  onsemi and Sineng Electric Spearhead the Development of Sustainable Energy Applications   
1   Modernizing State Services: Harnessing Technology for Enhanced Public Service Delivery   
2  Terry Richardson On Why He Left AMD GreenPages’ Technology Chops And The AI Opportunity   
3                                            5 Kubernetes technology vendors hot right now   
4                                     Bachelor of Science in Health Information Management   

  published_date  \
0     2023-05-16   
1     2023-05-01   
2     2023-05-02   
3     2023-02-28   
4     2023-08-16   

                                                                                                                      text  
0  (Nasdaq: ON) a leader in intelligent power and sensing technologies today announced that Sineng Electric will integr...  
1  To deliver 21st-century government services Governors and cabinet members need leaders with technology expertise to ...  
2  In February GreenPages acquired Toronto-based Zanaris an IT automation cloud and DevOps services firm ... Steve Burk...  
3  Kubernetes is a technology that has created a whole new ecosystem around itself and it is now a key plank in the Dev...  
4  Health information management (HIM) is a diverse yet evolving field that incorporates medicine management finance in...  

## Cell 12
Coref:   0%|          | 0/80 [00:00<?, ?it/s]

## Cell 14
NER+RE:   0%|          | 0/100 [00:00<?, ?it/s]  source_raw source_type relation target_raw   target_type source_chunk_id  \
0      Dummy      PERSON    HAS_A     Dummy2  ORGANIZATION           dummy   

  published_date        evidence  confidence  
0     2024-01-01  dummy evidence         1.0  

## Cell 16
Empty DataFrame
Columns: []
Index: []

## Cell 18
{'nodes': 87, 'edges': 50, 'invalid_provenance_edges': 0}
                          id                                     name  \
0   fb0f4df56fab164ec48722f0                                Microsoft   
1   23d7ceb58c062d83135817ba          Intelligent Technical Solutions   
2   76a986b1ff8cfae54ce1c5a1                            Eric Schummer   
3   d0eaaccf04669315e412ad07                                       DI   
4   42f221e4ff4b62d9f94970a9  data-intensive analytics-based services   
5   773eeb9b7cc008bff365fcdd                                   OpenAI   
6   26fe01fbff18a0ced2a65600                                  Infosys   
7   07f21a993871226abed12f9f                              Senzary LLC   
8   bd4cccc4f905ae863fc8c8c5                                    Lumen   
9   ce493f3efd776c3a90d1c029                                 Crexendo   
10  70c4e949ff245096c6946802                      Amazon Web Services   
11  4afd8768b3cad39aae7547b9                                 Level Ex   
12  24efe6cedc09a12ec8c3eff2                                 Synopsys   
13  5c0dfda16cbfa608d8cfc87b                                      IDC   
14  431cca765017665a7961a6ac                                   Aretum   

          type  degree  
0      Company       3  
1      Company       3  
2       Person       2  
3      Company       2  
4   Technology       2  
5      Company       2  
6      Company       2  
7      Company       2  
8      Company       2  
9      Company       2  
10     Company       2  
11     Company       1  
12     Company       1  
13     Company       1  
14     Company       1  

## Cell 20
modules.json:   0%|          | 0.00/349 [00:00<?, ?B/s]config_sentence_transformers.json:   0%|          | 0.00/116 [00:00<?, ?B/s]README.md:   0%|          | 0.00/10.5k [00:00<?, ?B/s]sentence_bert_config.json:   0%|          | 0.00/53.0 [00:00<?, ?B/s]config.json:   0%|          | 0.00/612 [00:00<?, ?B/s]model.safetensors: reconstructing file:   0%|          |  0.00B / 90.9MB            model.safetensors: downloading bytes:           |  0.00B            Loading weights:   0%|          | 0/103 [00:00<?, ?it/s]tokenizer_config.json:   0%|          | 0.00/350 [00:00<?, ?B/s]vocab.txt:   0%|          | 0.00/232k [00:00<?, ?B/s]tokenizer.json:   0%|          | 0.00/466k [00:00<?, ?B/s]special_tokens_map.json:   0%|          | 0.00/112 [00:00<?, ?B/s]config.json:   0%|          | 0.00/190 [00:00<?, ?B/s]Batches:   0%|          | 0/12 [00:00<?, ?it/s]Flat vectors: 1500


## Cell 26
    id      group  \
0  G01    factoid   
1  G02  multi-hop   
2  G03  cross-doc   
3  G04  multi-hop   

                                                                                                                  question  \
0                                                                                 Who was the CEO of Hugging Face in 2023?   
1                     Which startups were founded by former Microsoft employees and later received investment from Google?   
2     Compare the direction of AI-related investments by Meta and Apple during 2023 using evidence from multiple articles.   
3  Find a company invested in by a major technology company that also developed a named AI technology; identify both re...   

                                                                                reference_answer  \
0                                                                               Clément Delangue   
1          Startups founded by former Microsoft employees and invested in by Google include XYZ.   
2  Meta invested in open-source AI models, while Apple focused on on-device AI and acquisitions.   
3           Company X received investment from major tech and developed AI technology Y in 2023.   

                  reference_evidence  
0  Validate against instructor dump.  
1          TO_BE_FILLED_FROM_DATASET  
2          TO_BE_FILLED_FROM_DATASET  
3          TO_BE_FILLED_FROM_DATASET  

## Cell 28
✅ Golden Dataset valid.
Evaluation:   0%|          | 0/4 [00:00<?, ?it/s]    id      group  \
0  G01    factoid   
1  G02  multi-hop   
2  G03  cross-doc   
3  G04  multi-hop   

                                                                                                                  question  \
0                                                                                 Who was the CEO of Hugging Face in 2023?   
1                     Which startups were founded by former Microsoft employees and later received investment from Google?   
2     Compare the direction of AI-related investments by Meta and Apple during 2023 using evidence from multiple articles.   
3  Find a company invested in by a major technology company that also developed a named AI technology; identify both re...   

                                                                                reference_answer  \
0                                                                               Clément Delangue   
1          Startups founded by former Microsoft employees and invested in by Google include XYZ.   
2  Meta invested in open-source AI models, while Apple focused on on-device AI and acquisitions.   
3           Company X received investment from major tech and developed AI technology Y in 2023.   

                                                                                                               flat_answer  \
0  <think>\nHere's a thinking process:\n\n1.  **Analyze User Input:**\n   - **Question:** Who was the CEO of Hugging Fa...   
1  <think>\nHere's a thinking process:\n\n1.  **Analyze User Question:** The user asks: "Which startups were founded by...   
2  <think>\nHere's a thinking process:\n\n1.  **Analyze User Input:**\n   - **Question:** Compare the direction of AI-r...   
3  <think>\nHere's a thinking process:\n\n1.  **Analyze User Question:**\n   - Find a company invested in by a major te...   

                                                                                                              graph_answer  \
0  <think>\nHere's a thinking process:\n\n1.  **Analyze User Input:**\n   - **Question:** Who was the CEO of Hugging Fa...   
1  <think>\nHere's a thinking process:\n\n1.  **Analyze User Question:** "Which startups were founded by former Microso...   
2  <think>\nHere's a thinking process:\n\n1.  **Analyze User Question:**\n   - **Topic:** Compare the direction of AI-r...   
3  <think>\nHere's a thinking process:\n\n1.  **Analyze User Question:**\n   - Find a company invested in by a major te...   

   flat_comprehensiveness  graph_comprehensiveness  flat_faithfulness  \
0                       5                        5                  5   
1                       1                        5                  5   
2                       5                        4                  5   
3                       5                        5                  5   

   graph_faithfulness  flat_multi_hop_reasoning  graph_multi_hop_reasoning  \
0                   5                         5                          5   
1                   5                         1                          5   
2                   5                         5                          4   
3                   5                         5                          5   

   flat_latency_s  graph_latency_s  flat_total_tokens  graph_total_tokens  \
0        2.264059         1.967779               1705                1388   
1       15.844725        12.289551               2429                1706   
2        7.381231        15.489216               2241                2165   
3       14.302767         4.072077               2647                2414   

                                                                                                      flat_judge_rationale  \
0  The candidate correctly identifies that the provided context lacks information about Hugging Face and its CEO. It st...   
1  The candidate correctly identifies that the provided context lacks the requested information and explicitly states t...   
2  The candidate correctly identifies that the provided context lacks the necessary information to answer the question,...   
3  The candidate correctly identifies that the provided context lacks the necessary details to fulfill the multi-hop qu...   

                                                                                                     graph_judge_rationale  \
0  The candidate correctly identifies that the provided context lacks information about Hugging Face's CEO. It strictly...   
1  The candidate correctly identifies that the provided context lacks the necessary information to answer the question....   
2  The candidate accurately extracts and compares the AI investment directions for Meta and Apple based on the provided...   
3  The candidate correctly identifies that the provided context lacks the necessary information to answer the question....   

   graph_supernode_events  
0                       0  
1                       0  
2                       0  
3                       0  

## Cell 29
   Loại câu hỏi               Metric  Flat RAG  GraphRAG  \
0     cross-doc    Comprehensiveness     5.000     4.000   
1     cross-doc         Faithfulness     5.000     5.000   
2     cross-doc  Multi-hop reasoning     5.000     4.000   
3     cross-doc          Latency (s)     7.381    15.489   
4     cross-doc          Token usage  2241.000  2165.000   
5       factoid    Comprehensiveness     5.000     5.000   
6       factoid         Faithfulness     5.000     5.000   
7       factoid  Multi-hop reasoning     5.000     5.000   
8       factoid          Latency (s)     2.264     1.968   
9       factoid          Token usage  1705.000  1388.000   
10    multi-hop    Comprehensiveness     3.000     5.000   
11    multi-hop         Faithfulness     5.000     5.000   
12    multi-hop  Multi-hop reasoning     3.000     5.000   
13    multi-hop          Latency (s)    15.074     8.181   
14    multi-hop          Token usage  2538.000  2060.000   

                                                                   Nhận xét phân tích  
0   Flat RAG tốt hơn; graph extraction/retrieval có thể gây mất thông tin hoặc nhiễu.  
1                                                           Hai phương pháp gần nhau.  
2   Flat RAG tốt hơn; graph extraction/retrieval có thể gây mất thông tin hoặc nhiễu.  
3                                                       Flat RAG thường rẻ/nhanh hơn.  
4                                            GraphRAG không đắt hơn trong sample này.  
5                                                           Hai phương pháp gần nhau.  
6                                                           Hai phương pháp gần nhau.  
7                                                           Hai phương pháp gần nhau.  
8                                            GraphRAG không đắt hơn trong sample này.  
9                                            GraphRAG không đắt hơn trong sample này.  
10                           GraphRAG cải thiện rõ; kiểm tra rationale và provenance.  
11                                                          Hai phương pháp gần nhau.  
12                           GraphRAG cải thiện rõ; kiểm tra rationale và provenance.  
13                                           GraphRAG không đắt hơn trong sample này.  
14                                           GraphRAG không đắt hơn trong sample này.  

## Cell 31
{'id': '23d7ceb58c062d83135817ba', 'name': 'Intelligent Technical Solutions', 'degree': 3} fetched= 3
No audit rows.
