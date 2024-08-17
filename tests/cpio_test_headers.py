newc_test_headers = [{'magic': b'070701',        # Newc
                      'ino': b'00000001',        # 1
                      'mode': b'000081ED',       # 33261
                      'uid': b'000003E8',        # 1000
                      'gid': b'000003E8',        # 1000
                      'nlink': b'00000001',      # 1
                      'mtime': b'00000001',      # 1
                      'filesize': b'000000FF',   # 255
                      'devmajor': b'00000000',   # 0
                      'devminor': b'00000023',   # 35
                      'rdevmajor': b'00000000',  # 0
                      'rdevminor': b'00000000',  # 0
                      'namesize': b'00000002',   # 2, simulaes '.' and '\0'
                      'check': b'00000000'}      # 0
                     ]


def build_newc_header(header_data):
    from pycpio.header import HEADER_NEW
    header = b''
    for attr in HEADER_NEW:
        header += header_data[attr]
    return header

