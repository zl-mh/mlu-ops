# Copyright (C) [2021] by Cambricon, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# pylint: disable=missing-docstring, invalid-name, too-many-locals
"""A multi-platform code link example test for BANGPy TCP."""
import numpy as np

import bangpy
from bangpy import tcp
from bangpy.common import utils, load_op_by_type
from bangpy.platform.bang_config import ALIGN_LENGTH, TARGET
from bangpy.tcp.runtime import TaskType

DTYPES = [bangpy.float32]
TARGET_LIST = ["mlu290"]
KERNEL_NAME = "cosine_similarity"

class Cosine_similarity(object):
    """Operator description:
    compute cosine similarity of two given tensors
    """

    def __init__(self, dtype, target, task_num, stage):
        self.dtype = dtype
        self.target = target
        self.task_num = task_num
        self.stage = stage
        self.bp = tcp.TCP(target)
        # self.length = self.bp.Scalar(dtype=bangpy.int32, name="length")
        self.dim_0 = self.bp.SizeVar("dim_0")
        self.dim_1 = self.bp.SizeVar("dim_1")
        self.dim_2 = self.bp.SizeVar("dim_2")
        self.dim_3 = self.bp.SizeVar("dim_3")
        self.length = self.dim_0 * self.dim_1 * self.dim_2 * self.dim_3
        self.nram_size = TARGET(target).nram_size
        self.dtype_sz = dtype.bytes
        self.single_buffer_size = self.nram_size // 32
        self.bp.launch_task(self.task_num, 1, 1)


    def compute_body(self):
        #calculate basic data
        
        data_calculated_each_task = self.length // self.task_num
        data_remain = self.length % self.task_num
        loop_num = data_calculated_each_task * self.dtype_sz // self.single_buffer_size
        data_calculated_each_time = self.single_buffer_size // self.dtype_sz
        #remain = (data_calculated_each_task * self.dtype_sz) % self.single_buffer_size
        each_task_remain = data_calculated_each_task % data_calculated_each_time

       buffer_in0 = self.bp.Buffer(
            shape=(self.dim_0, self.dim_1, self.dim_2, self.dim_3), name="INPUT0", dtype=self.dtype, scope="global"
        )
        buffer_in1 = self.bp.Buffer(
            shape=(self.dim_0, self.dim_1, self.dim_2, self.dim_3), name="INPUT1", dtype=self.dtype, scope="global"
        )
        buffer_out = self.bp.Buffer(
            shape=(self.dim_0, self.dim_1, self.dim_2, self.dim_3), name="OUTPUT", dtype=self.dtype, scope="global"
        )
        task_id = self.bp.taskId

        f = self.bp.BuildBANG(
            inputs=[buffer_original,
                    self.dim_0,
                    self.dim_1,
                    self.dim_2,
                    self.dim_3],
            outputs=[buffer_final],
            kernel_name=KERNEL_NAME,
        )
        return f


@tcp.register_mlu_op(DTYPES, TARGET_LIST, KERNEL_NAME)
def build_cosine_similarity(dtype=None, target=None):
    # tasktype fixed in UNION1
    task_num = 64
    task_type = TaskType.BLOCK
    stage = 1
    f = Cosine_similarity(dtype, target, task_num, stage, ).compute_body()
    return f