from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
import os

model_name = "facebook/mbart-large-50-many-to-many-mmt"
save_path = r"models/mbart_model"

os.makedirs(save_path, exist_ok=True)

print("Downloading MBart model... This may take time.")

model = MBartForConditionalGeneration.from_pretrained(model_name)
tokenizer = MBart50TokenizerFast.from_pretrained(model_name)

model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)

print("MBart model downloaded successfully!")
