# Protocol Design
1. Start
2. Handshake: Sender -> Hello!
3. Handshake: Receiver -> Ready!
4. Metadata & Session Key: Sender creates session key, encrypts it with RSA Receiver Public Key. Signs metadata with Sender Private Key.
5. Receiver validates metadata timestamp and signature, decrypts session key.
6. Sender splits file into 3 parts.
7. Each part encrypted with Triple DES.
8. Hash of part calculated with SHA-512.
9. Part Hash signed with RSA Sender Private Key along with Sequence Number and Timestamp.
10. Receiver validates Packet Timestamp, Sequence Number, Hash, and Signature.
11. Decrypt part.
12. Assemble parts and save file.
13. Send ACK/NACK.
