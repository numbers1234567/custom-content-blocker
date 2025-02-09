from torch import nn
from torch.nn import CrossEntropyLoss
import torch.nn.functional as F
import torch
import numpy as np
from BLIP.models.blip import BLIP_Base,load_checkpoint
import json
from sklearn.svm import SVC
import struct

class Classifier:
    def __init__(self):
        pass

    def train(self, image, text, label): 
        pass
    
    def __call__(self, image, text): # Returns hit score(s) depending on the format
        pass

    def save(self, path):
        pass

    def load(self, path):
        pass

class BLIPNLVRHead(nn.Module):
    def __init__(self, med_config="BLIP/configs/med_config.json", device="cpu", dropout=False):
        super().__init__()
        with open(med_config, "r") as f:
            config = json.load(f)
        seq = [
            nn.Linear(config["hidden_size"], config["hidden_size"]),
            nn.ReLU(),
            nn.Linear(config["hidden_size"], 2),
            nn.Sigmoid()
        ]
        if dropout:
            seq = [
                nn.Linear(config["hidden_size"], config["hidden_size"]),
                nn.ReLU(),
                nn.Dropout(p=0.2),
                nn.Linear(config["hidden_size"], 2),
                nn.Sigmoid()
            ]
        self.mlp = nn.Sequential(
            *seq
        ).to(device)
        self.loss = CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.mlp.parameters())

        self.device = device

    def train_head(self, features, label):
        label = label.to(self.device)
        yp = self.mlp(features)
        l = torch.mean(self.loss(yp, label))
        l.backward()
        self.optimizer.step()

    def forward(self, features):
        self.eval()
        res = self.mlp(features).cpu().detach().numpy()
        self.train()
        return res
    
    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path):
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint)

class BLIPDeepHead1(nn.Module):
    def __init__(self, med_config="BLIP/configs/med_config.json", device="cpu", dropout=False):
        super().__init__()
        with open(med_config, "r") as f:
            config = json.load(f)
        seq = [
            nn.Linear(config["hidden_size"], config["hidden_size"]//2),
            nn.ReLU(),
            nn.Linear(config["hidden_size"]//2, 2),
            nn.Sigmoid()
        ]
        if dropout:
            seq = [
                nn.Linear(config["hidden_size"], config["hidden_size"]//2),
                nn.ReLU(),
                nn.Dropout(p=0.2),
                nn.Linear(config["hidden_size"]//2, 2),
                nn.Sigmoid()
            ]
        self.mlp = nn.Sequential(
            *seq
        ).to(device)
        self.loss = CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.mlp.parameters())

        self.device = device
        self.dropout = dropout

    def train_head(self, features, label):
        label = label.to(self.device)
        yp = self.mlp(features)
        l = torch.mean(self.loss(yp, label))
        l.backward()
        self.optimizer.step()

    def forward(self, features):
        self.eval()
        res = self.mlp(features).cpu().detach().numpy()
        self.train()
        return res
    
    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path):
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint)

class BLIPDeepHead2(nn.Module):
    def __init__(self, med_config="BLIP/configs/med_config.json", device="cpu"):
        super().__init__()
        with open(med_config, "r") as f:
            config = json.load(f)
        self.mlp = nn.Sequential(
            nn.Linear(config["hidden_size"], 3*config["hidden_size"]//4),
            nn.ReLU(),
            nn.Linear(3*config["hidden_size"]//4, 2),
            nn.Sigmoid()
        ).to(device)
        self.loss = CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.mlp.parameters())

        self.device = device

    def train_head(self, features, label):
        label = label.to(self.device)
        yp = self.mlp(features)
        l = torch.mean(self.loss(yp, label))
        l.backward()
        self.optimizer.step()

    def forward(self, features):
        return self.mlp(features).cpu().detach().numpy()
    
    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path):
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint)

