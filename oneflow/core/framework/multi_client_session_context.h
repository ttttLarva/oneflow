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
#ifndef ONEFLOW_CORE_FRAMEWORK_MULTI_CLIENT_SESSION_CONTEXT_H_
#define ONEFLOW_CORE_FRAMEWORK_MULTI_CLIENT_SESSION_CONTEXT_H_

#include "oneflow/core/common/util.h"
#include "oneflow/core/job/job_set.pb.h"
#include "oneflow/core/common/maybe.h"

namespace oneflow {

class MultiClientSessionContext {
 public:
  OF_DISALLOW_COPY_AND_MOVE(MultiClientSessionContext);
  MultiClientSessionContext() : is_inited_(false) {}
  ~MultiClientSessionContext() {}

  Maybe<void> TryInit(const ConfigProto& config_proto);
  Maybe<void> TryClose();

 private:
  bool is_inited_;
};

}  // namespace oneflow

#endif  // ONEFLOW_CORE_FRAMEWORK_MULTI_CLIENT_SESSION_CONTEXT_H_
