"""Preserve exact coefficients while making source hashing CRLF/LF portable."""
import hashlib
import json
from c020_exact_certificate import DATA,SOURCE
from c021_exact_dual import verify


if __name__=='__main__':
    cert=json.loads((DATA/'c031_candidate.json').read_text());verify(cert)
    cert['source_hash_normalization']='lf'
    cert['source_sha256']=hashlib.sha256(SOURCE.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    verify(cert)
    with (DATA/'c031_exact_six_certificate.json').open('x',encoding='utf-8') as stream:
        json.dump(cert,stream)
