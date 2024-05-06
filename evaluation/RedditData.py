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
    def __init__(self, root_dir, main_csv="main.csv", media_csv="media.csv", split="train", im_transform=transforms.Compose([]), **kwargs):
        super().__init__(**kwargs)
        self.main_csv  = os.path.join(root_dir, main_csv)
        self.media_csv = os.path.join(root_dir, media_csv)
        self.root_dir  = root_dir
        self.split = "train"

        self.main_df   = pd.read_csv(self.main_csv, delimiter="\t")
        self.main_df   = self.main_df[self.main_df["split"]==split]
        self.media_df  = pd.read_csv(self.media_csv, delimiter="\t")

        self.transform = im_transform

    def __len__(self): return len(self.main_df)
    def __getitem__(self, index):
        # A little inefficient, but data is going to be small.
        main_row = self.main_df.loc[self.main_df["ID"]==index]
        text = main_row["text"].iloc[0]
        label = main_row["label"].iloc[0]

        image_paths = self.media_df.loc[self.media_df["ID"]==index]["path"]
        image_paths = [os.path.join(self.root_dir, path) for path in image_paths]
        print(image_paths)
        images = [Image.open(path).convert('RGB') for path in image_paths]
        images = [im for im in images if im is not None]

        image = Image.new('RGB', (1000, 1000))
        if len(images) > 0:
            image = random.choice(images)
        image = self.transform(image)

        return text,image,label
    
class RedditDataSampler(Sampler):
    def __init__(self, root_dir, main_csv="main.csv", split="train"):
        super().__init__()
        main_csv  = os.path.join(root_dir, main_csv)
        main_df = pd.read_csv(main_csv, delimiter="\t")
        self.indices = list(main_df[main_df["split"]==split]["ID"])
        random.shuffle(self.indices)
        self.cur_index = 0

    def __iter__(self):
        while True:
            if self.cur_index==len(self.indices): # Seen all data
                random.shuffle(self.indices)
                self.cur_index = 0
            ret = self.indices[self.cur_index]
            self.cur_index += 1
            yield ret

    def __len__(self):
        return len(self.indices)