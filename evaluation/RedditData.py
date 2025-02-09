from torch.utils.data import Dataset, DataLoader, Sampler, BatchSampler
import torch
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode

import cv2
from PIL import Image

import pandas as pd
import numpy as np

import random
import os

class RedditDataset(Dataset):
    def __init__(self, 
                 root_dir, 
                 main_csv="main.csv", media_csv="media.csv", split=None, 
                 text_col="text", label_col="label", id_col="ID",
                 media_path_col="path",split_col="split",
                 im_transform=transforms.Compose([transforms.ToTensor(), transforms.Resize((224,224),interpolation=InterpolationMode.BICUBIC)]), 
                 **kwargs):
        super().__init__(**kwargs)
        self.main_csv  = os.path.join(root_dir, main_csv)
        self.media_csv = os.path.join(root_dir, media_csv)
        self.root_dir  = root_dir

        self.text_col=text_col
        self.label_col=label_col
        self.id_col=id_col
        self.media_path_col=media_path_col

        self.main_df   = pd.read_csv(self.main_csv, delimiter="\t")
        self.main_df   = self.main_df[self.main_df[split_col]==split] if split != None else self.main_df
        self.media_df  = pd.read_csv(self.media_csv, delimiter="\t")

        self.transform = im_transform

    def __len__(self): return len(self.main_df)
    def __getitem__(self, index):
        # A little inefficient, but data is going to be small.
        main_row = self.main_df.loc[self.main_df["ID"]==index]
        text = main_row[self.text_col].iloc[0]
        label = main_row[self.label_col].iloc[0]

        image_paths = self.media_df.loc[self.media_df[self.id_col]==index][self.media_path_col]
        image_paths = [os.path.join(self.root_dir, path) for path in image_paths]
        
        images = [Image.open(path).convert('RGB') for path in image_paths]
        images = [im for im in images if im is not None]

        image = Image.new('RGB', (1000, 1000))
        has_image = False
        if len(images) > 0:
            image = random.choice(images)
            has_image = True
        image = self.transform(image)

        return text,image,label,has_image
    
class RedditDataSampler(Sampler):
    def __init__(self, root_dir, main_csv="main.csv", split=None, 
                 label_col="label", id_col="ID",split_col="split", 
                 upsampling=False):
        super().__init__()
        main_csv  = os.path.join(root_dir, main_csv)
        main_df = pd.read_csv(main_csv, delimiter="\t")

        split_df = main_df[main_df[split_col]==split] if split != None else main_df

        self.negindices = list(split_df[split_df[label_col]==0][id_col])
        self.posindices = list(split_df[split_df[label_col]==1][id_col])
        
        self.upsampling = upsampling
        
        self.set_order()

    def set_order(self):
        self.cur_index = 0
        self.indices = self.negindices + self.posindices
        if self.upsampling:
            if len(self.negindices) < len(self.posindices):
                self.indices += random.choices(self.negindices, k=len(self.posindices)-len(self.negindices))
            elif len(self.negindices) > len(self.posindices):
                self.indices += random.choices(self.posindices, k=len(self.negindices)-len(self.posindices))
        random.shuffle(self.indices)

    def __iter__(self):
        while True:
            if self.cur_index==len(self.indices): # Seen all data
                self.set_order()
                return
            ret = self.indices[self.cur_index]
            self.cur_index += 1
            yield ret

    def __len__(self):
        return len(self.indices)