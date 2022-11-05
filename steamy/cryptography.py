import hashlib
from Crypto.PublicKey import RSA

primary_key = RSA.construct((
    16972286244849771984622451367228102174501719320240653652662330551811042672286869215561928929175827402752178598753445713908601088303475414633015321035251571211566978795872136026380777563265395267739035345972002870926699475330208864762370786289338571780113370443705220053580642621034990905081765661421515793197322286229310533378663925641599451069026309189868652973825372527822995378307658254979118985781849587869182040447299629997994344818433422788110169038839718660945475305838947440389938769132300261658746306829589651102747347903636404092182462550116241824059779050479962155170547507469291673134785087525867735462771,
    998369779108810116742497139248711892617748195308273744274254738341826039546286424444819348775048670750128152867849747876976534606086789096059724766779504188915704635051302119198869268427376192219943255645411933583923498548835815574257105075843445398830198261394424709034155448296175935593045038907147987835121276143092265929765857522003315234046704493380086236406227181752690639773759910381564885451567942201551660793531581412046961847318500202889539128927129171613072773956837051742450320264942416013004138711897082646106738944678776002164289048233329862454552712571702039963458146099156364834927612038865038435329,
    17
))

network_key = RSA.construct((
    134539629474386922037791973580118887976202262513059806716070824872604019001549619717043869049820865778686338042804246699105615306763509624582695524159630542063424520740697096695065917367798513676047684857537002873465544160954589243833288573668688641279313120835560801603892833928651320394652562952389632548953,
    55398670960041673780267283238872483284318578681848155706617398476954596059461608118782769608749768261812021547037042758455253361608503963063462862889259625398654146184924437001549904434764958250148333879602146773194545846894891569844887509155520581612255537741780582148990843840620079165238381404172781505181,
    17
))


def sign_message_rsa(key, message: bytes):
    sha1 = hashlib.sha1()
    sha1.update(message)
    message_hash = sha1.digest()
    digest = b'\x00\x01' + (b'\xff' * int((key.public_key().size_in_bits()) / 8 - 38)) + \
             b'\x000!0\t\x06\x05+\x0e\x03\x02\x1a\x05\x00\x04\x14' + message_hash
    pt_int = int.from_bytes(digest, 'big')
    ct_int = pow(pt_int, key.public_key().e, key.public_key().n)
    signature = ct_int.to_bytes(key.public_key().size_in_bytes(), 'big')
    if len(signature) != 256:
        signature = signature.rjust(int((key.public_key().size_in_bits()) / 8), b'\x00')
    return signature
