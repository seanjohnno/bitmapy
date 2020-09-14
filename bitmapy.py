from typing import Tuple, Iterator, BinaryIO

HEADER_LENGTH = 14
LITTLE_ENDIAN = 'little'
INT_SIZE = 4
SHORT_SIZE = 2
BITS_PER_BYTE = 8

KEY_WIDTH = 'width'
KEY_HEIGHT = 'height'
KEY_COLOR_PLANE_COUNT = 'color_plane_count'
KEY_BITS_PER_PIXEL = 'bits_per_pixel'
KEY_COMPRESSION_METHOD = 'compression_method'
KEY_RAW_IMG_SIZE = 'raw_img_size'
KEY_HORIZONTAL_RESOLUTION = 'horizontal_resolution'
KEY_VERTICAL_RESOLUTION = 'vertical_resolution'
KEY_COLOR_PALETTE_COUNT = 'color_palette_count'
KEY_IMPORTANT_COLOR_COUNT = 'important_color_count'

LOC_BMP_SIZE = 2
LOC_BMP_START_OFFSET = 10

HEADER_MAP = {
    40: {
        'name': 'BITMAPINFOHEADER',
        KEY_WIDTH: (0, INT_SIZE),
        KEY_HEIGHT: (4, INT_SIZE),
        KEY_COLOR_PLANE_COUNT: (8, SHORT_SIZE),
        KEY_BITS_PER_PIXEL: (10, SHORT_SIZE),
        KEY_COMPRESSION_METHOD: (12, INT_SIZE),
        KEY_RAW_IMG_SIZE: (16, INT_SIZE),
        KEY_HORIZONTAL_RESOLUTION: (20, INT_SIZE),
        KEY_VERTICAL_RESOLUTION: (24, INT_SIZE),
        KEY_COLOR_PALETTE_COUNT: (28, INT_SIZE),
        KEY_IMPORTANT_COLOR_COUNT: (32, INT_SIZE)
    }
}

class BitmapHeaderInfo:
    def __init__(self, file: BinaryIO):
        self.__header = file.read(HEADER_LENGTH)
        self.__bmpSize = self.__get_val_from_header(LOC_BMP_SIZE)
        self.__bmpStartOffset = self.__get_val_from_header(LOC_BMP_START_OFFSET)

        self.__dib_header_len_bytes = file.read(INT_SIZE)
        dib_header_len = int.from_bytes(self.__dib_header_len_bytes, LITTLE_ENDIAN)
        self.__dib_header_type = dib_header_len
        self.__dib_header = file.read(dib_header_len - INT_SIZE)
        
        self.__bits_per_pixel = self.__get_val_from_dib_header(KEY_BITS_PER_PIXEL)

        header_before_image_data = self.__bmpStartOffset - (HEADER_LENGTH + dib_header_len)
        self.__other_headers = b'' if header_before_image_data == 0 else file.read(header_before_image_data)

    def width(self) -> int:
        return self.__get_val_from_dib_header(KEY_WIDTH)

    def height(self) -> int:
        return self.__get_val_from_dib_header(KEY_HEIGHT)

    def bits_per_pixel(self) -> int:
        return self.__bits_per_pixel

    def bytes_per_pixel(self) -> int:
        return int(self.bits_per_pixel() / BITS_PER_BYTE)

    def raw_image_size(self) -> int:
        return int(self.__get_val_from_dib_header(KEY_RAW_IMG_SIZE))

    def write_header(self, f: BinaryIO):
        f.write(self.__header)
        f.write(self.__dib_header_len_bytes)
        f.write(self.__dib_header)
        f.write(self.__other_headers)

    def __get_val_from_header(self, offset: int):
        start_ptr = offset
        end_ptr = start_ptr + INT_SIZE
        val_bytes = self.__header[start_ptr:end_ptr]
        return int.from_bytes(val_bytes, LITTLE_ENDIAN)

    def __get_val_from_dib_header(self, key: str):
        start_index, byte_count = HEADER_MAP[self.__dib_header_type][key]
        end_index = start_index + byte_count
        return int.from_bytes(self.__dib_header[start_index:end_index], LITTLE_ENDIAN)

    def __str__(self) -> str:
        return f'Size in bytes: {self.__bmpSize}, width: {self.width()}, height: {self.height()}, bits per pixel: {self.bits_per_pixel()}'

class Pixel:
    def __init__(self, bmp, x, y, pixel_data):
        self.__bmp = bmp
        self.__x = x
        self.__y = y
        self.__pixel_data = pixel_data
    
    def position(self) -> Tuple[int]:
        return (self.__x, self.__y)
    
    def pixel_data(self) -> Tuple[int]:
        return self.__pixel_data

    def update_pixel_data(self, pixel_tuple: Tuple[int]):
        self.__bmp.set_pixel(self.__x, self.__y, pixel_tuple)

    def __str__(self) -> str:
        return f'x[{self.__x}] y[{self.__y}]: {self.__pixel_data}'

class Bitmap:
    def __init__(self, filename: str):
        with open(filename, 'rb') as img:
            self.__bitmap_info = BitmapHeaderInfo(img)
            self.__bytes = bytearray(img.read())

    def info(self) -> BitmapHeaderInfo:
        return self.__bitmap_info

    def width(self) -> int:
        return self.__bitmap_info.width()

    def height(self) -> int:
        return int((len(self.__bytes) / self.info().bytes_per_pixel()) / self.width())

    def get_pixel(self, x: int, y: int) -> Pixel:
        bytes_per_pixel = self.__bitmap_info.bytes_per_pixel()
        start_ptr = (x + (y * self.__bitmap_info.width())) * bytes_per_pixel
        end_ptr = start_ptr + bytes_per_pixel
        pixel_data = tuple(self.__bytes[start_ptr:end_ptr])
        return Pixel(self, x, y, pixel_data)
    
    def set_pixel(self, x: int, y: int, pixel: Pixel):
        bytes_per_pixel = self.__bitmap_info.bytes_per_pixel()
        if len(pixel) != bytes_per_pixel:
            raise IndexError(f'Your pixel tuple should have {bytes_per_pixel} values')
        
        start_ptr = (x + (y * self.__bitmap_info.width())) * bytes_per_pixel
        for i in range(bytes_per_pixel):
            self.__bytes[start_ptr+i] = pixel[i]

    def save_as(self, filename: str):
        with open(filename, 'wb') as write_file:
            self.__bitmap_info.write_header(write_file)
            write_file.write(self.__bytes)
        
    def enumerate_pixels(self) -> Iterator[Pixel]:
        bytes_per_pixel = self.__bitmap_info.bytes_per_pixel()
        pixel_count = int(len(self.__bytes) / bytes_per_pixel)
        bmp_width = self.__bitmap_info.width()

        pixel_ptrs = ((x % bmp_width, int(x / bmp_width)) for x in range(pixel_count))
        for ptr in pixel_ptrs:
            yield self.get_pixel(ptr[0], ptr[1])

    def __str__(self) -> str:
        return f'{self.__bitmap_info}'