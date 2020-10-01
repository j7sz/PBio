from yacryptopan import CryptoPAn
cp = CryptoPAn(b'34-char-str-for-AES-key-and-pad.')
cp2 = CryptoPAn(b'34-char-str-for-AES-key-and-ped.')

ip = '192.168.1.1'
a = cp.anonymize(ip)
b = cp2.anonymize(ip)

print(a)
print(b)


a2 = cp.anonymize(b)
b2 = cp2.anonymize(a)

print(a2)
print(b2)