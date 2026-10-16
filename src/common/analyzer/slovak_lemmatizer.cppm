// Copyright(C) 2026 InfiniFlow, Inc. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

module;

export module infinity_core:slovak_lemmatizer;

import std;

namespace infinity {

// Dictionary forms of inflected Slovak words, for the forms the light stemmer
// cannot reduce on its own ("ľudí" -> "ľudia", "psovi" -> "pes").
//
// The table is resource/slovak/lemma.tsv: one "form<TAB>lemma" line per
// lowercase form, sorted bytewise by form. tools/generate_slovak_lemma_table.py
// derives it from the hunspell-sk dictionary, and it carries that dictionary's
// licence (MPL-2.0) next to it. Mirrors _SlovakLemmatizer in rag_tokenizer.py.
export class SlovakLemmatizer {
public:
    static constexpr std::string_view TABLE_PATH = "slovak/lemma.tsv";

    // The table under a resource directory, read once per process and shared
    // by every analyzer; nullptr when the resource directory has none, in
    // which case Slovak is stemmed without a lemma lookup.
    static const SlovakLemmatizer *Shared(const std::string &resource_path);

    // The lemma of a lowercase form, or the form itself when the table has no
    // entry for it.
    std::string_view Lemmatize(std::string_view form) const;

private:
    explicit SlovakLemmatizer(std::string data);

    std::string_view Form(std::uint32_t line) const;

    std::string data_;
    std::vector<std::uint32_t> lines_; // offset of each line, in the table's (bytewise) order
};

} // namespace infinity
