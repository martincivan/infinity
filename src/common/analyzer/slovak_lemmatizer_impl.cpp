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

module infinity_core:slovak_lemmatizer.impl;

import :slovak_lemmatizer;
import :logger;

import std;
import third_party;

namespace infinity {

const SlovakLemmatizer *SlovakLemmatizer::Shared(const std::string &resource_path) {
    static std::mutex mutex;
    static std::map<std::string, std::unique_ptr<SlovakLemmatizer>> tables;
    std::lock_guard<std::mutex> lock(mutex);
    auto [it, inserted] = tables.try_emplace(resource_path);
    if (inserted) {
        std::filesystem::path path = std::filesystem::path(resource_path) / TABLE_PATH;
        std::ifstream file(path, std::ios::binary);
        if (file) {
            std::ostringstream data;
            data << file.rdbuf();
            it->second.reset(new SlovakLemmatizer(std::move(data).str()));
        } else {
            LOG_WARN(fmt::format("Slovak lemma table not found, stemming without it: {}", path.string()));
        }
    }
    return it->second.get();
}

SlovakLemmatizer::SlovakLemmatizer(std::string data) : data_(std::move(data)) {
    for (std::size_t line = 0; line < data_.size();) {
        std::size_t end = data_.find('\n', line);
        if (end == std::string::npos) {
            data_ += '\n';
            end = data_.size() - 1;
        }
        if (data_.find('\t', line) < end) {
            lines_.push_back(static_cast<std::uint32_t>(line));
        }
        line = end + 1;
    }
}

std::string_view SlovakLemmatizer::Lemmatize(std::string_view form) const {
    auto it = std::lower_bound(lines_.begin(), lines_.end(), form, [this](std::uint32_t line, std::string_view key) { return Form(line) < key; });
    if (it == lines_.end() || Form(*it) != form) {
        return form;
    }
    std::size_t lemma = *it + form.size() + 1;
    return std::string_view(data_).substr(lemma, data_.find('\n', lemma) - lemma);
}

std::string_view SlovakLemmatizer::Form(std::uint32_t line) const { return std::string_view(data_).substr(line, data_.find('\t', line) - line); }

} // namespace infinity
