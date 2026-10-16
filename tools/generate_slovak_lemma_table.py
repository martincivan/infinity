# Copyright(C) 2026 InfiniFlow, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generate the Slovak lemma table (resource/slovak/lemma.tsv) from hunspell-sk.

The RAG analyzer looks a lowercased Slovak token up in this table before the
light stemmer runs, so that forms the suffix rules cannot reach -- "ľudí" and
"človek", "psa" and "pes", "som" and "byť" -- reduce to their dictionary form
first.

Every word form the dictionary generates is analysed with "hunspell -m" and
mapped to the lemma of its "st:" field. A form is written only when the table
changes the analyzer's output, i.e. when the stem of its lemma differs from
its own stem, and only when the lemma is unambiguous:

* analyses tagged "tp:negation" are dropped, so "nebezpečný" keeps its own
  term instead of meeting "bezpečný";
* a form whose analyses reach lemmas with different stems ("je": byť, jesť)
  is left to the stemmer;
* forms shorter than MIN_FORM_LENGTH characters and the forms in EXCLUDED_FORMS
  are left to the stemmer. hunspell-sk lists few function words, so many of
  them only analyse as an inflection of an unrelated rare word ("nič" as the
  imperative of "ničiť", "tri" of "trieť").

Requires the hunspell command-line tools ("unmunch", "hunspell") and a checkout
of https://github.com/sk-spell/hunspell-sk:

    uv run tools/generate_slovak_lemma_table.py --hunspell-sk <checkout> --output resource/slovak/lemma.tsv

The table is a derived work of hunspell-sk and is distributed under its
licence, the Mozilla Public License 2.0, next to the table.
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python", "infinity_sdk"))
from infinity.rag_tokenizer import _SlovakStemmer

MIN_FORM_LENGTH = 4

# Forms whose only hunspell-sk analysis is an inflection of an unrelated word.
EXCLUDED_FORMS = {
    "autu",  # auto, not "aut"
    "celkom",  # adverb, not "celok"
    "ciel",
    "ciest",  # cesta, not "cesto"
    "dolu",  # adverb, not "dol"
    "duší",  # duša, not "dušiť"
    "jednu",  # jeden/jedna, not "jedno"
    "kade",  # adverb, not "kaďa"
    "kopu",  # kopa, not "kop"
    "mamu",  # mama, not "mam"
    "maria",
    "naraz",  # adverb, not "naraziť"
    "naši",  # náš, not "našiť"
    "není",
    "niečím",  # niečo, not "niečí"
    "okej",
    "over",
    "piatim",  # päť, not "piati"
    "proste",  # adverb, not "prosiť"
    "rádu",  # rad, not "rád"
    "sním",
    "späť",  # adverb, not "spätiť"
    "tiel",  # telo, not "tlo"
    "tomu",  # ten, not "tomus"
    "týmu",  # tím, not "týmus"
    "váhu",  # váha, not "Váh"
    "veku",  # vek, not "veko"
    "zásob",  # zásoba, not "zásobiť"
    "zrazu",  # adverb, not "zraz"
    "zrejme",  # adverb, not "zrieť"
}

# The tokens the analyzer stems: lowercase letters of the Latin-1 Supplement and
# Latin Extended-A blocks.
_LATIN_WORD = re.compile(r"[a-zÀ-ſ]+")


def expand_forms(dic: str, aff: str) -> list:
    output = subprocess.run(["unmunch", dic, aff], check=True, capture_output=True, text=True).stdout
    return sorted({line for line in output.splitlines() if line})


def analyse(forms: list, dictionary: str) -> dict:
    """Map each lowercased form to the lowercased lemmas of its non-negated analyses."""
    output = subprocess.run(
        ["hunspell", "-d", dictionary, "-m"], input="\n".join(forms) + "\n", check=True, capture_output=True, text=True
    ).stdout
    lemmas = defaultdict(set)
    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 2 or "tp:negation" in fields:
            continue
        stems = [field[3:] for field in fields if field.startswith("st:")]
        if stems:
            lemmas[fields[0].lower()].add(stems[0].lower())
    return lemmas


def build_table(lemmas: dict) -> list:
    stemmer = _SlovakStemmer()
    table = []
    for form, candidates in lemmas.items():
        if len(form) < MIN_FORM_LENGTH or form in EXCLUDED_FORMS or not _LATIN_WORD.fullmatch(form):
            continue
        candidates = sorted(lemma for lemma in candidates if _LATIN_WORD.fullmatch(lemma))
        if not candidates or len({stemmer.stemWord(lemma) for lemma in candidates}) != 1:
            continue
        if stemmer.stemWord(candidates[0]) == stemmer.stemWord(form):
            continue
        table.append((form, candidates[0]))
    return sorted(table)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hunspell-sk", required=True, help="checkout of https://github.com/sk-spell/hunspell-sk")
    parser.add_argument("--output", required=True, help="path of the generated lemma.tsv")
    args = parser.parse_args()

    dictionary = os.path.join(args.hunspell_sk, "sk_SK")
    forms = expand_forms(dictionary + ".dic", dictionary + ".aff")
    table = build_table(analyse(forms, dictionary))
    with open(args.output, "w", encoding="utf-8", newline="\n") as output:
        output.writelines(f"{form}\t{lemma}\n" for form, lemma in table)
    print(f"{len(forms)} forms, {len(table)} table entries -> {args.output}")


if __name__ == "__main__":
    main()