class BLIPDeepHead3(nn.Module):
    def __init__(self, med_config="BLIP/configs/med_config.json", device="cpu", dropout=False):
        super().__init__()
        with open(med_config, "r") as f:
            config = json.load(f)
        seq = [
            nn.Linear(config["hidden_size"], config["hidden_size"]//4),
            nn.ReLU(),
            nn.Linear(config["hidden_size"]//4, 2),
            nn.Sigmoid()
        ]
        if dropout:
            seq = [
                nn.Linear(config["hidden_size"], config["hidden_size"]//4),
                nn.ReLU(),
                nn.Dropout(p=0.2),
                nn.Linear(config["hidden_size"]//4, 2),
                nn.Sigmoid()
            ]
        self.mlp = nn.Sequential(
            *seq
        ).to(device)
        self.loss = CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.mlp.parameters())

        self.device = device

    def train_head(self, features, label):
        label = label.to(self.device)
        yp = self.mlp(features)
        l = torch.mean(self.loss(yp, label))
        l.backward()
        self.optimizer.step()

    def forward(self, features):
        return self.mlp(features).cpu().detach().numpy()
    
    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path):
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint)

class BLIPDeepHead4(nn.Module):
    def __init__(self, med_config="BLIP/configs/med_config.json", device="cpu", dropout=False):
        super().__init__()
        with open(med_config, "r") as f:
            config = json.load(f)
        seq = [
            nn.Linear(config["hidden_size"], 10),
            nn.ReLU(),
            nn.Linear(10, 2),
            nn.Sigmoid()
        ]
        if dropout:
            seq = [
                nn.Linear(config["hidden_size"], 10),
                nn.ReLU(),
                nn.Dropout(p=0.2),
                nn.Linear(10, 2),
                nn.Sigmoid()
            ]
        self.mlp = nn.Sequential(
            *seq
        ).to(device)
        self.loss = CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.mlp.parameters())

        self.device = device

    def train_head(self, features, label):
        label = label.to(self.device)
        yp = self.mlp(features)
        l = torch.mean(self.loss(yp, label))
        l.backward()
        self.optimizer.step()

    def forward(self, features):
        return self.mlp(features).cpu().detach().numpy()
    
    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path):
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint)

class BLIPDeepHead5(nn.Module):
    def __init__(self, med_config="BLIP/configs/med_config.json", device="cpu", dropout=False):
        super().__init__()
        with open(med_config, "r") as f:
            config = json.load(f)
        seq = [
            nn.Linear(config["hidden_size"], 2),
            nn.ReLU(),
            nn.Linear(2, 2),
            nn.Sigmoid()
        ]
        if dropout:
            seq = [
                nn.Linear(config["hidden_size"], 2),
                nn.ReLU(),
                nn.Dropout(p=0.2),
                nn.Linear(2, 2),
                nn.Sigmoid()
            ]
        self.mlp = nn.Sequential(
            *seq
        ).to(device)
        self.loss = CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.mlp.parameters())

        self.device = device

    def train_head(self, features, label):
        label = label.to(self.device)
        yp = self.mlp(features)
        l = torch.mean(self.loss(yp, label))
        l.backward()
        self.optimizer.step()

    def forward(self, features):
        return self.mlp(features).cpu().detach().numpy()
    
    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path):
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint)

