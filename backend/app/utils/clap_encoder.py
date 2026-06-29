import torch
import numpy as np
import librosa
import torch.nn.functional as F
from transformers import ClapModel, ClapProcessor

class ClapEncoder:
    """
    True CLAP encoder using laion/clap-htsat-fused.
    Produces aligned text and audio vectors:
      - 512-dim joint embedding space
      - Dynamic Zero-Shot Valence, Arousal, Dominance (VAD) estimates appended
    Total = 515 dims (aligned across text and audio)
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🚀 Initializing CLAP Encoder on engine: {self.device}")
        
        self.model = ClapModel.from_pretrained("laion/clap-htsat-fused").to(self.device)
        self.processor = ClapProcessor.from_pretrained("laion/clap-htsat-fused")
        
        self.sample_rate = 48000
        self.model.eval()

        # Define semantic anchor phrases to extract dynamic VAD metrics
        self.vad_anchors = {
            "valence": ["happy, joyful, cheerful, positive music", "sad, depressing, gloomy, negative music"],
            "arousal": ["energetic, intense, fast, exciting music", "calm, serene, sleepy, quiet music"],
            "dominance": ["powerful, aggressive, strong, confident music", "weak, submissive, gentle, vulnerable music"]
        }
        self._precompute_vad_anchors()

    def _precompute_vad_anchors(self):
        """Pre-encodes VAD anchor descriptions into the joint space for fast comparison."""
        self.anchor_embeddings = {}
        with torch.no_grad():
            for dimension, phrases in self.vad_anchors.items():
                inputs = self.processor(text=phrases, return_tensors="pt", padding=True).to(self.device)
                # Extract and normalize text embeddings for the anchors
                embeds = self.model.get_text_features(**inputs)
                embeds = F.normalize(embeds, p=2, dim=-1)
                self.anchor_embeddings[dimension] = embeds

    def _calculate_vad_score(self, normalized_vector: torch.Tensor) -> list:
        """
        Calculates continuous VAD metrics (0.0 to 1.0) based on cosine similarity
        relative to the positive and negative semantic anchor vectors.
        """
        vad_scores = []
        # Ensure input vector is a normalized 2D tensor row
        if len(normalized_vector.shape) == 1:
            normalized_vector = normalized_vector.unsqueeze(0)

        for dimension in ["valence", "arousal", "dominance"]:
            anchors = self.anchor_embeddings[dimension] # [2, 512]
            
            # Compute cosine similarity between our embedding and both anchors
            similarity = torch.matmul(normalized_vector, anchors.T) * 100.0 # Scaling factor
            probabilities = F.softmax(similarity, dim=-1).cpu().numpy()[0]
            
            # The score represents probability bias toward the positive anchor
            vad_scores.append(probabilities[0]) 
            
        return vad_scores

    def encode_text(self, text: str):
        """Return a 515-dim embedding (512 base + calculated VAD values)."""
        inputs = self.processor(
            text=text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.get_text_features(**inputs)
            # Standardize length to safely compute similarity coordinates
            norm_outputs = F.normalize(outputs, p=2, dim=-1)

        base_vec = outputs.cpu().numpy()[0]
        vad_values = self._calculate_vad_score(norm_outputs)
        
        return np.concatenate([base_vec, vad_values]).astype(np.float32)

    def encode_audio(self, file_path: str):
        """Loads audio, passes it through the CLAP audio encoder, and appends dynamic VAD."""
        try:
            # 1. Load and resample raw snippet data to 48kHz mono
            # Note: passing [audio_data] inside a list ensures stable tokenization processing shapes
            audio_data, _ = librosa.load(file_path, sr=self.sample_rate, mono=True)
            
            # 2. Extract features via CLAP processor
            inputs = self.processor(
                audios=[audio_data], 
                sampling_rate=self.sample_rate, 
                return_tensors="pt"
            ).to(self.device)
            
            # 3. Generate raw audio feature projections
            with torch.no_grad():
                outputs = self.model.get_audio_features(**inputs)
                norm_outputs = F.normalize(outputs, p=2, dim=-1)
                
            base_vec = outputs.cpu().numpy()[0]
            vad_values = self._calculate_vad_score(norm_outputs)
            
            return np.concatenate([base_vec, vad_values]).astype(np.float32)
            
        except Exception as e:
            print(f"❌ Error encoding audio file {file_path}: {e}")
            return None