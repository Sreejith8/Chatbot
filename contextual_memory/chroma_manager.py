import os
import uuid
import datetime

class ContextualMemory:
    def __init__(self, persist_path):
        self.use_chroma = False
        self.collection = None
        self.memory_store = [] # Fallback list of dicts
        
        try:
            import chromadb
            # Try initializing client to see if it works
            self.client = chromadb.PersistentClient(path=persist_path)
            self.collection = self.client.get_or_create_collection(
                name="conversation_history",
                metadata={"hnsw:space": "cosine"}
            )
            self.use_chroma = True
            print("ContextualMemory: ChromaDB loaded successfully.")
        except Exception as e:
            print(f"ContextualMemory Warning: ChromaDB failed to load ({e}). Using in-memory fallback.")
            self.use_chroma = False

    def add_memory(self, user_id, text, metadata=None):
        """
        Add a conversation snippet to vector memory.
        """
        if metadata is None:
            metadata = {}
        
        metadata['user_id'] = str(user_id)
        metadata['timestamp'] = str(datetime.datetime.now().isoformat())
        # Add default importance if missing
        if 'importance' not in metadata:
            metadata['importance'] = 1.0

        
        if self.use_chroma:
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[str(uuid.uuid4())]
            )
        else:
            # Fallback
            self.memory_store.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": metadata
            })

    def SemanticSimilarity(self, distance):
        # ChromaDB often returns distance (e.g., L2 or cosine). Smaller distance = higher similarity.
        # Assuming normalized vectors and cosine distance, similarity is roughly 1 - distance.
        # (Chroma usually uses L2 on normalized, which is effectively cosine distance).
        return max(0.0, 1.0 - (distance / 2.0))

    def TemporalProximity(self, memory_timestamp_str):
        try:
            mem_time = datetime.datetime.fromisoformat(memory_timestamp_str)
            delta = datetime.datetime.now() - mem_time
            # Decay score based on hours elapsed
            hours = delta.total_seconds() / 3600.0
            # Higher weight for more recent memories
            return max(0.1, 1.0 / (1.0 + (hours * 0.1)))
        except (ValueError, TypeError):
            return 0.5 

    def retrieve_context(self, user_id, query_text, n_results=3):
        """
        Retrieve relevant past interactions matching the Contextual Memory Retrieval Algorithm.
        """
        if self.use_chroma:
            # We fetch more candidates than needed (e.g., top 10) to re-rank them
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(10, max(5, n_results * 2)), 
                where={"user_id": str(user_id)}
            )
            
            if not results['documents']:
                return []
                
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0] if 'distances' in results and results['distances'] else [0.0]*len(documents)
            
            scored_memories = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                # Calculate relevance score per Algorithm 3
                semantic_score = self.SemanticSimilarity(dist)
                temporal_score = self.TemporalProximity(meta.get('timestamp', ''))
                importance = float(meta.get('importance', 1.0))
                
                score = semantic_score
                score = score + temporal_score
                score = score * importance
                
                scored_memories.append({
                    "text": doc,
                    "metadata": meta,
                    "score": score
                })
            
            # Sort memories by relevance score (descending)
            scored_memories.sort(key=lambda x: x['score'], reverse=True)
            
            # Select top-k most relevant memories
            top_memories = scored_memories[:n_results]
            
            # Strip out the temporary score to match previous API format
            return [{"text": m["text"], "metadata": m["metadata"]} for m in top_memories]
        else:
            # Fallback: Simple keyword match or recent history
            # For simplicity, just return recent items for this user
            user_items = [item for item in self.memory_store if item['metadata']['user_id'] == str(user_id)]
            # Reverse to get most recent
            recent = user_items[-n_results:]
            return [{"text": i["text"], "metadata": i["metadata"]} for i in recent]

    def delete_user_memory(self, user_id):
        """
        Clear memory for a specific user.
        """
        if self.use_chroma:
            self.collection.delete(
                where={"user_id": str(user_id)}
            )
        else:
            self.memory_store = [item for item in self.memory_store if item['metadata']['user_id'] != str(user_id)]

# Singleton instance will be created in app init
