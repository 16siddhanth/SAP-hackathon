import torch
import soundfile as sf
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor

model_name = "DeepFake-Audio-Rangers/DeepfakeDetect_wav2vec2"
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)

audio_input, sample_rate = sf.read("/home/nerdnhk/Downloads/2rogan.wav")
inputs = processor(audio_input, sampling_rate=sample_rate, return_tensors="pt", padding=True)

with torch.no_grad():
    logits = model(**inputs).logits

# Get prediction
predicted_class_id = torch.argmax(logits, dim=-1).item()
labels = model.config.id2label
prediction = labels[predicted_class_id]

print(f"Prediction: {prediction}")
