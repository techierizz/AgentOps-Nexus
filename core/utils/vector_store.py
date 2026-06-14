import math
import re
import json
import os
from collections import Counter
from typing import List, Dict, Any, Tuple

STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
    "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn',
    "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn',
    "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words."""
    words = re.findall(r'\b\w+\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]

class LocalVectorStore:
    def __init__(self, db_path: str = "memory_store.json"):
        self.db_path = db_path
        self.items: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.items = json.load(f)
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.items = []
        else:
            self.items = []

    def save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2)
        except Exception as e:
            print(f"Error saving vector store: {e}")

    def add_item(self, id: str, content: str, metadata: Dict[str, Any]):
        """Adds an item to the memory store."""
        # Check if item with this ID already exists, if so, replace it
        self.items = [item for item in self.items if item["id"] != id]
        
        self.items.append({
            "id": id,
            "content": content,
            "metadata": metadata
        })
        self.save()

    def search(self, query: str, top_k: int = 3) -> List[Tuple[float, Dict[str, Any]]]:
        """Performs a TF-IDF cosine similarity search over stored documents."""
        if not self.items:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Create corpus vocabulary and calculate document frequencies
        documents = [tokenize(item["content"]) for item in self.items]
        doc_count = len(documents)
        
        # Calculate DF (Document Frequency) for all words in query + docs
        all_vocab = set(query_tokens)
        for doc in documents:
            all_vocab.update(doc)
            
        df = Counter()
        for doc in documents:
            unique_words = set(doc)
            for word in unique_words:
                df[word] += 1
                
        # Calculate IDF (Inverse Document Frequency)
        idf = {}
        for word in all_vocab:
            # Add-one smoothing to avoid division by zero
            word_df = df[word]
            idf[word] = math.log((doc_count + 1) / (word_df + 1)) + 1.0

        # Vectorize query
        query_counter = Counter(query_tokens)
        query_vector = {}
        for word, count in query_counter.items():
            query_vector[word] = count * idf.get(word, 1.0)
            
        query_norm = math.sqrt(sum(val ** 2 for val in query_vector.values()))
        if query_norm == 0:
            return []

        results = []
        for index, item in enumerate(self.items):
            doc_tokens = documents[index]
            doc_counter = Counter(doc_tokens)
            
            # Vectorize document
            doc_vector = {}
            for word, count in doc_counter.items():
                if word in query_vector: # only intersection matters for dot product
                    doc_vector[word] = count * idf[word]
                    
            # Full norm of document (including non-matching words)
            full_doc_vector = {word: count * idf[word] for word, count in doc_counter.items()}
            doc_norm = math.sqrt(sum(val ** 2 for val in full_doc_vector.values()))
            
            if doc_norm == 0:
                similarity = 0.0
            else:
                dot_product = sum(query_vector[w] * doc_vector.get(w, 0.0) for w in query_vector if w in doc_vector)
                similarity = dot_product / (query_norm * doc_norm)
                
            results.append((similarity, item))

        # Sort by similarity score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

if __name__ == "__main__":
    # Test script
    store = LocalVectorStore("test_db.json")
    store.add_item("1", "ZeroDivisionError inside payment calculator discount calculation", {"fix": "check total count"})
    store.add_item("2", "NullPointerException when connecting to Stripe payment gateway", {"fix": "null check stripe client"})
    
    matches = store.search("division error in discount calculator")
    for score, item in matches:
        print(f"[{score:.2f}] {item['id']}: {item['content']}")
    
    # clean up test file
    if os.path.exists("test_db.json"):
        os.remove("test_db.json")
