# Are dogwhistles culturally embedded across varieties of English ?

## Interisciplinary project, M1 NLP
### Institut des sciences du digital Management & Cognition, Université de Lorraine


Dogwhistles refer to coded language used by communities with socially reprehensible beliefs to convey their ideas without the understanding of outsiders. Their meaning depends on the situation of the utterance, which is related to the pragmatic functioning of language. In addition, new dogwhistles are constantly emerging, making them difficult for moderation services to detect. Some researchers tried to create tools to detect dogwhistles and new ones among english corpora. However, in all this research, English is treated as a single, homogeneous block, devoid of any variation. Consequently, we aim to use a model for detecting dogwhistles on various English varieties corpora, in order to determine whether these coded messages vary across diatopic varieties.

Our project raises two research questions: 
* *RQ1*: How to locate new dogwhistles in order to spot hateful speech online?
* *RQ2*: To what degree do the American dogwhistles influence varying interpretations of hate across distinct varieties of English?

## Repository structure

The repository is structured as follows : 

```bash
.
├── data_cleaning.py
├── new_dogwhistle_pipeline
│   ├── config.py
│   ├── data.py
│   ├── model.py
│   └── pipeline.py
└── reddit_api.py
```