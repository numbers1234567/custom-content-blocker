import torch
import sys
sys.path.append("BLIP")
from models.blip import BLIP_Base,load_checkpoint
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
from torch import nn
from PIL import Image
import json

class PostClassifier:
    def __init__(self):
        pass

    def __call__(self, image, text) -> float:
        pass

class BLIPDeepHead3(nn.Module):
    def __init__(self, med_config="BLIP/configs/med_config.json", device="cpu"):
        super().__init__()
        with open(med_config, "r") as f:
            config = json.load(f)
        self.mlp = nn.Sequential(
            nn.Linear(config["hidden_size"], config["hidden_size"]//4),
            nn.ReLU(),
            nn.Linear(config["hidden_size"]//4, 2),
            nn.Sigmoid()
        ).to(device)

        self.device = device

    def forward(self, features):
        return self.mlp(features).cpu().detach().numpy()
    
    def load(self, path):
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint)

class BLIPClassifier(PostClassifier):
    def __init__(self, 
                 image_size=224, 
                 vit="base", 
                 med_config="BLIP/configs/med_config.json", 
                 pretrain_path="blip_base.pth", 
                 cls_head=BLIPDeepHead3, # A classifier which takes a numpy array of fixed size and returns a hit score
                 cls_head_path="model_checkpoints/blip_deep_mlp_3/blip_deep_mlp_3_e0",
                 device="cpu",
                 text_inject=True,
                 **kwargs):
        self.encoder = BLIP_Base(image_size=image_size,vit=vit,med_config=med_config, **kwargs)
        load_checkpoint(self.encoder, pretrain_path)
        self.encoder.eval()
        self.encoder = self.encoder.to(device)
        self.cls_head = BLIPDeepHead3(med_config=med_config,device=device)
        self.cls_head.load(cls_head_path)
        self.device = device
        self.text_inject = text_inject
        self.transform = transforms.Compose([
            transforms.Resize((image_size,image_size),interpolation=InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
        ]) 

    def encoder_forward(self, image, text, has_image):
        with torch.no_grad():
            batches = len(image)
            image = image.to(self.device)

            image_embeds = self.encoder.visual_encoder(image)  
            if self.text_inject:
                target_len = image_embeds.shape[1]
                fake = " ".join(["[PAD]"*(target_len-2)])
                text = tuple(list(text) + [fake])
                text = self.encoder.tokenizer(text, return_tensors="pt", padding="longest").to(self.device) 
                
                text_input_ids = text.input_ids[:batches]
                text_attention_mask = text.attention_mask[:batches]
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
        
    def preprocess(self, image : Image, text : str, has_image : bool):
        image = self.transform(image).unsqueeze(0).to(self.device)
        has_image = torch.tensor(has_image).unsqueeze(0).to(self.device)
        return image,(text,),has_image

    def __call__(self, image, text, has_image):
        image,text,has_image = self.preprocess(image,text,has_image)
        hidden_state = self.encoder_forward(image, text, has_image)
        return self.cls_head(hidden_state)[0][1]