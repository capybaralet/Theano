#
# Slice type and Op. None Type and NoneConst.
#
import theano
from theano.gof import Apply, Constant, Generic, Op, Type, hashtype
from theano.gradient import DisconnectedType


def as_int_none_variable(x):
    if x is None:
        return NoneConst
    elif NoneConst.equals(x):
        return x
    x = theano.tensor.as_tensor_variable(x, ndim=0)
    if x.type.dtype[:3] not in ('int', 'uin'):
        raise TypeError('index must be integers')
    return x


class MakeSlice(Op):
    def make_node(self, slc, stop=None, step=None):
        # We need to accept and handle in make_node inputs the node
        # inputs to allow redoing a new op elsewhere in the graph by
        # optimization.
        if isinstance(slc, slice):
            assert stop is None
            assert step is None
            inp = [slc.start, slc.stop, slc.step]
        else:
            inp = [slc, stop, step]
        return Apply(self,
                     map(as_int_none_variable, inp),
                     [slicetype()])

    def perform(self, node, inp, out_):
        out, = out_
        out[0] = slice(*inp)

    def __str__(self):
        return self.__class__.__name__

    def __eq__(self, other):
        return type(self) == type(other)

    def __hash__(self):
        return hash(type(self))

    def grad(self, inputs, grads):
        return [DisconnectedType()() for i in inputs]

make_slice = MakeSlice()


class SliceType(Type):

    def filter(self, x, strict=False, allow_downcast=None):
        if isinstance(x, slice):
            return x
        else:
            raise TypeError('Expected a slice!')

    def __str__(self):
        return "slice"

    def __eq__(self, other):
        return type(self) == type(other)

    def __hash__(self):
        return hashtype(self)

    @staticmethod
    def may_share_memory(a, b):
        # Slices never shared memory between object
        return isinstance(a, slice) and a is b

slicetype = SliceType()


class NoneTypeT(Generic):
    """
    Inherit from Generic to have c code working.
    """

    def filter(self, x, strict=False, allow_downcast=None):
        if x is None:
            return x
        else:
            raise TypeError('Expected None!')

    @staticmethod
    def may_share_memory(a, b):
        # None never share memory between object, in the sence of DebugMode.
        # Python None are singleton
        return False

none_type_t = NoneTypeT()

# This is a variable instance. It can be used only once per fgraph.
# So use NoneConst.clone() before using it in a Theano graph.
# Use NoneConst.equal(x) to check if two variable are NoneConst.
NoneConst = Constant(NoneTypeT(), None, name='NoneConst')
