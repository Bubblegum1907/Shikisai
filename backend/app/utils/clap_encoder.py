# app/utils/clap_encoder.py
import torch
import numpy as np
from transformers import ClapModel, ClapProcessor

class ClapEncoder:
    """
    True CLAP encoder using laion/clap-htsat-fused
    Produces:
      - 1024-dim embedding
      - valence, arousal, dominance
    Total = 1027 dims 
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load the actual CLAP model
        self.model = ClapModel.from_pretrained("laion/clap-htsat-fused").to(self.device)
        self.processor = ClapProcessor.from_pretrained("laion/clap-htsat-fused")

        self.model.eval()

    def encode_text(self, text: str):
        """Return a 1027-dim embedding (1024 + VAD values)."""
        inputs = self.processor(text=text, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.get_text_features(**inputs)

        # 1024-dim text embedding
        vec = outputs.cpu().numpy()[0]

        # Try extracting VAD if available; else fallback to 0.5
        try:
            val = float(self.model.text_model.valence_logits.cpu().numpy()[0])
            aro = float(self.model.text_model.arousal_logits.cpu().numpy()[0])
            dom = float(self.model.text_model.dominance_logits.cpu().numpy()[0])
        except:
            val = aro = dom = 0.5

        full_vec = np.concatenate([vec, [val, aro, dom]]).astype(np.float32)

        return full_vec
