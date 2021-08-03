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
#ifndef ONEFLOW_CORE_FRAMEWORK_SYNC_SYMBOL_nd_sbp_H_
#define ONEFLOW_CORE_FRAMEWORK_SYNC_SYMBOL_nd_sbp_H_

#include "oneflow/core/common/maybe.h"
#include "oneflow/core/common/symbol.h"
#include "oneflow/core/framework/rpc_util.h"
#include "oneflow/core/framework/rpc_token.h"

namespace oneflow {

namespace cfg {

class ParallelDistribution;

}

Maybe<void> SyncSymbolParallelDistribution(uint64_t symbol_id, Symbol<cfg::ParallelDistribution>);

}  // namespace oneflow

#endif  // ONEFLOW_CORE_FRAMEWORK_SYNC_SYMBOL_nd_sbp_H_
