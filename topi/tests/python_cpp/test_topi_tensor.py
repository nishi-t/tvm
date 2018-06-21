"""Test code for tensor operator"""
import numpy as np
import tvm
import topi

def verify_elemwise_sum(num_args, dtype):
    shape = (3,5,4)

    tvm_placeholders = []
    for i in range(num_args):
        tvm_placeholders.append(
            tvm.placeholder(shape, name="data"+str(i), dtype=dtype))
    esum = topi.cpp.elemwise_sum(tvm_placeholders, num_args)

    def get_ref_data():
        np_nd = [np.random.uniform(0, 10, size=shape).astype(dtype)
                 for i in range(num_args)]
        return np_nd
    np_nd = get_ref_data()

    def check_device(device):
        if not tvm.module.enabled(device):
            print("Skip because %s is not enabled" % device)
            return
        target = topi.cpp.TEST_create_target(device)
        s = topi.cpp.generic.default_schedule(target, [esum], False)
        ctx = tvm.context(device, 0)
        out = tvm.nd.array(np.zeros(shape, dtype=dtype), ctx)
        f = tvm.build(s, tvm_placeholders + [esum], device, name="elemwise_sum")
        tvm_nd = [tvm.nd.array(nd, ctx) for nd in np_nd] + [out]
        f(*tvm_nd)
        np_out = np.sum(np.array(np_nd), axis=0)
        np.testing.assert_allclose(out.asnumpy(), np_out, rtol=1e-5)

    for device in ["llvm"]:
        check_device(device)


def verify_full(shape, dtype, fill_value):
    A = tvm.placeholder(shape, dtype=dtype, name="A")
    B = topi.cpp.full_like(A, fill_value)
    C = topi.cpp.full(shape, dtype, fill_value)

    def get_ref_data():
        return np.full(shape, fill_value, dtype)
    np_nd = get_ref_data()

    def check_device(device):
        if not tvm.module.enabled(device):
            print("Skip because %s is not enabled" % device)
            return
        target = topi.cpp.TEST_create_target(device)
        s1 = topi.cpp.generic.default_schedule(target, [B], False)
        s2 = topi.cpp.generic.default_schedule(target, [C], False)
        ctx = tvm.context(device, 0)
        out = tvm.nd.array(np.zeros(shape, dtype=dtype), ctx)
        f = tvm.build(s1, [A, B], device, name="full_like")
        f(tvm.nd.array(np.zeros(shape, dtype), ctx), out)
        np.testing.assert_allclose(out.asnumpy(), np_nd, rtol=1e-5)

        f = tvm.build(s2, [C], device, name="full")
        f(out)
        np.testing.assert_allclose(out.asnumpy(), np_nd, rtol=1e-5)

    for device in ["llvm"]:
        check_device(device)


def verify_comparator(shape, dtype, out_type='int8'):
    A = tvm.placeholder(shape, dtype, name="A")
    B = tvm.placeholder(shape, dtype, name="B")
    C = topi.cpp.less(A, B, out_type)

    D = tvm.placeholder(shape, dtype, name="D")
    E = tvm.placeholder(shape, dtype, name="E")
    F = topi.cpp.greater(D, E, out_type)

    def get_ref_data():
        return [np.random.uniform(0, 10, size=shape).astype(dtype),
                np.random.uniform(0, 10, size=shape).astype(dtype)]
    [np_l, np_r] = get_ref_data()

    def check_device(device):
        if not tvm.module.enabled(device):
            print("Skip because %s is not enabled" % device)
            return

        target = topi.cpp.TEST_create_target(device)
        s_less = topi.cpp.generic.default_schedule(target, [C], False)
        s_greater = topi.cpp.generic.default_schedule(target, [F], False)

        ctx = tvm.context(device, 0)
        out = tvm.nd.array(np.zeros(shape, dtype=out_type), ctx)
        tvm_l = tvm.nd.array(np_l, ctx)
        tvm_r = tvm.nd.array(np_r, ctx)

        f = tvm.build(s_less, [A, B, C], device, name="less")
        f(tvm_l, tvm_r, out)
        np.testing.assert_allclose(out.asnumpy(), np.less(np_l, np_r).astype(out_type), rtol=1e-5)

        f = tvm.build(s_greater, [D, E, F], device, name="greater")
        f(tvm_l, tvm_r, out)
        np.testing.assert_allclose(out.asnumpy(), np.greater(np_l, np_r).astype(out_type), rtol=1e-5)

    for device in ["llvm"]:
        check_device(device)


def test_elemwise_sum():
    verify_elemwise_sum(1, "float32")
    verify_elemwise_sum(5, "float32")
    verify_elemwise_sum(4, "int32")


def test_full():
    verify_full((3,4,5), "float32", 3.14)
    verify_full((10,), "int32", 7)


def test_comparator():
    verify_comparator((3,4,5), "float32")
    verify_comparator((7,), "int32")
    verify_comparator((3,4,5), "float32", "int8")


if __name__ == "__main__":
    test_elemwise_sum()
