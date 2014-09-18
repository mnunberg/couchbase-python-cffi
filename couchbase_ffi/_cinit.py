import os.path
import os
import subprocess
from cffi import FFI

ffi = FFI()
C = None

CPP_INPUT=b"""
#define __attribute__(x)
#include <libcouchbase/sysdefs.h>
#include <libcouchbase/couchbase.h>
"""

VERIFY_INPUT=b"""
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/time.h>
#include <libcouchbase/couchbase.h>
"""

CPP_OUTPUT = os.path.join(os.path.dirname(__file__), "_lcb.h")
FAKE_INKPATH = os.path.join(os.path.dirname(__file__), 'fakeinc')
LCB_ROOT = '/usr/local/'

def _exec_cpp():
    if not os.environ.get('PYCBC_GENHEADER'):
        return

    cpp_cmd = ('gcc', '-E', '-Wall', '-Wextra',
               '-I{0}'.format(FAKE_INKPATH),
               '-I{0}/include'.format(LCB_ROOT),
               '-std=c89',
               '-xc', '-')

    rx_shifty = re.compile(r'([^=]+)=.*(?:(?:<<)|(?:>>)|(?:\|))[^,]+')

    po = subprocess.Popen(cpp_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    stdout, _ = po.communicate(CPP_INPUT)
    try:
        lines = str(stdout, "utf8").split("\n")
    except TypeError:
        lines = stdout.split("\n")

    outlines = []
    for l in lines:
        if l.startswith('#'):
            continue
        if not l:
            continue
        # va_list stuff
        if '__gnuc' in l:
            l = '//' + l

        l = l.replace("\r", "")

        outlines.append(l)

    with open(CPP_OUTPUT, "w") as fp:
        fp.write("\n".join(outlines))
        fp.flush()


def get_handle():
    global C
    if C:
        return (ffi, C)

    _exec_cpp()
    ffi.cdef(open(CPP_OUTPUT, "r").read())
    C = ffi.verify(VERIFY_INPUT,
                   libraries=['couchbase'],
                   library_dirs=[os.path.join(LCB_ROOT, 'lib')],
                   include_dirs=[os.path.join(LCB_ROOT, 'include')],
                   runtime_library_dirs=[os.path.join(LCB_ROOT, 'lib')])

    return (ffi, C)


CALLBACK_DECLS = {
    'store':
        'void(lcb_t,const void*,lcb_storage_t,lcb_error_t,const lcb_store_resp_t*)',
    'get':
        'void(lcb_t,const void*,lcb_error_t,const lcb_get_resp_t*)',
    'delete':
        'void(lcb_t,const void*,lcb_error_t,const lcb_remove_resp_t*)',
    'arith':
        'void(lcb_t,const void*,lcb_error_t,const lcb_arithmetic_resp_t*)',
    'error':
        'void(lcb_t,lcb_error_t,const char*)',
    'touch':
        'void(lcb_t,const void*,lcb_error_t,const lcb_touch_resp_t*)',
    'unlock':
        'void(lcb_t,const void*,lcb_error_t,const lcb_unlock_resp_t*)',
    'observe':
        'void(lcb_t,const void*,lcb_error_t,const lcb_observe_resp_t*)',
    'stats':
        'void(lcb_t,const void*,lcb_error_t,const lcb_server_stat_resp_t*)',
    'http':
        'void(lcb_http_request_t,lcb_t,const void*,lcb_error_t,const lcb_http_resp_t*)',
    'endure':
        'void(lcb_t,const void*,lcb_error_t,const lcb_durability_resp_t*)'
}