# This is tricky to add to the current training framework. Make sure there aren't many back-to-back train_head and forward calls.
class BLIPSVMHead: 
    def __init__(self, **kwargs):
        self.x = []
        self.y = []
        self.fit = False
        self.svm = SVC(**kwargs)

    def train_head(self, features, label):
        label = label.cpu().detach().numpy()
        features = features.cpu().detach().numpy()
        for l,f in zip(label, features):
            l = np.argmax(label)
            self.x.append(f)
            self.y.append(l)
        self.fid=False

    def forward(self, features):
        if not self.fit:
            self.fit = True
            self.svm.fit(self.x,self.y)
        pred = self.svm.predict(features.cpu().detach().numpy())
        onehot_pred = np.zeros((len(features), 2))
        onehot_pred[:,1] = pred
        onehot_pred[:,0] = 1-pred
        return onehot_pred
    
    def save(self, path):
        with open(path, "wb") as f:
            svm_params = self.svm.get_params()
            nfeatures = len(self.x[0])
            nsamples = len(self.x)
            fit = self.fit
            f.write(struct.pack("?", fit))
            f.write(struct.pack("<i", nfeatures))
            f.write(struct.pack("<i", nsamples))
            for i in range(nsamples):
                for j in range(nfeatures):
                    f.write(struct.pack("<f", self.x[i][j]))
                f.write(struct.pack("<i", self.y[i]))

    def load(self, path):
        with open(path, "rb") as f:
            self.fit = struct.unpack("?", f.read(1))[0]
            nfeatures = struct.unpack("<i", f.read(4))[0]
            nsamples = struct.unpack("<i", f.read(4))[0]
            self.x,self.y = [],[]
            for i in range(nsamples):
                self.x.append([])
                for j in range(nfeatures):
                    self.x[i].append(struct.unpack("<f", f.read(4))[0])
                self.y.append(struct.unpack("<i", f.read(4))[0])
            if self.fit:
                self.svm.fit(self.x,self.y)

    def __call__(self, features): return self.forward(features)

class BLIPClassifier(Classifier):
    def __init__(self, 
                 cls_head, # A classifier which takes a numpy array of fixed size and returns a hit score
                 image_size=224, 
                 vit="base", 
                 med_config="BLIP/configs/med_config.json", 
                 pretrain_path="blip_base.pth", 
                 device="cpu",
                 text_inject=False,
                 **kwargs):
        self.encoder = BLIP_Base(image_size=image_size,vit=vit,med_config=med_config, **kwargs)
        load_checkpoint(self.encoder, pretrain_path)
        self.encoder.eval()
        self.encoder = self.encoder.to(device)
        self.cls_head = cls_head
        self.device = device
        self.text_inject = text_inject

    def encoder_forward(self, image, text, has_image):
        with torch.no_grad():
            batches = len(image)
            image = image.to(self.device)

            image_embeds = self.encoder.visual_encoder(image)  
            if self.text_inject:
                target_len = image_embeds.shape[1]
                fake = " ".join(["[PAD]"]*(target_len-2))
                text = tuple(list(text) + [fake])
                
                text = self.encoder.tokenizer(text, return_tensors="pt", padding="longest").to(self.device)

                text_input_ids = text.input_ids[:batches,:197]
                text_attention_mask = text.attention_mask[:batches,:197]
            else:
                text = self.encoder.tokenizer(text, return_tensors="pt", padding="longest").to(self.device) 
                
                text_input_ids = text.input_ids
                text_attention_mask = text.attention_mask

            # return multimodel features
            image_embeds = self.encoder.visual_encoder(image)  
            if self.text_inject:
                text_embeds = self.encoder.text_encoder(text_input_ids, attention_mask = text_attention_mask,                      
                                                return_dict = True, mode = 'text')
                for i in range(len(image)): # Blank image
                    if not has_image[i]:
                        image_embeds[i] = text_embeds.last_hidden_state[i]
            image_atts = torch.ones(image_embeds.size()[:-1],dtype=torch.long).to(self.device)      
            
            text.input_ids[:,0] = self.encoder.tokenizer.enc_token_id
            output = self.encoder.text_encoder(text_input_ids,
                                        attention_mask = text_attention_mask,
                                        encoder_hidden_states = image_embeds,
                                        encoder_attention_mask = image_atts,      
                                        return_dict = True,
                                        )              
            hidden_state = output.last_hidden_state
            hidden_state = hidden_state[:,0,:].detach()
            return hidden_state
        
    def train(self, image, text, label, has_image): # Condition: text should be under 150 tokens.
        label = label.to(self.device)
        hidden_state = self.encoder_forward(image, text, has_image)
        self.cls_head.train_head(hidden_state, label)

    def __call__(self, image, text, has_image):
        hidden_state = self.encoder_forward(image, text, has_image)
        return self.cls_head(hidden_state)
    
    def save(self, path):
        self.cls_head.save(path)

    def load(self, path):
        self.cls_head.load(path)