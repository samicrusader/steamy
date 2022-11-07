from io import BytesIO

ip = '10.0.2.174'
search_list = {
    '30820120300d06092a864886f70d01010105000382010d00308201080282010100d1543176ee6741270dc1a32f4b04c3a304d499ad0570777d'
    'ba31483d01eb5e639a05eb284f93cf9260b1ef9e159403ae5f7d3997e789646cfc70f26815169a9b4ba4dc5700ea4480f78466eae6d2bdf5e4'
    '181da076ca2e95b32b79c016eb91b5f158e8448d2dd5a42f883976a935dcccbbc611dc2bdf0ea3b88ca72fba919501fb8c6187b4ecddbbb662'
    '3d640e819302a6be35be74460cbad9bff0ab7dff0c5b4b8f4aff8252815989ec5fffb460166c5a75b81dd99d79b05f23d97476eb3a5d44c74d'
    'cd1136e776f5d2bb52e77f530fa2a5ad75f16c1fb5d8218d71b93073bddad930b3b4217989aa58b30566f1887907ca431e02defe51d1948948'
    '6caf033d020111': '30820120300d06092a864886f70d01010105000382010d0030820108028201010086724794f8a0fcb0c129b979e7af2e'
                      '1e309303a7042503d835708873b1df8a9e307c228b9c0862f8f5dbe6f81579233db8a4fe6ba14551679ad72c01973b5e'
                      'e4ecf8ca2c21524b125bb06cfa0047e2d202c2a70b7f71ad7d1c3665e557a7387bbc43fe52244e58d91a14c660a84b6a'
                      'e6fdc857b3f595376a8e484cb6b90cc992f5c57cccb1a1197ee90814186b046968f872b84297dad46ed4119ae0f40280'
                      '3108ad95777615c827de8372487a22902cb288bcbad7bc4a842e03a33bd26e052386cbc088c3932bdd1ec4fee1f734fe'
                      '5eeec55d51c91e1d9e5eae46cf7aac15b2654af8e6c9443b41e92568cce79c08ab6fa61601e4eed791f0436fdc296bb3'
                      '73020111', # Main RSA key
    'gds1.steampowered.com:27030 gds2.steampowered.com:27030': f'{ip}:27030 {ip}:27030', # Content List Servers (?)
    '72.165.61.189:27030 72.165.61.190:27030 69.28.151.178:27038 69.28.153.82:27038 87.248.196.194:27038 '
    '68.142.72.250:27038': f'{ip}:27030 {ip}:27030 {ip}:27038 {ip}:27038 {ip}:27038 {ip}:27038',  # Content List Servers
                                                                                                  # and AuthServer
}


def replace(binary: bytes, replace_list: dict=search_list):
    f = BytesIO(binary)  # This is a really cheap hack but effective.
    for search, replace in replace_list.items():
        if len(replace) > len(search):
            raise ValueError('Replacement data is bigger than search')
        loc = binary.find(search.encode())
        if loc != -1:
            f.seek(loc)
            f.write(replace.encode()+b'\x00')
    f.seek(0)
    return f.read()
