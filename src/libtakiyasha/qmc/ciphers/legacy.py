from __future__ import annotations

from typing import Generator

from .legacyconstants import key256mapping_all
from ...common import Cipher, KeylessCipher
from ...utils import bytesxor

__all__ = ['Key256Mask128', 'OldStaticMap']


class OldStaticMap(KeylessCipher):
    @staticmethod
    def cipher_name() -> str:
        return 'Slower Static Mapping'

    @staticmethod
    def masks() -> bytes:
        return bytes(
            [
                0x77, 0x48, 0x32, 0x73, 0xde, 0xf2, 0xc0, 0xc8,
                0x95, 0xec, 0x30, 0xb2, 0x51, 0xc3, 0xe1, 0xa0,
                0x9e, 0xe6, 0x9d, 0xcf, 0xfa, 0x7f, 0x14, 0xd1,
                0xce, 0xb8, 0xdc, 0xc3, 0x4a, 0x67, 0x93, 0xd6,
                0x28, 0xc2, 0x91, 0x70, 0xca, 0x8d, 0xa2, 0xa4,
                0xf0, 0x08, 0x61, 0x90, 0x7e, 0x6f, 0xa2, 0xe0,
                0xeb, 0xae, 0x3e, 0xb6, 0x67, 0xc7, 0x92, 0xf4,
                0x91, 0xb5, 0xf6, 0x6c, 0x5e, 0x84, 0x40, 0xf7,
                0xf3, 0x1b, 0x02, 0x7f, 0xd5, 0xab, 0x41, 0x89,
                0x28, 0xf4, 0x25, 0xcc, 0x52, 0x11, 0xad, 0x43,
                0x68, 0xa6, 0x41, 0x8b, 0x84, 0xb5, 0xff, 0x2c,
                0x92, 0x4a, 0x26, 0xd8, 0x47, 0x6a, 0x7c, 0x95,
                0x61, 0xcc, 0xe6, 0xcb, 0xbb, 0x3f, 0x47, 0x58,
                0x89, 0x75, 0xc3, 0x75, 0xa1, 0xd9, 0xaf, 0xcc,
                0x08, 0x73, 0x17, 0xdc, 0xaa, 0x9a, 0xa2, 0x16,
                0x41, 0xd8, 0xa2, 0x06, 0xc6, 0x8b, 0xfc, 0x66,
                0x34, 0x9f, 0xcf, 0x18, 0x23, 0xa0, 0x0a, 0x74,
                0xe7, 0x2b, 0x27, 0x70, 0x92, 0xe9, 0xaf, 0x37,
                0xe6, 0x8c, 0xa7, 0xbc, 0x62, 0x65, 0x9c, 0xc2,
                0x08, 0xc9, 0x88, 0xb3, 0xf3, 0x43, 0xac, 0x74,
                0x2c, 0x0f, 0xd4, 0xaf, 0xa1, 0xc3, 0x01, 0x64,
                0x95, 0x4e, 0x48, 0x9f, 0xf4, 0x35, 0x78, 0x95,
                0x7a, 0x39, 0xd6, 0x6a, 0xa0, 0x6d, 0x40, 0xe8,
                0x4f, 0xa8, 0xef, 0x11, 0x1d, 0xf3, 0x1b, 0x3f,
                0x3f, 0x07, 0xdd, 0x6f, 0x5b, 0x19, 0x30, 0x19,
                0xfb, 0xef, 0x0e, 0x37, 0xf0, 0x0e, 0xcd, 0x16,
                0x49, 0xfe, 0x53, 0x47, 0x13, 0x1a, 0xbd, 0xa4,
                0xf1, 0x40, 0x19, 0x60, 0x0e, 0xed, 0x68, 0x09,
                0x06, 0x5f, 0x4d, 0xcf, 0x3d, 0x1a, 0xfe, 0x20,
                0x77, 0xe4, 0xd9, 0xda, 0xf9, 0xa4, 0x2b, 0x76,
                0x1c, 0x71, 0xdb, 0x00, 0xbc, 0xfd, 0x0c, 0x6c,
                0xa5, 0x47, 0xf7, 0xf6, 0x00, 0x79, 0x4a, 0x11,
            ]
        )

    def gen_keystream(self, data_offset: int, data_len: int) -> Generator[int, None, None]:
        masks = self.masks()

        for i in range(data_offset, data_offset + data_len):
            if i > 0x7fff:
                i %= 0x7fff
            idx = (i ** 2 + 27) & 0xff
            yield masks[idx]

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        data_len = len(cipherdata)
        keystream = bytes(self.gen_keystream(start_offset, data_len))
        return bytesxor(cipherdata, keystream)


class Key256Mask128(Cipher):
    @staticmethod
    def cipher_name() -> str:
        return 'Dynamic Mapping (from Mask-128 or Mask-44)'

    def __init__(self, mask: bytes):
        if len(mask) == 44:
            # 从 44 位转换为 128 位
            key = self.mask44_to_mask128(mask)
        elif len(mask) == 128:
            key = mask[:]
        else:
            raise ValueError(f'invalid mask length (should be 44 or 128, got {len(mask)}')

        super().__init__(key)

    @staticmethod
    def mask44_to_mask128(mask44: bytes) -> bytes:
        if len(mask44) != 44:
            raise ValueError(f'invalid mask length (should be 44, got {len(mask44)})')

        mask128 = bytearray(128)
        idx44 = 0
        for it256 in key256mapping_all:
            if it256:
                for idx128 in it256:
                    mask128[idx128] = mask44[idx44]
                idx44 += 1

        return bytes(mask128)

    @classmethod
    def yield_mask(cls,
                   mask: bytes,
                   data_offset: int,
                   data_len: int
                   ) -> Generator[int, None, None]:
        index = data_offset - 1
        mask_idx = (data_offset % 128) - 1

        for _ in range(data_len):
            index += 1
            mask_idx += 1
            if index == 0x8000 or (index > 0x8000 and ((index + 1) % 0x8000 == 0)):
                index += 1
                mask_idx += 1
            if mask_idx >= 128:
                mask_idx -= 128

            yield mask[mask_idx]

    def gen_mask(self, data_offset: int, data_len: int) -> Generator[int, None, None]:
        yield from self.yield_mask(self._key, data_offset, data_len)

    def decrypt(self, cipherdata: bytes, start_offset: int = 0) -> bytes:
        keystream = bytes(self.gen_mask(start_offset, len(cipherdata)))
        return bytesxor(cipherdata, keystream)