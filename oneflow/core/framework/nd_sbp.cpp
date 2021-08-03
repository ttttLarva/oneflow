/*
Copyright 2020 The OneFlow Authors. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
#include <mutex>
#include "oneflow/core/common/util.h"
#include "oneflow/core/framework/nd_sbp.h"

namespace oneflow {

namespace {

Maybe<Symbol<cfg::NdSbp>> FindOrCreateNdSbp(
    const std::vector<Symbol<cfg::SbpParallel>>& sbp_list) {
  static thread_local auto* sbp_list2nd_sbp =
      new HashMap<std::vector<Symbol<cfg::SbpParallel>>, Symbol<cfg::NdSbp>>();
  auto iter = sbp_list2nd_sbp->find(sbp_list);
  if (iter == sbp_list2nd_sbp->end()) {
    cfg::NdSbp nd_sbp;
    for (Symbol<cfg::SbpParallel> sbp_symbol : sbp_list) {
      *(nd_sbp.mutable_sbp_parallel()->Add()) = *sbp_symbol;
    }
    iter = sbp_list2nd_sbp->emplace(sbp_list, SymbolOf(nd_sbp)).first;
  }
  return iter->second;
}

Maybe<void> GetDualSbpParallel(const cfg::SbpParallel& sbp_parallel,
                               cfg::SbpParallel* dual_sbp_parallel) {
  if (sbp_parallel.has_split_parallel()) {
    *dual_sbp_parallel = sbp_parallel;
  } else if (sbp_parallel.has_broadcast_parallel()) {
    dual_sbp_parallel->mutable_partial_sum_parallel();
  } else if (sbp_parallel.has_partial_sum_parallel()) {
    dual_sbp_parallel->mutable_broadcast_parallel();
  } else {
    UNIMPLEMENTED_THEN_RETURN();
  }
  return Maybe<void>::Ok();
}

}  // namespace

Maybe<Symbol<cfg::NdSbp>> GetDualNdSbp(
    Symbol<cfg::NdSbp> nd_sbp) {
  static thread_local HashMap<Symbol<cfg::NdSbp>, Symbol<cfg::NdSbp>>
      map;
  auto iter = map.find(nd_sbp);
  if (iter == map.end()) {
    cfg::NdSbp dual_nd_sbp;
    auto* mut_sbp_parallel = dual_nd_sbp.mutable_sbp_parallel();
    for (const auto& sbp_parallel : nd_sbp->sbp_parallel()) {
      JUST(GetDualSbpParallel(sbp_parallel, mut_sbp_parallel->Add()));
    }
    iter = map.emplace(nd_sbp, SymbolOf(dual_nd_sbp)).first;
  }
  return iter->second;
}

Maybe<Symbol<cfg::NdSbp>> GetNdSbp(
    const std::vector<Symbol<cfg::SbpParallel>>& sbp_list) {
  return FindOrCreateNdSbp(sbp_list);
}

}  // namespace oneflow
