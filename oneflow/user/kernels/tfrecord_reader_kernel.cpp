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

#include "oneflow/core/record/example.pb.h"
#include "oneflow/core/common/data_type.h"
#include "oneflow/core/framework/framework.h"
#include "oneflow/user/data/tfrecord_data_reader.h"

namespace oneflow {

namespace {

class TFRecordReaderWrapper final : public user_op::OpKernelState {
 public:
  explicit TFRecordReaderWrapper(user_op::KernelInitContext* ctx) : reader_(ctx) {}
  ~TFRecordReaderWrapper() = default;

  void Read(user_op::KernelComputeContext* ctx) { reader_.Read(ctx); }

 private:
  data::TFRecordDataReader reader_;
};

}  // namespace

class TFRecordReaderKernel final : public user_op::OpKernel {
 public:
  TFRecordReaderKernel() = default;
  ~TFRecordReaderKernel() override = default;

  std::shared_ptr<user_op::OpKernelState> CreateOpKernelState(
      user_op::KernelInitContext* ctx) const override {
    std::shared_ptr<TFRecordReaderWrapper> reader(new TFRecordReaderWrapper(ctx));
    return reader;
  }

 private:
  void Compute(user_op::KernelComputeContext* ctx, user_op::OpKernelState* state) const override {
    auto* reader = dynamic_cast<TFRecordReaderWrapper*>(state);
    reader->Read(ctx);
  }
  bool AlwaysComputeWhenAllOutputsEmpty() const override { return false; }
};

REGISTER_USER_KERNEL("TFRecordReader")
    .SetCreateFn<TFRecordReaderKernel>()
    .SetIsMatchedHob((user_op::HobDeviceTag() == "cpu")
                     & (user_op::HobDataType("out", 0) == DataType::kTFRecord));

}  // namespace oneflow
