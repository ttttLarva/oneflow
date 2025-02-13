#!/bin/bash
set -xe

export TF_CPP_MIN_LOG_LEVEL=3
export PYTHONUNBUFFERED=1

src_dir=${ONEFLOW_SRC_DIR:-"$PWD"}
test_tmp_dir=${ONEFLOW_TEST_TMP_DIR:-"./test_tmp_dir"}


rm -rf $test_tmp_dir
mkdir -p $test_tmp_dir
cp -r $src_dir/python/oneflow/compatible/single_client/test $test_tmp_dir
cd $test_tmp_dir

python3 -m oneflow --doctor

gpu_num=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
for CHUNK in 1
do
	export ONEFLOW_TEST_DEVICE_NUM=${CHUNK}
    python3 $src_dir/ci/test/parallel_run.py \
        --gpu_num="${gpu_num}" \
        --dir=test/ops \
        --timeout=1 \
        --verbose \
        --chunk=${CHUNK}
done

if [ -z "$ONEFLOW_TEST_ENABLE_EAGER" ]
then
    export ONEFLOW_TEST_DEVICE_NUM=2
    python3 -m unittest discover test/ops --failfast --verbose

    export ONEFLOW_TEST_DEVICE_NUM=4
    python3 -m unittest discover test/ops --failfast --verbose
else
    echo "deadlock unsolved, skipping multi-card eager"
fi

ONEFLOW_TEST_MULTI_PROCESS=1 python3 test/ops/test_multi_process.py --failfast --verbose
