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
#ifndef ONEFLOW_CORE_CCL_CCL_H_
#define ONEFLOW_CORE_CCL_CCL_H_

#include "oneflow/core/common/data_type.pb.h"
#include "oneflow/core/common/device_type.pb.h"
#include "oneflow/core/common/symbol.h"

namespace oneflow {

class DeviceCtx;
class ParallelDesc;

// collective communication library
namespace ccl {

template<DeviceType device_type>
Maybe<void> Broadcast(const void* in, void* out, size_t elem_cnt, DataType dtype, int64_t root,
                      Symbol<ParallelDesc> parallel_desc, DeviceCtx* ctx);

}

}  // namespace oneflow

#endif  // ONEFLOW_CORE_CCL_CCL_H_
