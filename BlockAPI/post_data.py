from dataclasses import dataclass,field
import struct
import pickle

@dataclass
class Media:
    data_format : str # 12 bytes
    content     : bytes

def encode_media(media : Media) -> bytes:
    return bytearray(struct.pack("12s<i%ds"%(media.csize), media.data_format, media.csize, media.content))

def decode_media(buffer : bytearray, offset : int) -> Media:
    data_format,csize = struct.unpack_from("12s<i", buffer, offset=offset)
    content, = struct.unpack_from("%ds"%(csize), buffer, offset=offset+12+4)
    return (Media(data_format,csize,content), csize+12+4)

@dataclass
class MediaData:
    text    : str
    images  : list[Media] = field(default_factory=list)
    video   : list[Media] = field(default_factory=list)

def encode_media_data(media_data : MediaData):
    ret = bytearray(struct.pack("<i%ds<i<i" % media_data.nchar, media_data.nchar, media_data.nimages, media_data.nvideo))
    for image in media_data.images:
        ret += encode_media(image)
    for video in media_data.video:
        ret += encode_media(video)

    return ret

def decode_media_data(buffer : bytearray, offset : int):
    nchar = struct.unpack_from("<i", buffer, offset=offset)
    text = struct.unpack_from("%ds" % nchar, buffer, offset=offset+4)
    nimages,nvideo = struct.unpack_from("<i<i", buffer, offset=offset+4+nchar)
    cur_offset = offset+4+nchar+4+4
    images,videos = [],[]
    for i in range(len(nimages)):
        image,sz = decode_media(buffer, cur_offset)
        cur_offset += sz
        images.append(image)
    for i in range(len(nvideo)):
        video,sz = decode_media(buffer, cur_offset)
        cur_offset += sz
        videos.append(video)

    return (MediaData(nchar, text, nimages, nvideo, images, videos), cur_offset-offset)

@dataclass
class Metadata:
    ukey     : str
    uid      : str
    crt_time : int # time this was created

@dataclass
class PostData:
    media    : MediaData
    metadata : Metadata

def serialize_post_data(post_data : PostData) -> bytes:
    return pickle.dumps(post_data)

def deserialize_post_data(buffer : bytes) -> PostData:
    return pickle.loads(buffer)