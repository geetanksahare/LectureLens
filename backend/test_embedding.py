from api.services.embedding_service import embed_text, embed_texts

vec = embed_text("Photosynthesis converts sunlight into chemical energy.")
print(f"Single embedding length: {len(vec)}")
print(f"First 5 values: {vec[:5]}")

vecs = embed_texts(["The mitochondria is the powerhouse of the cell.", "Water boils at 100 degrees Celsius."])
print(f"Batch embeddings count: {len(vecs)}")
print(f"Each embedding length: {len(vecs[0])}")