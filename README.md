# Completion-Weighted Random-Order Access for Tree-Shaped Conjunctive Queries with Short-Span Negation

![Python](https://img.shields.io/badge/Python-3.10%2B-386FA4?style=flat-square)
![Query Processing](https://img.shields.io/badge/Area-Database%20Query%20Processing-679C92?style=flat-square)
![Random Order](https://img.shields.io/badge/Output-Without%20Replacement-C18A59?style=flat-square)

This repository accompanies **Completion-Weighted Random-Order Access for Tree-Shaped Conjunctive Queries with Short-Span Negation**. The paper studies duplicate-free random-order enumeration of full conjunctive-query answers when the positive joins form a tree and one safe negative atom closes a path of at most three edges.

A forbidden endpoint pair can remove many full join answers at once. The method counts those completions exactly, assigns each surviving answer an internal rank, and draws unused ranks uniformly. Its physical-plan analysis also accounts for index construction, memory, and the number of answers requested.

## ✨ Main Contributions

- **🧮 Completion-weighted access.** Off-path join subtrees are summarized by exact completion counts and conditional decoders. The signed core is partitioned into disjoint weighted groups. Light branches use persistent weighted prefixes, while heavy branches subtract blocked completion mass. For fixed queries with one negative atom of span at most three, the paper establishes **Õ(M³ᐟ²)** preprocessing and static space, **expected polylogarithmic** output delay, and **O(k)** additional state after *k* outputs.
- **🔀 Exact random order without replacement.** A rank bijection and a sparse Fisher–Yates permutation ensure that each surviving full answer is emitted once. The mathematical uniformity guarantee assumes independent unbiased random draws and exact integer counts.
- **📐 An ordering-sensitive separation.** For fixed self-join-free span-three queries, instance-selected internal ranks have a different preprocessing bound from prescribed lexicographic direct access. The lower-bound comparison is conditional on the **Zero-Clique Conjecture**.
- **⏱️ Prefix-sensitive execution choices.** The experiments compare streaming rejection, weighted indexing, and full materialization with setup cost included. The preferred plan depends on answer-prefix length, completion skew, and available memory.

## 🧭 Method at a Glance

```text
Positive join tree + one safe negative atom (span ≤ 3)
                    │
                    ▼
      Subtree completion masses
         + conditional decoders
                    │
                    ▼
       Blocker-aware orientation
                    │
           ┌────────┴────────┐
           ▼                 ▼
    Light branches      Heavy branches
    Weighted prefixes   Blocked-mass subtraction
           └────────┬────────┘
                    ▼
       Disjoint answer groups
       + exact rank decoding
                    │
                    ▼
      Sparse random permutation
                    │
                    ▼
       Unique random-order answers
```

## 📁 Repository Structure

```text
tree-join-random-order/
├── README.md                         # 📖 Project description and usage
├── .gitignore                        # 🧹 Local Python and editor artifacts
├── reference_impl/                   # 🧮 Small-instance reference algorithm
│   ├── __init__.py
│   └── random_order.py               # Signed tree join, rank access, no-replacement draws
├── scripts/                          # ▶️ Command-line entry point
│   ├── __init__.py
│   └── run_reference.py
├── tests/                            # ✅ Correctness checks
│   ├── __init__.py
│   └── test_random_order.py
├── fixtures/                         # 🧩 Synthetic input and expected answers
│   ├── small_tree.json
│   └── expected_small_tree.json
└── data/                             # 📊 Saved short-prefix timing summary
    ├── README.md
    └── short_prefix_medians.csv
```

## ⚙️ Environment

The reference code uses **Python 3.10 or newer** and the Python standard library. No third-party packages or GPU are required for the commands below.

```bash
git clone https://github.com/Anna042023/tree-join-random-order.git
cd tree-join-random-order
```

You can also extract the repository ZIP and run the same commands from its root directory.

## 🚀 Run the Reference Example

```bash
python -m scripts.run_reference --input fixtures/small_tree.json --seed 17
```

The sample contains three positive binary atoms and one forbidden endpoint relation. The command prints four valid, nonrepeating full answers in JSON format. Its expected output is saved at `fixtures/expected_small_tree.json`.

To check the reference implementation:

```bash
python -m unittest discover -s tests -v
```

The tests compare the join and anti-join output with an independent Cartesian-product oracle, check rank coverage, exercise sampling without replacement, and verify the packaged example.

## 🧪 Experiments and Data

The paper evaluates three questions: exact rank decoding, representation costs under completion skew, and the build-inclusive cost of obtaining an answer prefix.

| Evaluation | Reported setup |
|---|---|
| 🔎 Exactness | 65,536 finite relation worlds and 512 weighted fixtures |
| 📈 Scaling | Four synthetic workloads (W1–W4) with different degree and blocker patterns |
| 🌐 Graph workloads | Induced graphs with 200 and 250 vertices, plus additional graph-derived checks |
| ⏱️ Access plans | Streaming rejection, completion-weighted indexing, and materialization |

The paper reports that streaming is preferable for very short prefixes in its induced-graph tests, while indexing becomes competitive at larger prefixes. The reported crossover points differ between the 200-vertex and 250-vertex inputs.

`data/short_prefix_medians.csv` preserves the aggregate measurements for prefixes of 1, 100, and 1,000 answers on those two inputs. The underlying graph datasets and benchmark execution traces are not included here.

## 🔬 Implementation Scope

**The included Python implementation is a small-instance correctness reference.** It materializes the full answer set, groups answers by the signed core, decodes integer ranks, and enumerates without replacement. It is suitable for inspecting query semantics and checking small fixtures.

The paper's nonmaterializing completion-weighted Heavy/Light index, native C++/SQLite benchmark drivers, original workload generators, and full graph inputs are **not present in the supplied source archive**. The included tests therefore do not reproduce the paper's preprocessing bounds, memory measurements, or runtime crossover results.

## 🔗 Repository

[tree-join-random-order](https://github.com/Anna042023/tree-join-random-order)
